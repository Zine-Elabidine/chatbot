# Deployment Guide: Render + Qdrant Cloud

This guide walks you through deploying the Conso News Chatbot to **Render** (FastAPI backend) and **Qdrant Cloud** (vector database).

---

## Prerequisites

- GitHub account (to push your code)
- Render account (free tier available at https://render.com)
- Qdrant Cloud account (free tier at https://cloud.qdrant.io)
- API keys for:
  - OpenAI (or compatible LLM provider)
  - Tavily (web search)

---

## Step 1: Set Up Qdrant Cloud

### 1.1 Create Account & Cluster

1. Go to https://cloud.qdrant.io/ and sign up
2. Create a new cluster:
   - Choose **Free Tier** (1GB storage, ~100k+ vectors)
   - Select a region close to your Render deployment
3. Wait for cluster to be ready (~2 minutes)

### 1.2 Get Credentials

From your cluster dashboard:
- **Cluster URL**: e.g., `abc123-xyz.eu-central.aws.cloud.qdrant.io`
- **API Key**: Generate one in "API Keys" section

**Important**: Save these for Step 3.

---

## Step 2: Push Code to GitHub

1. Initialize git repo (if not already done):
   ```bash
   cd chatbot
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. Create a new repository on GitHub

3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

**Security Note**: Make sure `app/.env` is in `.gitignore` and NOT committed!

---

## Step 3: Deploy to Render

### 3.1 Create Web Service

1. Go to https://render.com/dashboard
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `conso-news-chatbot` (or your choice)
   - **Root Directory**: `app`
   - **Environment**: `Docker`
   - **Region**: Choose same region as Qdrant Cloud (if possible)
   - **Instance Type**: Free tier is fine for testing

### 3.2 Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

```env
# LLM Configuration
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.2

# Web Search
TAVILY_API_KEY=tvly-...

# WordPress
WORDPRESS_BASE_URL=https://consonews.ma

# Qdrant Cloud
QDRANT_HOST=abc123-xyz.eu-central.aws.cloud.qdrant.io
QDRANT_PORT=443
QDRANT_API_KEY=your-qdrant-cloud-api-key
QDRANT_COLLECTION=conso_news_articles
```

**Replace**:
- `QDRANT_HOST` with your cluster URL (without `https://`)
- `QDRANT_API_KEY` with your Qdrant API key from Step 1.2
- Other API keys with your actual keys

### 3.3 Deploy

1. Click **Create Web Service**
2. Render will:
   - Build the Docker image (~5-10 minutes first time)
   - Deploy the container
   - Assign a URL: `https://your-app-name.onrender.com`

3. Monitor logs for:
   ```
   ⌘ Fetching up to 200 posts from https://consonews.ma...
   ✅ Retrieved X posts
   ✅ Indexed Y chunks from X posts into Qdrant collection 'conso_news_articles'
   ```

---

## Step 4: Update WordPress Plugin

### 4.1 Update API URL

In your WordPress plugin files:

**File**: `wp-plugin/conso-news-chatbot/assets/js/chatbot.js`

Find the line:
```javascript
API_URL: 'http://localhost:8000'
```

Change to:
```javascript
API_URL: 'https://your-app-name.onrender.com'
```

**Also update** `wordpress_integration.js` if you're using the standalone widget.

### 4.2 Deploy Plugin

1. Zip the `wp-plugin/conso-news-chatbot` folder
2. Upload to WordPress:
   - Go to WordPress Admin → Plugins → Add New → Upload Plugin
   - Upload the zip file
   - Activate the plugin

---

## Step 5: Test

1. Visit your WordPress site
2. The chatbot widget should appear in the bottom-right corner
3. Test queries:
   - Ask about recent Conso News articles
   - Ask general questions (will use Tavily web search)

---

## Monitoring & Maintenance

### Check Render Logs
- Go to Render dashboard → Your service → Logs
- Look for indexing success/errors

### Check Qdrant Cloud
- Go to Qdrant Cloud dashboard → Your cluster
- Check collection `conso_news_articles` has points
- Monitor storage usage

### Refresh Schedule
- The app automatically refreshes WordPress posts **every 1 hour**
- To change frequency, edit `app/main.py` line 43:
  ```python
  scheduler.add_job(refresh_all_posts, "interval", hours=1, ...)
  ```

---

## Troubleshooting

### "Collection doesn't exist" errors
- Check Qdrant Cloud credentials in Render environment variables
- Check Render logs for indexing errors

### No articles found in chatbot
- Verify `WORDPRESS_BASE_URL` is correct
- Check WordPress REST API is accessible: `https://consonews.ma/wp-json/wp/v2/posts`
- Check Render logs for fetch/embedding errors

### Slow responses
- Free tier Render instances sleep after inactivity (~15 min)
- First request after sleep takes ~30s to wake up
- Consider upgrading to paid tier for always-on service

---

## Costs

### Free Tier Limits
- **Render**: 750 hours/month (enough for 1 service 24/7)
- **Qdrant Cloud**: 1GB storage (~100k-200k vectors)

### When to Upgrade
- If you need faster cold starts → Render paid tier ($7/month)
- If you exceed 1GB vectors → Qdrant Cloud paid tier ($25/month)

---

## Support

For issues:
1. Check Render logs first
2. Check Qdrant Cloud dashboard
3. Verify all environment variables are set correctly
4. Test WordPress REST API endpoint directly

---

## Security Notes

- Never commit `.env` files to git
- Rotate API keys periodically
- In production, restrict CORS in `app/main.py`:
  ```python
  allow_origins=["https://consonews.ma"]  # Instead of ["*"]
  ```
