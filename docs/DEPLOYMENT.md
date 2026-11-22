# AgroGuard Production Deployment Guide

This repository is pre-configured for one-click deployment across all major cloud providers.

---

## Deployment Platform Comparison

| Platform | Best For | Persistent DB | Free Tier | Setup Time | Recommended |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **[Render.com](https://render.com)** | Easiest zero-config Python web service | Disk add-on | Yes (Free Web Service) | 2 mins | ⭐⭐⭐ **Top Choice** |
| **[Railway.app](https://railway.app)** | High performance & fastest deploys | Yes (Volumes) | $5 monthly credit | 2 mins | ⭐⭐⭐ **Top Choice** |
| **[Hugging Face Spaces](https://huggingface.co/spaces)** | Academic / AI Community demo | ephemeral | 100% Free (16GB RAM) | 3 mins | ⭐⭐ Great for Demo |
| **[Vercel](https://vercel.com)** | Serverless Jamstack | `/tmp` only (Stateless) | Yes (Hobby) | 2 mins | ⚠️ Limited for ML/DB |

---

## Option 1: Render.com (Recommended — 2 Minutes)

Render provides a native Python 3 web service that reads [`render.yaml`](../render.yaml) and [`Procfile`](../Procfile) automatically.

### Steps:
1. Open [Render.com](https://render.com) and sign in with your GitHub account.
2. Click **New +** in the top navigation bar and select **Web Service**.
3. Select your repository: `chiragchanchal/Ai-powered-grain-spoilage-prevention-system`.
4. Configure the settings:
   - **Name**: `agroguard-grain-spoilage`
   - **Region**: Singapore (`Singapore`) or Frankfurt (closest to your location)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. (Optional) Under **Environment Variables**, add:
   - `OPENWEATHER_API_KEY`: *(Your key, or leave blank to use intelligent realistic fallback)*
   - `FACILITY_NAME`: `Gurugram Central Agro-Mandi Godown`
   - `DEFAULT_REGION`: `Haryana`
6. Click **Create Web Service**.
7. Render will build the environment and provide you with a live URL:
   `https://agroguard-grain-spoilage.onrender.com`

---

## Option 2: Railway.app (Persistent Storage & Fast)

Railway automatically detects the [`Dockerfile`](../Dockerfile) or `Procfile`.

### Steps:
1. Open [Railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `Ai-powered-grain-spoilage-prevention-system`.
4. Click **Deploy Now**.
5. Once deployed, click on the service card:
   - Go to **Settings** → **Networking** → Click **Generate Domain**.
   - Your live public URL will appear immediately (e.g., `https://ai-powered-grain-spoilage...up.railway.app`).
6. *(Optional)* To make farmer custom silo data survive rebuilds:
   - Click **+ New** → **Volume** → Mount to `/app/data`.

---

## Option 3: Hugging Face Spaces (100% Free with 16GB RAM)

Ideal for showcasing this CS002 project to university evaluators and international viewers.

### Steps:
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Set Space Name: `agroguard-grain-spoilage`.
3. License: `mit` or `apache-2.0`.
4. Select **Docker** as the Space SDK → choose **Blank**.
5. Push this repository to your Hugging Face Space git remote:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/agroguard-grain-spoilage
   git push hf main
   ```
6. Hugging Face builds the included `Dockerfile` and provides a permanent public URL with 16GB RAM for free.

---

## Option 4: Vercel (Direct Connection)

The repository includes [`vercel.json`](../vercel.json) and [`api/index.py`](../api/index.py) pre-configured with `@vercel/python`.

### Steps:
1. Go to [Vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New...** → **Project**.
3. Import `chiragchanchal/Ai-powered-grain-spoilage-prevention-system`.
4. Leave Framework Preset as **Other**.
5. Click **Deploy**.

> [!NOTE]
> **Vercel Serverless Consideration**:
> Vercel runs on AWS Lambda serverless functions. AgroGuard is engineered to automatically divert SQLite time-series data to `/tmp/data` on Vercel so it won't crash. However, AWS Lambda instances are stateless and cycle when idle, meaning custom farmer silos created in the session may reset upon a cold start. For permanent persistence and zero cold starts, **Render** or **Railway** is recommended.

---

## Verification Checklist After Deployment

Once deployed on any platform, test these endpoints to confirm 100% functionality:
- Home Dashboard: `https://<your-app-url>/`
- API Health Check: `https://<your-app-url>/api/health`
- Silo Fleet Telemetry: `https://<your-app-url>/api/silos`
- Weather Feed: `https://<your-app-url>/api/weather/current`
- Model Prediction: `https://<your-app-url>/api/predict`
- Audit Certificate: Click **Inspection Sheet** on the navbar and verify printing.
