# Deploy to Render.com - Step by Step Guide 🚀

## Quick Deploy (5 minutes)

### Step 1: Push to GitHub
Make sure your code is pushed to GitHub first.

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub (free)

### Step 3: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select your repository

### Step 4: Configure Service
Use these settings:
- **Name**: `resume-parser` (or your choice)
- **Environment**: `Docker`
- **Dockerfile Path**: `./Dockerfile.production`
- **Docker Context**: `.` (root directory)
- **Region**: Choose closest to you
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty

### Step 5: Set Environment Variables
Click **"Environment"** tab and add:

1. **GROK_API_KEYS**
   - Value: `your-api-key-1,your-api-key-2` (comma-separated)
   - Click **"Add Environment Variable"**

2. **BACKEND_URL**
   - Value: `http://localhost:8000`
   - Click **"Add Environment Variable"**

### Step 6: Deploy
1. Scroll down and click **"Create Web Service"**
2. Render will automatically:
   - Build your Docker image
   - Deploy your application
   - Provide a public URL

### Step 7: Access Your App
- Wait 3-5 minutes for build to complete
- Your app will be available at: `https://your-app-name.onrender.com`
- The Streamlit frontend will be accessible on this URL

## ✅ That's It!

Your Resume Parser is now live on Render!

## 🔧 Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify Dockerfile.production exists
- Ensure all files are in GitHub

### App Won't Start
- Check environment variables are set correctly
- Verify GROK_API_KEYS format (comma-separated, no spaces)
- Check application logs in Render dashboard

### Backend Not Connecting
- Verify BACKEND_URL is set to `http://localhost:8000`
- Check that both services are running (backend on 8000, frontend on PORT)

## 📝 Notes

- **Free Tier**: Render free tier spins down after 15 minutes of inactivity
- **First Deploy**: May take 5-10 minutes
- **Subsequent Deploys**: Faster (2-3 minutes)
- **Auto-Deploy**: Render auto-deploys on git push (if enabled)

## 🔄 Updating Your App

Just push to GitHub:
```bash
git add .
git commit -m "Update app"
git push
```

Render will automatically redeploy!
