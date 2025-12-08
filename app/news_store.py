import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
from dotenv import load_dotenv
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# Load environment variables from .env
load_dotenv()

# Base URL of the WordPress site (Conso News production by default)
WORDPRESS_BASE_URL = os.getenv("WORDPRESS_BASE_URL", "https://consonews.ma")

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # Optional, for Qdrant Cloud
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "conso_news_articles")

# Embedding configuration
# gemini-embedding-001: multilingual, supports 3072/1536/768 dims
# - Runtime queries: Gemini API (free tier, uses LLM_API_KEY)
# - Batch indexing: Vertex AI (uses GCP credits, for local use)
EMBEDDING_MODEL_GEMINI = "models/gemini-embedding-001"  # Gemini API model name
EMBEDDING_MODEL_VERTEX = "gemini-embedding-001"  # Vertex model name
EMBEDDING_DIMENSION = 768

# Gemini API key (for runtime query embeddings)
GOOGLE_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Vertex AI config (for batch indexing, local use)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0981273199")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "gen-lang-client-0981273199-da547dc931c3.json")
)

# When set, completely disable embeddings and Qdrant search/indexing
DISABLE_EMBEDDING = os.getenv("DISABLE_EMBEDDING", "").lower() in {"1", "true", "yes"}

# Initialize Vertex AI
_VERTEX_INITIALIZED = False
def _init_vertex_ai():
    global _VERTEX_INITIALIZED
    if _VERTEX_INITIALIZED:
        return
    # Set credentials env var if file exists
    if os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
    import vertexai
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    _VERTEX_INITIALIZED = True
    print(f"   🔧 Vertex AI initialized (project={GCP_PROJECT_ID}, location={GCP_LOCATION})")
_QDRANT_CLIENT: QdrantClient | None = None

# Cache and progress files
POSTS_CACHE_FILE = "posts_cache.json"
EMBEDDINGS_CACHE_FILE = "embeddings_cache.json"
PROGRESS_FILE = "indexing_progress.json"
BATCH_FILES_DIR = "posts_batches"


def embed_text(text: str) -> List[float]:
    """Embed a single text using Gemini API (for runtime queries)."""
    if DISABLE_EMBEDDING:
        raise RuntimeError("Embeddings are disabled (DISABLE_EMBEDDING env var is set)")
    if not GOOGLE_API_KEY:
        raise RuntimeError("No API key found (set LLM_API_KEY or GOOGLE_API_KEY)")
    
    result = genai.embed_content(
        model=EMBEDDING_MODEL_GEMINI,
        content=text,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=EMBEDDING_DIMENSION
    )
    return result['embedding']


def embed_texts_batch(texts: List[str], batch_size: int = 10) -> List[List[float]]:
    """
    Embed multiple texts using Vertex AI (for batch indexing, local use).
    We are limited to 5 online prediction requests per minute for this base model,
    so we throttle to ~4 requests/min (sleep ~15s between batches).
    """
    if not texts:
        return []
    if DISABLE_EMBEDDING:
        raise RuntimeError("Embeddings are disabled (DISABLE_EMBEDDING env var is set)")

    _init_vertex_ai()
    from vertexai.language_models import TextEmbeddingModel

    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_VERTEX)
    all_embeddings = []
    total = len(texts)

    # Target ~4 requests/min to stay under the 5 req/min quota
    sleep_between_batches = 15.0

    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"      📊 Batch {batch_num}/{total_batches} ({len(batch)} texts)")

        # Retry once on quota errors, then fall back to zeros for this batch
        for attempt in range(2):
            try:
                embeddings = model.get_embeddings(batch, output_dimensionality=EMBEDDING_DIMENSION)
                all_embeddings.extend([e.values for e in embeddings])
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                    # Quota hit: wait one full interval then retry once
                    if attempt == 0:
                        print(f"      ⏳ Quota hit, waiting {sleep_between_batches}s then retrying...")
                        time.sleep(sleep_between_batches)
                    else:
                        print("      ⚠️ Quota still exceeded, using zeros for this batch")
                else:
                    print(f"⚠️ Batch embedding failed: {e}")
                    all_embeddings.extend([[0.0] * EMBEDDING_DIMENSION] * len(batch))
                    break
        else:
            # All attempts failed due to quota
            all_embeddings.extend([[0.0] * EMBEDDING_DIMENSION] * len(batch))

        # Always sleep between batches to respect 5 req/min
        time.sleep(sleep_between_batches)

    return all_embeddings


