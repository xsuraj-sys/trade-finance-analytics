
# 🚀 Deployment Guide: Trade Finance Analytics Platform

This guide covers two main ways to deploy your application:
1.  **Docker (Recommended for internal demos/VPS)** - Runs both Frontend & Backend in one container.
2.  **Cloud Platforms (Railway/Render)** - Deploys as a web service.

---

## Option 1: Docker (Single Container)
This method packages the entire application (Front + Back) into one image. Ideal for running on a VPS (DigitalOcean, AWS EC2) or locally.

### 1. Build the Image
Run this in the project root:
```bash
docker build -t trade-finance-app .
```

### 2. Run the Container
Map both ports to your host machine:
```bash
docker run -p 8000:8000 -p 8501:8501 trade-finance-app
```
*   **Backend:** `http://localhost:8000`
*   **Frontend:** `http://localhost:8501`

---

## Option 2: Cloud Platform (e.g., Railway/Render)
Since we have a `Dockerfile`, platforms like **Railway** or **Render** can automatically build and deploy this repo.

### Steps for Railway.app (Easiest)
1.  Push your code to **GitHub**.
2.  Log in to [Railway.app](https://railway.app/).
3.  Click **"New Project"** -> **"Deploy from GitHub repo"**.
4.  Select your repository.
5.  Railway will detect the `Dockerfile` and start building.
6.  Once deployed, Railway will give you a public URL (e.g., `https://trade-finance.up.railway.app`).
    *   **Note:** By default, Streamlit runs on port 8501. You may need to set the `PORT` environment variable in Railway to `8501` so it exposes the correct port.
    *   *Advanced:* If you want the backend reachable separately, you might need two services or configure the start script to listen differently. For a simple demo, the single container usually works if the internal routing is `127.0.0.1`.

### Steps for Render.com
1.  Create a **"Web Service"**.
2.  Connect your GitHub repo.
3.  Select **"Docker"** as the runtime.
4.  Deploy.

---

## ⚠️ Important Environment Variables
If you split the frontend and backend into two separate services (e.g. Frontend on Vercel, Backend on Render), you MUST set this environment variable in the Frontend service:

*   `API_URL`: The full URL of your backend (e.g., `https://my-backend-api.onrender.com`).
    *   *Default is `http://127.0.0.1:8000` which only works if they are in the same container.*
