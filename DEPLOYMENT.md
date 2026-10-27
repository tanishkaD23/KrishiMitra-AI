# KrishiMitra AI — Deployment & Production Guide

This guide explains how to run, test, and deploy the KrishiMitra AI web application to production platforms (Render, Railway, Cloud Run, Docker).

---

## 1. Local Development Run

Ensure dependencies are installed and `.env` has your OpenAI API key:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the FastAPI Uvicorn Server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
- **Landing Page**: [http://localhost:8000](http://localhost:8000)
- **Farmer Dashboard Portal**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 2. Deploy to Render (Recommended - Free / Low Cost)

Render natively runs Python ASGI applications.

1. Push your repository to **GitHub**:
   ```bash
   git add .
   git commit -m "Build professional KrishiMitra AI web application"
   git push origin main
   ```
2. Log into [Render.com](https://render.com) and click **New → Web Service**.
3. Connect your KrishiMitra AI GitHub repository.
4. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `OPENAI_API_KEY` = `your_openai_api_key_here`
6. Click **Create Web Service**. Your app will be live with free automatic SSL (HTTPS).

---

## 3. Deploy to Railway

1. Install the Railway CLI or link via GitHub at [railway.app](https://railway.app).
2. Click **New Project → Deploy from GitHub repo**.
3. Railway automatically detects the included `Procfile` and `requirements.txt`.
4. In the **Variables** tab, set:
   - `OPENAI_API_KEY` = `your_openai_api_key_here`
5. Click **Deploy**. Your custom URL is generated automatically.

---

## 4. Deploy with Docker / Google Cloud Run

Build and run anywhere with Docker:

```bash
# Build the container image
docker build -t krishimitra-ai:latest .

# Run the container locally
docker run -p 8000:8000 -e OPENAI_API_KEY="your_key" krishimitra-ai:latest
```

To deploy to **Google Cloud Run**:
```bash
gcloud builds submit --tag gcr.io/[PROJECT-ID]/krishimitra-ai
gcloud run deploy krishimitra-ai --image gcr.io/[PROJECT-ID]/krishimitra-ai --platform managed --allow-unauthenticated
```

---

## 5. Security & Verification Checklist

- [x] `.env` is listed in `.gitignore` and never committed to source control.
- [x] No API keys are leaked or exposed in frontend JavaScript files.
- [x] Fallback mechanisms are in place if the OpenAI quota is exhausted or offline.
- [x] 57 unit tests pass with `python -m unittest discover -s tests`.