# ============================================================
# EMBEDDING CACHE - Never re-embed already processed posts
# ============================================================

def load_embeddings_cache() -> Dict[int, List[float]]:
    """Load cached embeddings from disk. Key = post_id, Value = embedding vector."""
    if os.path.exists(EMBEDDINGS_CACHE_FILE):
        try:
            with open(EMBEDDINGS_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            # Convert string keys back to int
            return {int(k): v for k, v in cache.items()}
        except Exception as e:
            print(f"⚠️ Failed to load embeddings cache: {e}")
    return {}


def save_embeddings_cache(cache: Dict[int, List[float]]) -> None:
    """Save embeddings cache to disk."""
    try:
        with open(EMBEDDINGS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        print(f"💾 Saved {len(cache)} embeddings to cache")
    except Exception as e:
        print(f"⚠️ Failed to save embeddings cache: {e}")


def load_progress() -> Dict:
    """Load indexing progress from disk."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load progress: {e}")
    return {"completed_batches": [], "total_indexed": 0}


def save_progress(progress: Dict) -> None:
    """Save indexing progress to disk."""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save progress: {e}")


def get_qdrant_client() -> QdrantClient:
    """Return a shared Qdrant client."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        # Support both local (no API key) and Qdrant Cloud (with API key)
        if QDRANT_API_KEY:
            _QDRANT_CLIENT = QdrantClient(
                url=f"https://{QDRANT_HOST}:{QDRANT_PORT}",
                api_key=QDRANT_API_KEY,
            )
        else:
            _QDRANT_CLIENT = QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
            )
    return _QDRANT_CLIENT


def fetch_posts(limit: int = 50) -> List[Dict]:
    """Fetch the latest posts from the WordPress REST API."""
    url = f"{WORDPRESS_BASE_URL.rstrip('/')}/wp-json/wp/v2/posts"
    per_page = 100 if limit is None else min(limit, 100)

    all_posts: List[Dict] = []
    page = 1
    last_error: Exception | None = None

    print(f"   📡 Fetching from {url} (page size: {per_page})...")

    while True:
        if limit is not None and len(all_posts) >= limit:
            break

        params = {
            "per_page": per_page,
            "orderby": "date",
            "order": "desc",
            "page": page,
        }

        success = False
        for attempt in range(3):
            try:
                print(f"   📄 Fetching page {page}...", end=" ", flush=True)
                resp = requests.get(url, params=params, timeout=60)  # 60s timeout
                # If we requested a page beyond the available range, WordPress typically returns 400
                if resp.status_code == 400:
                    print("(no more pages)")
                    return all_posts
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    print("(empty, done)")
                    return all_posts
                all_posts.extend(batch)
                print(f"got {len(batch)} posts (total: {len(all_posts)})")
                success = True
                break
            except Exception as e:
                last_error = e
                print(f"FAILED (attempt {attempt + 1}/3): {e}")

        if not success:
            print(f"   ⚠️ Giving up on page {page} after 3 attempts")
            break

        page += 1

    if last_error is not None and not all_posts:
        raise last_error

    if limit is not None and len(all_posts) > limit:
        return all_posts[:limit]

    return all_posts


def fetch_recent_posts(hours: int = 24) -> List[Dict]:
    """Fetch posts published in the last N hours using WordPress 'after' parameter."""
    url = f"{WORDPRESS_BASE_URL.rstrip('/')}/wp-json/wp/v2/posts"
    
    # Calculate the cutoff time in ISO format
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    after_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
    
    all_posts: List[Dict] = []
    page = 1
    
    print(f"   📡 Fetching posts from last {hours} hours (after {after_iso})...")
    
    while True:
        params = {
            "per_page": 100,
            "orderby": "date",
            "order": "desc",
            "page": page,
            "after": after_iso,  # Only posts after this date
        }
        
        try:
            print(f"   📄 Fetching page {page}...", end=" ", flush=True)
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 400:
                print("(no more pages)")
                break
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                print("(empty, done)")
                break
            all_posts.extend(batch)
            print(f"got {len(batch)} posts (total: {len(all_posts)})")
            page += 1
        except Exception as e:
            print(f"FAILED: {e}")
            break
    
    return all_posts


def html_to_text(html: str) -> str:
    """Very simple HTML → text conversion.

    For now we strip tags naively; for a real project you may want
    BeautifulSoup or similar.
    """
    # Cheap fallback to keep things lightweight
    import re

    # Remove script/style tags
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.IGNORECASE)

    # Replace <br> and </p> with newlines
    html = re.sub(r"<br ?/?>", "\n", html, flags=re.IGNORECASE)
    html = html.replace("</p>", "\n")

    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", html)

    # Unescape HTML entities
    import html as html_lib

    text = html_lib.unescape(text)

    # Normalize whitespace
    text = " ".join(text.split())
    return text.strip()


