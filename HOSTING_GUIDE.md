# Hosting Guide for Resume Parser

This guide covers multiple hosting options for your Resume Parser application.

## Prerequisites

- GitHub repository with your code
- Grok API keys (for environment variables)
- Basic understanding of cloud platforms

---

## Option 1: Railway (Recommended - Easiest) 🚂

Railway is the easiest option with excellent Docker support.

### Steps:

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**:
   - Go to your project → Variables
   - Add: `GROK_API_KEYS` = `your-api-key-1,your-api-key-2` (comma-separated)
   - Add: `BACKEND_URL` = `http://localhost:8000` (or your Railway backend URL)

4. **Deploy**:
   - Railway will auto-detect your Dockerfile
   - Click "Deploy" and wait for build to complete

5. **Access Your App**:
   - Railway provides a public URL (e.g., `https://your-app.railway.app`)
   - Your Streamlit app will be on port 8501
   - You may need to configure a custom domain

**Pricing**: Free tier available, then pay-as-you-go (~$5-20/month)

---

## Option 2: Render 🎨

Another excellent option with Docker support.

### Steps:

1. **Sign up**: Go to [render.com](https://render.com) and sign up with GitHub

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure**:
   - **Name**: `resume-parser` (or your choice)
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.` (root)

4. **Environment Variables**:
   - `GROK_API_KEYS` = `your-api-key-1,your-api-key-2`
   - `BACKEND_URL` = `http://localhost:8000`

5. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically

**Note**: You may need to modify the Dockerfile to expose only one port (8501 for Streamlit) or use separate services for frontend/backend.

**Pricing**: Free tier available, then ~$7-25/month

---

## Option 3: Fly.io ✈️

Great for Docker deployments with global edge locations.

### Steps:

1. **Install Fly CLI**:
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Sign up**: Go to [fly.io](https://fly.io) and create account

3. **Login**:
   ```bash
   fly auth login
   ```

4. **Create App**:
   ```bash
   fly launch
   ```
   - Follow prompts to create app
   - Select region
   - Don't deploy yet

5. **Create `fly.toml`** (if not auto-generated):
   ```toml
   app = "your-app-name"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 8501
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[services]]
     protocol = "tcp"
     internal_port = 8501
     ports = [
       { handlers = ["http"], port = 80 },
       { handlers = ["tls", "http"], port = 443 }
     ]
   ```

6. **Set Secrets**:
   ```bash
   fly secrets set GROK_API_KEYS="your-api-key-1,your-api-key-2"
   fly secrets set BACKEND_URL="http://localhost:8000"
   ```

7. **Deploy**:
   ```bash
   fly deploy
   ```

**Pricing**: Free tier available, then pay-as-you-go

---

## Option 4: DigitalOcean App Platform 💧

Simple Docker hosting with good performance.

### Steps:

1. **Sign up**: Go to [digitalocean.com](https://digitalocean.com)

2. **Create App**:
   - Go to App Platform
   - Click "Create App"
   - Connect GitHub repository

3. **Configure**:
   - **Source**: GitHub repository
   - **Type**: Docker
   - **Dockerfile Path**: `./Dockerfile`

4. **Environment Variables**:
   - Add `GROK_API_KEYS`
   - Add `BACKEND_URL`

5. **Deploy**:
   - Click "Create Resources"
   - Wait for deployment

**Pricing**: ~$5-12/month

---

## Option 5: VPS (DigitalOcean Droplet, AWS EC2, etc.) 🖥️

For more control, deploy on a VPS.

### Steps:

1. **Create VPS**:
   - DigitalOcean: Create Droplet (Ubuntu 22.04, $6/month minimum)
   - AWS: Launch EC2 instance (t2.micro free tier available)
   - Linode/Vultr: Similar process

2. **SSH into Server**:
   ```bash
   ssh root@your-server-ip
   ```

3. **Install Docker**:
   ```bash
   # Update system
   apt update && apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh

   # Install Docker Compose
   apt install docker-compose -y
   ```

4. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

5. **Create `.env` file**:
   ```bash
   nano .env
   ```
   Add:
   ```
   GROK_API_KEYS=your-api-key-1,your-api-key-2
   BACKEND_URL=http://localhost:8000
   ```

6. **Update docker-compose.yml**:
   Make sure it reads from `.env`:
   ```yaml
   environment:
     - GROK_API_KEYS=${GROK_API_KEYS}
     - BACKEND_URL=${BACKEND_URL}
   ```

7. **Deploy**:
   ```bash
   docker-compose up -d
   ```

8. **Configure Nginx (Reverse Proxy)**:
   ```bash
   apt install nginx -y
   ```

   Create `/etc/nginx/sites-available/resume-parser`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable site:
   ```bash
   ln -s /etc/nginx/sites-available/resume-parser /etc/nginx/sites-enabled/
   nginx -t
   systemctl reload nginx
   ```

9. **SSL Certificate (Let's Encrypt)**:
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d your-domain.com
   ```

---

## Option 6: Google Cloud Run ☁️

Serverless container hosting.

### Steps:

1. **Install Google Cloud SDK**

2. **Build and Push**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/resume-parser
   ```

3. **Deploy**:
   ```bash
   gcloud run deploy resume-parser \
     --image gcr.io/PROJECT-ID/resume-parser \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GROK_API_KEYS="your-keys",BACKEND_URL="http://localhost:8000"
   ```

---

## Important Notes

### Dockerfile Modifications for Production

Your current Dockerfile runs both services in one container. For production, consider:

1. **Separate Services**: Deploy backend and frontend separately
2. **Process Manager**: Use a process manager like `supervisord` for better control
3. **Health Checks**: Add health check endpoints

### Environment Variables

Always set these in your hosting platform:
- `GROK_API_KEYS`: Comma-separated list of API keys
- `BACKEND_URL`: Backend URL (use internal URL for same-host deployments)

### File Storage

Your app processes local files. For cloud hosting:
- Consider using cloud storage (S3, Google Cloud Storage)
- Or mount volumes (Railway, Render support this)
- Or use file uploads instead of folder paths

### Port Configuration

- Backend: Port 8000
- Frontend: Port 8501
- Make sure your hosting platform exposes the correct port

---

## Recommended: Railway or Render

For easiest setup, I recommend **Railway** or **Render**:
- ✅ Automatic deployments from GitHub
- ✅ Docker support out of the box
- ✅ Free tier available
- ✅ Easy environment variable management
- ✅ Automatic HTTPS

---

## Need Help?

- Check platform-specific documentation
- Review Docker logs: `docker logs <container-id>`
- Test locally first: `docker-compose up`
- Verify environment variables are set correctly
