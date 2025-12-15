# 🚀 Deploy to Render.com - Quick Guide

## Prerequisites
- ✅ Code pushed to GitHub
- ✅ Render.com account (free)

## Deploy in 3 Steps

### 1. Go to Render Dashboard
Visit [dashboard.render.com](https://dashboard.render.com)

### 2. Create New Web Service
- Click **"New +"** → **"Web Service"**
- Connect GitHub and select your repository
- Use these settings:
  ```
  Name: resume-parser
  Environment: Docker
  Dockerfile Path: ./Dockerfile.production
  Docker Context: .
  ```

### 3. Add Environment Variables
In the Environment tab, add:
```
GROK_API_KEYS = your-key-1,your-key-2
BACKEND_URL = http://localhost:8000
```

### 4. Deploy!
Click **"Create Web Service"** and wait 3-5 minutes.

Your app will be live at: `https://your-app.onrender.com`

---

## ✅ Files Ready for Render

- ✅ `Dockerfile.production` - Production-ready Docker image
- ✅ `render.yaml` - Render configuration (optional)
- ✅ `backend/config.py` - Reads from environment variables
- ✅ `.gitignore` - Protects sensitive files

## 📖 Full Instructions

See `RENDER_DEPLOY.md` for detailed step-by-step guide.