def refresh_all_posts(fresh: bool = False) -> None:
    """
    Index all posts to Qdrant using Gemini embeddings with full resume support.
    
    - Loads from batch files (posts_batches/batch_*.json)
    - Tracks completed batches in indexing_progress.json
    - Caches embeddings to avoid re-embedding on resume
    - No chunking: 1 post = 1 Qdrant document
    
    Args:
        fresh: If True, delete collection and reset progress
    """
    from pathlib import Path
    
    qclient = get_qdrant_client()
    
    # Check batch files exist
    batch_dir = Path(BATCH_FILES_DIR)
    if not batch_dir.exists():
        print(f"❌ Batch files not found: {BATCH_FILES_DIR}/")
        print("   Run validate_posts.py first to create batch files.")
        return
    
    batch_files = sorted(batch_dir.glob("batch_*.json"))
    if not batch_files:
        print(f"❌ No batch files found in {BATCH_FILES_DIR}/")
        return
    
    print(f"📂 Found {len(batch_files)} batch files")
    
    # Load progress and embeddings cache
    if fresh:
        progress = {"completed_batches": [], "total_indexed": 0}
        embeddings_cache = {}
        # Delete progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        if os.path.exists(EMBEDDINGS_CACHE_FILE):
            os.remove(EMBEDDINGS_CACHE_FILE)
        print("🗑️ Cleared progress and embeddings cache")
    else:
        progress = load_progress()
        embeddings_cache = load_embeddings_cache()
        print(f"📂 Loaded progress: {len(progress['completed_batches'])} batches done")
        print(f"📂 Loaded {len(embeddings_cache)} cached embeddings")
    
    # Handle Qdrant collection
    if fresh:
        try:
            qclient.delete_collection(collection_name=QDRANT_COLLECTION)
            print(f"🗑️ Deleted existing collection '{QDRANT_COLLECTION}'")
        except Exception:
            pass
    
    if not qclient.collection_exists(collection_name=QDRANT_COLLECTION):
        qclient.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=qmodels.Distance.COSINE,
            ),
        )
        print(f"✅ Created collection '{QDRANT_COLLECTION}' (dim={EMBEDDING_DIMENSION})")
        
        # Create datetime index on 'date' field for date filtering
        qclient.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="date",
            field_schema=qmodels.PayloadSchemaType.DATETIME,
        )
        print("✅ Created datetime index on 'date' field")
    else:
        print(f"ℹ️ Collection '{QDRANT_COLLECTION}' exists, will upsert")
    
    # Process each batch file
    total_indexed = progress.get("total_indexed", 0)
    total_skipped = 0
    new_embeddings = 0
    completed = set(progress.get("completed_batches", []))
    
    for batch_file in batch_files:
        batch_name = batch_file.name
        batch_num = int(batch_name.replace("batch_", "").replace(".json", ""))
        
        # Skip completed batches
        if batch_name in completed:
            print(f"⏭️ Skipping {batch_name} (already done)")
            continue
        
        print(f"\n📦 Processing {batch_name} ({batch_num}/{len(batch_files)})")
        
        # Load batch
        try:
            with open(batch_file, "r", encoding="utf-8") as f:
                posts = json.load(f)
        except Exception as e:
            print(f"   ❌ Failed to load {batch_name}: {e}")
            continue
        
        # Prepare posts
        posts_to_embed = []
        posts_with_cache = []
        
        for post in posts:
            post_id = post.get("id")
            title = post.get("title", {}).get("rendered", "")
            content_html = post.get("content", {}).get("rendered", "")
            url = post.get("link", "")
            date = post.get("date", "")
            
            content_text = html_to_text(content_html)
            
            if not content_text or not content_text.strip():
                total_skipped += 1
                continue
            
            full_text = f"{title}\n\n{content_text}"
            
            if post_id in embeddings_cache:
                posts_with_cache.append((post_id, title, content_text, url, date, embeddings_cache[post_id]))
            else:
                posts_to_embed.append((post_id, title, content_text, url, date, full_text))
        
        # Embed new posts
        if posts_to_embed:
            texts_to_embed = [p[5] for p in posts_to_embed]
            print(f"   🔄 Embedding {len(texts_to_embed)} new posts...")
            
            try:
                embeddings = embed_texts_batch(texts_to_embed)
                
                for (post_id, title, content_text, url, date, _), vec in zip(posts_to_embed, embeddings):
                    embeddings_cache[post_id] = vec
                    posts_with_cache.append((post_id, title, content_text, url, date, vec))
                
                new_embeddings += len(embeddings)
            except Exception as e:
                print(f"   ❌ Embedding failed: {e}")
                save_embeddings_cache(embeddings_cache)
                save_progress(progress)
                raise
        else:
            print(f"   ✅ All {len(posts_with_cache)} posts already cached")
        
        # Build Qdrant points
        points = []
        for post_id, title, content_text, url, date, vec in posts_with_cache:
            points.append(
                qmodels.PointStruct(
                    id=post_id,
                    vector=vec,
                    payload={
                        "post_id": post_id,
                        "title": title,
                        "content": content_text,
                        "url": url,
                        "date": date,
                    },
                )
            )
        
        # Upsert to Qdrant
        if points:
            for attempt in range(3):
                try:
                    qclient.upsert(
                        collection_name=QDRANT_COLLECTION,
                        points=points,
                    )
                    total_indexed += len(points)
                    print(f"   ✅ Indexed {len(points)} posts")
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"   ⚠️ Upsert failed (attempt {attempt+1}/3): {e}")
                        time.sleep(2 ** attempt)
                    else:
                        print(f"   ❌ Upsert failed: {e}")
                        save_embeddings_cache(embeddings_cache)
                        save_progress(progress)
                        raise
        
        # Mark batch as complete
        progress["completed_batches"].append(batch_name)
        progress["total_indexed"] = total_indexed
        
        # Save progress after each batch
        save_progress(progress)
        save_embeddings_cache(embeddings_cache)
        print(f"   💾 Progress saved ({len(progress['completed_batches'])}/{len(batch_files)} batches)")
    
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE!")
    print(f"   Batches processed: {len(progress['completed_batches'])}/{len(batch_files)}")
    print(f"   Total indexed: {total_indexed} posts")
    print(f"   Skipped (empty): {total_skipped} posts")
    print(f"   New embeddings: {new_embeddings}")
    print(f"   Cached embeddings: {len(embeddings_cache)}")
    print(f"{'='*60}")


