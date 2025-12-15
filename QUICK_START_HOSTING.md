# Quick Start: Host Your Resume Parser

## 🚀 Fastest Option: Railway (5 minutes)

### Step 1: Prepare Your Repository
Make sure your code is pushed to GitHub.

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect your Dockerfile

### Step 3: Set Environment Variables
In Railway dashboard:
- Go to your project → Variables tab
- Add: `GROK_API_KEYS` = `your-key-1,your-key-2`
- Add: `BACKEND_URL` = `http://localhost:8000`

### Step 4: Deploy
- Railway will automatically deploy
- Wait 2-3 minutes for build
- Get your public URL from the dashboard

### Step 5: Access Your App
- Railway provides a URL like: `https://your-app.up.railway.app`
- Your Streamlit app is accessible on this URL

**That's it!** Your app is live. 🎉

---

## 🎨 Alternative: Render (Similar Process)

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. New → Web Service
4. Connect repository
5. Set:
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile` (or `./Dockerfile.production`)
6. Add environment variables (same as Railway)
7. Deploy!

---

## 📝 Before Deploying

### 1. Create `.env` file (for local testing):
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Test Locally:
```bash
docker-compose up
```

### 3. Push to GitHub:
```bash
git add .
git commit -m "Ready for deployment"
git push
```

---

## 🔧 Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify all files are in repository
- Check build logs in platform dashboard

### App Won't Start
- Verify environment variables are set
- Check application logs
- Ensure ports are correctly exposed

### Can't Access App
- Check if deployment completed successfully
- Verify public URL is correct
- Check firewall/security settings

---

## 💡 Pro Tips

1. **Use Production Dockerfile**: The `Dockerfile.production` uses supervisor for better process management
2. **Monitor Logs**: Always check logs in your hosting platform dashboard
3. **Set Up Custom Domain**: Most platforms allow custom domains (optional)
4. **Enable Auto-Deploy**: Connect GitHub for automatic deployments on push

---

## 📚 More Options

See `HOSTING_GUIDE.md` for:
- VPS deployment
- AWS/GCP/Azure
- Fly.io
- DigitalOcean
- And more!
