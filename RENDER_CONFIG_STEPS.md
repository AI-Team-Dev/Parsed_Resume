# Render.com Configuration - Step by Step

## On the Configuration Page:

### 1. Basic Settings ✅
- **Name**: `Parsed_Resume` (or `resume-parser`) - Already set ✓
- **Language**: `Docker` - Already set ✓
- **Branch**: `main` - Already set ✓
- **Region**: `Virginia (US East)` - Good choice ✓
- **Root Directory**: Leave **EMPTY** ✓

### 2. Instance Type
Choose one:
- **Free** (for testing) - 512 MB RAM, 0.1 CPU
- **Starter** ($7/month) - 512 MB RAM, 0.5 CPU (recommended for production)

### 3. Dockerfile Configuration
**IMPORTANT**: You need to set the Dockerfile path!

**Option A - If "Advanced" section is visible:**
1. Click to expand "Advanced" section
2. Find "Dockerfile Path" field
3. Enter: `./Dockerfile.production`
4. Docker Context: `.` (just a dot)

**Option B - If no Advanced section:**
Render might auto-detect `Dockerfile`. Since we use `Dockerfile.production`, you may need to:
1. Rename `Dockerfile.production` to `Dockerfile` temporarily, OR
2. Check if there's a "Build Command" or "Dockerfile" field in the main form

### 4. Environment Variables (CRITICAL!)

**Remove the default:**
- Delete `BUILT_IN_PORT=10000` (click the X or remove it)

**Add these two:**

1. **First Variable:**
   - Click "Add Environment Variable"
   - **Key**: `GROK_API_KEYS`
   - **Value**: `your-api-key-1,your-api-key-2` (replace with your actual keys, comma-separated)
   - Click "Add" or "Save"

2. **Second Variable:**
   - Click "Add Environment Variable" again
   - **Key**: `BACKEND_URL`
   - **Value**: `http://localhost:8000`
   - Click "Add" or "Save"

### 5. Deploy!
- Scroll to bottom
- Click **"Deploy Web Service"** button
- Wait 3-5 minutes for build

## ✅ Final Checklist Before Deploying:

- [ ] Dockerfile path set to `./Dockerfile.production` (or renamed to `Dockerfile`)
- [ ] `GROK_API_KEYS` environment variable added with your actual keys
- [ ] `BACKEND_URL` environment variable set to `http://localhost:8000`
- [ ] `BUILT_IN_PORT` removed (if it was there)
- [ ] Instance type selected (Free or Starter)

## 🚨 Common Issues:

**"Dockerfile not found" error:**
- Make sure `Dockerfile.production` exists in your GitHub repo
- Or rename it to `Dockerfile` and update the path

**"Build fails":**
- Check that all files are pushed to GitHub
- Verify `supervisord.conf` exists in repo
- Check build logs in Render dashboard

**"App won't start":**
- Verify environment variables are set correctly
- Check application logs in Render dashboard
- Make sure API keys are comma-separated with no spaces

## After Deployment:

Your app will be available at:
`https://parsed-resume.onrender.com` (or your chosen name)

The first deploy takes 5-10 minutes. Subsequent deploys are faster!