def index_new_posts(hours: int = 24) -> None:
    """
    Incremental indexing: fetch posts from the last N hours and add/update them in Qdrant.
    Does NOT recreate the collection - assumes it already exists from initial backfill.
    Uses post_id directly as Qdrant point ID (no chunking).
    """
    if DISABLE_EMBEDDING:
        print(f"⚠️ Embeddings disabled (DISABLE_EMBEDDING=1), skipping incremental indexing.")
        return

    print(f"⌘ Incremental index: checking for posts from last {hours} hours...")
    qclient = get_qdrant_client()
    
    # Check if collection exists
    try:
        qclient.get_collection(collection_name=QDRANT_COLLECTION)
    except Exception:
        print(f"⚠️ Collection '{QDRANT_COLLECTION}' doesn't exist. Run full backfill first!")
        return
    
    posts = fetch_recent_posts(hours=hours)
    
    if not posts:
        print("✅ No new posts found. Index is up to date.")
        return
    
    print(f"✅ Found {len(posts)} new posts to index")
    
    # Load embeddings cache
    embeddings_cache = load_embeddings_cache()
    
    try:
        # Prepare posts
        posts_data = []
        for post in posts:
            post_id = post.get("id")
            title = post.get("title", {}).get("rendered", "")
            content_html = post.get("content", {}).get("rendered", "")
            url = post.get("link", "")
            date = post.get("date", "")
            
            content_text = html_to_text(content_html)
            if not content_text:
                continue
            
            full_text = f"{title}\n\n{content_text}"
            posts_data.append((post_id, title, content_text, url, date, full_text))
        
        if not posts_data:
            print("⚠️ No content to index from new posts.")
            return
        
        # Embed posts (skip cached ones)
        posts_to_embed = [(p, t) for p, _, _, _, _, t in posts_data if p not in embeddings_cache]
        
        if posts_to_embed:
            texts = [t for _, t in posts_to_embed]
            print(f"   🔄 Embedding {len(texts)} new posts...")
            embeddings = embed_texts_batch(texts)
            
            for (post_id, _), vec in zip(posts_to_embed, embeddings):
                embeddings_cache[post_id] = vec
        
        # Build points
        points: List[qmodels.PointStruct] = []
        for post_id, title, content_text, url, date, _ in posts_data:
            vec = embeddings_cache.get(post_id)
            if not vec:
                continue
            
            payload = {
                "post_id": post_id,
                "title": title,
                "content": content_text,
                "url": url,
                "date": date,
            }
            points.append(
                qmodels.PointStruct(
                    id=post_id,
                    vector=vec,
                    payload=payload,
                )
            )
        
        # Upsert
        if points:
            qclient.upsert(
                collection_name=QDRANT_COLLECTION,
                points=points,
            )
            print(f"✅ Indexed {len(points)} posts")
            
            # Save cache
            save_embeddings_cache(embeddings_cache)
        
    except Exception as e:
        print(f"[index_new_posts] Error: {e}")
        save_embeddings_cache(embeddings_cache)


