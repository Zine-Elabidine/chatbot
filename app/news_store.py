import os
import json
from typing import List, Dict

import requests
from dotenv import load_dotenv
from fastembed import TextEmbedding
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

_EMBED_MODEL: TextEmbedding | None = None
_QDRANT_CLIENT: QdrantClient | None = None


def get_embed_model() -> TextEmbedding:
    """Return a shared FastEmbed text embedding model."""
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = TextEmbedding()
    return _EMBED_MODEL


def embed_text(text: str) -> List[float]:
    """Embed a single text using FastEmbed TextEmbedding."""
    model = get_embed_model()
    # FastEmbed expects an iterable of texts and returns an iterator of embeddings
    embedding_iter = model.embed([text])
    embedding = next(embedding_iter)
    return embedding.tolist()


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
    params = {
        "per_page": min(limit, 100),
        "orderby": "date",
        "order": "desc",
    }
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            print(f"[fetch_posts] Attempt {attempt + 1} failed: {e}")

    # If all retries failed, propagate the last error
    if last_error is not None:
        raise last_error

    return []


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


def chunk_text(text: str, max_chars: int = 1000) -> List[str]:
    """Split long text into smaller chunks by characters.

    This is a simple character-based splitter; for production you might
    switch to a token-based splitter.
    """
    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunks.append(text[start:end])
        start = end
    return chunks


def refresh_all_posts(limit: int = 50, batch_size: int = 10) -> None:
    """Fetch latest posts from WordPress, embed them in batches, and rebuild the Qdrant index."""
    print(f"⌘ Fetching up to {limit} posts from {WORDPRESS_BASE_URL}...")
    qclient = get_qdrant_client()

    try:
        posts = fetch_posts(limit=limit)
        print(f"✅ Retrieved {len(posts)} posts")
    except Exception as e:
        print(f"[refresh_all_posts] Error fetching posts after retries: {e}")
        posts = []

    if not posts:
        # Never rely on old data: clear the existing collection if it exists
        try:
            qclient.delete_collection(collection_name=QDRANT_COLLECTION)
            print(
                f"⚠️ No posts fetched; deleted Qdrant collection '{QDRANT_COLLECTION}' to avoid stale data."
            )
        except Exception as e:
            print(f"[refresh_all_posts] Error deleting Qdrant collection: {e}")
        return
    
    try:
        # Process posts in batches
        total_posts = len(posts)
        total_chunks_indexed = 0
        vector_size = None
        collection_created = False
        
        for batch_start in range(0, total_posts, batch_size):
            batch_end = min(batch_start + batch_size, total_posts)
            batch_posts = posts[batch_start:batch_end]
            
            print(f"📦 Processing batch {batch_start//batch_size + 1}/{(total_posts + batch_size - 1)//batch_size} (posts {batch_start+1}-{batch_end})...")
            
            points: List[qmodels.PointStruct] = []
            point_id = total_chunks_indexed + 1

            for post in batch_posts:
                post_id = post.get("id")
                title = post.get("title", {}).get("rendered", "")
                content_html = post.get("content", {}).get("rendered", "")
                url = post.get("link", "")
                date = post.get("date", "")

                content_text = html_to_text(content_html)
                if not content_text:
                    continue

                chunks = chunk_text(content_text, max_chars=1000)
                if not chunks:
                    continue

                for idx, chunk in enumerate(chunks):
                    vec = embed_text(chunk)
                    if not vec:
                        continue
                    
                    # Get vector size from first embedding
                    if vector_size is None:
                        vector_size = len(vec)
                    
                    payload = {
                        "post_id": post_id,
                        "chunk_index": idx,
                        "title": title,
                        "url": url,
                        "date": date,
                        "text": chunk,
                    }
                    points.append(
                        qmodels.PointStruct(
                            id=point_id,
                            vector=vec,
                            payload=payload,
                        )
                    )
                    point_id += 1
            
            # Create collection on first batch with points
            if points and not collection_created:
                if vector_size is None:
                    vector_size = len(points[0].vector)
                
                qclient.recreate_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                collection_created = True
                print(f"✅ Created collection '{QDRANT_COLLECTION}' with vector size {vector_size}")
            
            # Upsert batch points
            if points:
                qclient.upsert(
                    collection_name=QDRANT_COLLECTION,
                    points=points,
                )
                total_chunks_indexed += len(points)
                print(f"   ✅ Indexed {len(points)} chunks from batch")

        if total_chunks_indexed == 0:
            # We fetched posts but produced no embeddings; clear the collection to avoid stale data
            try:
                qclient.delete_collection(collection_name=QDRANT_COLLECTION)
                print(
                    f"⚠️ No points produced; deleted Qdrant collection '{QDRANT_COLLECTION}' to avoid stale data."
                )
            except Exception as e:
                print(f"[refresh_all_posts] Error deleting Qdrant collection after empty points: {e}")
            return

        print(
            f"✅ Completed! Indexed {total_chunks_indexed} chunks from {total_posts} posts into Qdrant collection '{QDRANT_COLLECTION}'"
        )

    except Exception as e:
        print(f"[refresh_all_posts] Error during embedding/indexing: {e}")
        # On any embedding or indexing error, delete the collection to avoid using stale data
        try:
            qclient.delete_collection(collection_name=QDRANT_COLLECTION)
            print(
                f"⚠️ Error during indexing; deleted Qdrant collection '{QDRANT_COLLECTION}' to avoid stale data."
            )
        except Exception as e2:
            print(f"[refresh_all_posts] Error deleting Qdrant collection after failure: {e2}")


def search_news(query: str, top_k: int = 5) -> List[Dict]:
    """Search indexed news chunks for a query using Qdrant."""
    qclient = get_qdrant_client()

    try:
        query_vec = embed_text(query)
    except Exception as e:
        print(f"[search_news] Error embedding query: {e}")
        return []

    try:
        response = qclient.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vec,
            limit=top_k,
        )
        results = response.points
    except Exception as e:
        print(f"[search_news] Error querying Qdrant: {e}")
        return []

    scored: List[Dict] = []
    for r in results:
        payload = r.payload or {}
        scored.append(
            {
                "post_id": payload.get("post_id"),
                "chunk_index": payload.get("chunk_index"),
                "title": payload.get("title", ""),
                "url": payload.get("url", ""),
                "date": payload.get("date", ""),
                "text": payload.get("text", ""),
                "score": r.score,
            }
        )

    return scored


if __name__ == "__main__":
    # Simple manual test against the local WordPress site
    refresh_all_posts(limit=20)

    print("\n🔎 Test search (query='Hello'):\n")
    results = search_news("Hello", top_k=3)
    for i, r in enumerate(results, start=1):
        print(f"--- Result {i} (score={r['score']:.3f}) ---")
        print(f"Title: {r['title']}")
        print(f"URL:   {r['url']}")
        print(f"Date:  {r['date']}")
        print(f"Text snippet: {r['text'][:200]}...")
        print()