def repair_zero_embeddings(batch_size: int = 5) -> None:
    """Re-embed posts whose embeddings are all zeros.

    This scans the local embeddings cache, finds entries where every component
    is 0.0, fetches their payloads from Qdrant, re-embeds the corresponding
    text using Vertex AI, and upserts the fixed vectors back into Qdrant.
    """
    if DISABLE_EMBEDDING:
        print("⚠️ Embeddings disabled (DISABLE_EMBEDDING=1), cannot repair zeros.")
        return

    print("⌘ Repair zeros: scanning embeddings cache...")

    embeddings_cache = load_embeddings_cache()
    if not embeddings_cache:
        print("⚠️ No embeddings cache found.")
        return

    zero_ids = [pid for pid, vec in embeddings_cache.items() if vec and all(v == 0.0 for v in vec)]
    print(f"✅ Found {len(zero_ids)} posts with all-zero embeddings")

    if not zero_ids:
        return

    qclient = get_qdrant_client()

    fixed = 0
    for i in range(0, len(zero_ids), batch_size):
        chunk_ids = zero_ids[i:i + batch_size]
        print(f"\n🔎 Fetching payloads for {len(chunk_ids)} posts (chunk {i//batch_size+1}/{(len(zero_ids)+batch_size-1)//batch_size})")

        try:
            points = qclient.retrieve(collection_name=QDRANT_COLLECTION, ids=chunk_ids)
        except Exception as e:
            print(f"⚠️ Failed to retrieve points from Qdrant: {e}")
            continue

        if not points:
            print("⚠️ No points returned for these IDs, skipping chunk")
            continue

        texts: list[str] = []
        payloads: list[dict] = []
        ids_for_chunk: list[int] = []

        for p in points:
            pid = p.id
            payload = p.payload or {}
            title = payload.get("title", "")
            content = payload.get("content", "")
            url = payload.get("url", "")
            date = payload.get("date", "")

            if not content:
                continue

            full_text = f"{title}\n\n{content}"
            texts.append(full_text)
            payloads.append({
                "post_id": pid,
                "title": title,
                "content": content,
                "url": url,
                "date": date,
            })
            ids_for_chunk.append(pid)

        if not texts:
            print("⚠️ No usable text in this chunk, skipping")
            continue

        print(f"   🔄 Re-embedding {len(texts)} posts with zero vectors...")
        # Use smaller batches for safety; embed_texts_batch will still throttle
        embeddings = embed_texts_batch(texts, batch_size=batch_size)

        points_to_upsert: list[qmodels.PointStruct] = []
        for pid, payload, vec in zip(ids_for_chunk, payloads, embeddings):
            if not vec:
                continue
            embeddings_cache[int(pid)] = vec
            points_to_upsert.append(
                qmodels.PointStruct(id=pid, vector=vec, payload=payload)
            )

        if points_to_upsert:
            try:
                qclient.upsert(collection_name=QDRANT_COLLECTION, points=points_to_upsert)
                fixed += len(points_to_upsert)
                print(f"   ✅ Upserted {len(points_to_upsert)} repaired posts")
            except Exception as e:
                print(f"⚠️ Failed to upsert repaired points: {e}")

        # Persist cache after each chunk
        save_embeddings_cache(embeddings_cache)

    print(f"\n✅ Repair complete. Fixed embeddings for {fixed} posts.")


def search_news(query: str, top_k: int = 5, days_back: int = None) -> List[Dict]:
    """
    Search indexed news posts for a query using Qdrant.
    
    Args:
        query: Search query
        top_k: Number of results to return
        days_back: If specified, only return articles from the last N days
    """
    from datetime import datetime, timedelta

    print(f"[search_news] Called with query='{query}', top_k={top_k}, days_back={days_back}")

    # On environments where embeddings are disabled (e.g. Render free tier),
    # we cannot embed queries, so we just return no internal results.
    if DISABLE_EMBEDDING:
        print("[search_news] Embeddings disabled (DISABLE_EMBEDDING=1), returning no results.")
        return []

    print("[search_news] Getting Qdrant client...")
    qclient = get_qdrant_client()

    try:
        print("[search_news] Embedding query...")
        query_vec = embed_text(query)
        print(f"[search_news] Query embedded, vector dim={len(query_vec)}")
    except Exception as e:
        print(f"[search_news] Error embedding query: {e}")
        import traceback
        traceback.print_exc()
        return []

    # Build date filter if specified
    query_filter = None
    if days_back is not None:
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S")
        query_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="date",
                    range=qmodels.DatetimeRange(gte=cutoff_date)
                )
            ]
        )

    try:
        print(f"[search_news] Querying Qdrant collection '{QDRANT_COLLECTION}'...")
        response = qclient.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vec,
            query_filter=query_filter,
            limit=top_k,
        )
        results = response.points
        print(f"[search_news] Qdrant returned {len(results)} results")
    except Exception as e:
        print(f"[search_news] Error querying Qdrant: {e}")
        import traceback
        traceback.print_exc()
        return []

    scored: List[Dict] = []
    for r in results:
        payload = r.payload or {}
        scored.append(
            {
                "post_id": payload.get("post_id"),
                "title": payload.get("title", ""),
                "url": payload.get("url", ""),
                "date": payload.get("date", ""),
                "content": payload.get("content", ""),
                "score": r.score,
            }
        )

    return scored


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("📰 Conso News Indexer (Vertex AI gemini-embedding-001, 768 dims)")
    print("="*60)
    
    # Flags
    fresh_mode = "--fresh" in sys.argv
    repair_zeros_mode = "--repair-zeros" in sys.argv

    # Check for --search to just test search
    if "--search" in sys.argv:
        query = " ".join([a for a in sys.argv[1:] if not a.startswith("--")])
        if not query:
            query = "actualité maroc"
        print(f"\n🔎 Search: '{query}'\n")
        results = search_news(query, top_k=5)
        for i, r in enumerate(results, start=1):
            print(f"--- Result {i} (score={r['score']:.3f}) ---")
            print(f"Title: {r['title']}")
            print(f"URL:   {r['url']}")
            print(f"Date:  {r['date']}")
            print(f"Content: {r['content'][:200]}...")
            print()
    elif repair_zeros_mode:
        # Only repair zero embeddings
        print("Mode: REPAIR-ZEROS (re-embed posts with all-zero vectors)\n")
        repair_zero_embeddings()
    else:
        # Full indexing
        print(f"Mode: {'FRESH (delete & rebuild)' if fresh_mode else 'RESUME (use cached embeddings)'}")
        print()
        refresh_all_posts(fresh=fresh_mode)
        
        # Quick test search
        print("\n🔎 Test search (query='tourisme maroc'):\n")
        results = search_news("tourisme maroc", top_k=3)
        for i, r in enumerate(results, start=1):
            print(f"--- Result {i} (score={r['score']:.3f}) ---")
            print(f"Title: {r['title']}")
            print(f"URL:   {r['url']}")
            print()
