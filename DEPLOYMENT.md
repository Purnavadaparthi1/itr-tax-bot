# 🚀 Deployment Guide - ITR Tax Chatbot

## Production Deployment Options

### Option 1: Deploy to Railway (Recommended - Free Tier Available)

#### Backend on Railway

1. **Sign up** at [Railway.app](https://railway.app)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository

3. **Configure Backend**
   - Root directory: `/backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Go to Variables tab
   - Add: `GEMINI_API_KEY=your_key`

5. **Deploy** - Railway will auto-deploy!

#### Frontend on Vercel

1. **Sign up** at [Vercel.com](https://vercel.com)

2. **Import Project**
   - Click "Import Project"
   - Select your Git repository
   - Root directory: `/frontend`

3. **Configure Build**
   - Build command: `npm run build`
   - Output directory: `dist`
   - Framework: Vite

4. **Environment Variables**
   - Add: `VITE_API_URL=https://your-backend-url.railway.app`

5. **Deploy** - Done!

---

### Option 2: Deploy to Render

#### Backend

1. Go to [Render.com](https://render.com)
2. Create new "Web Service"
3. Connect repository
4. Configure:
   - Root directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GEMINI_API_KEY`

#### Frontend

1. Create "Static Site"
2. Root: `frontend`
3. Build: `npm install && npm run build`
4. Publish: `dist`
5. Add env: `VITE_API_URL=your-backend-url`

---

### Option 3: Deploy to DigitalOcean App Platform

1. Create account at [DigitalOcean](https://www.digitalocean.com)
2. Go to App Platform
3. Create new app from GitHub
4. Configure backend and frontend components
5. Add environment variables
6. Deploy

**Monthly Cost**: ~$12/month for both services

---

### Option 4: Self-Host on VPS (Ubuntu)

#### Setup Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Nginx
sudo apt install nginx -y
```

#### Deploy Backend

```bash
# Clone repository
git clone your-repo-url
cd itr-tax-bot/backend

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install gunicorn
pip install gunicorn

# Create .env file
nano .env
# Add: GEMINI_API_KEY=your_key

# Create systemd service
sudo nano /etc/systemd/system/itr-backend.service
```

Add this content:
```ini
[Unit]
Description=ITR Tax Chatbot Backend
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/itr-tax-bot/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start itr-backend
sudo systemctl enable itr-backend
```

#### Deploy Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Build
npm run build

# Copy to nginx
sudo cp -r dist/* /var/www/html/
```

#### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/itr-tax-bot
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/itr-tax-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Setup SSL (Optional but Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com
```

---

## Environment Variables for Production

### Backend (.env)
```env
GEMINI_API_KEY=your_production_key
DEBUG=False
ALLOWED_ORIGINS=https://your-domain.com
DATABASE_URL=postgresql://user:pass@host/db  # If using database
REDIS_URL=redis://localhost:6379/0  # If using Redis
```

### Frontend
```env
VITE_API_URL=https://api.your-domain.com
```

---

## Performance Optimization

### Backend
- Use gunicorn with multiple workers (4-8)
- Enable response caching with Redis
- Add database for persistent storage
- Use CDN for static assets

### Frontend
- Enable gzip compression in Nginx
- Use CDN (Cloudflare, AWS CloudFront)
- Optimize images
- Enable browser caching

---

## Monitoring & Logging

### Setup PM2 (Alternative to systemd)
```bash
npm install -g pm2

# Start backend
pm2 start "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001" --name itr-backend

# Save configuration
pm2 save

# Auto-start on boot
pm2 startup
```

### Logging
```bash
# View logs
pm2 logs itr-backend

# Or with systemd
sudo journalctl -u itr-backend -f
```

---

## Cost Comparison

| Platform | Cost/Month | Pros | Cons |
|----------|-----------|------|------|
| Railway | Free - $5 | Easy, free tier | Limited resources |
| Render | Free - $7 | Simple setup | Cold starts on free |
| Vercel | Free | Great frontend | Need separate backend |
| DigitalOcean | $12+ | Full control | Manual setup |
| VPS | $5+ | Maximum control | Requires sysadmin |

---

## Security Checklist

- [ ] Use HTTPS (SSL certificate)
- [ ] Set strong SECRET_KEY
- [ ] Enable CORS only for your domain
- [ ] Rate limit API endpoints
- [ ] Sanitize user inputs
- [ ] Keep dependencies updated
- [ ] Monitor logs for suspicious activity
- [ ] Regular backups (if using database)

---

## Scaling Considerations

For high traffic:
1. Use load balancer (Nginx, AWS ALB)
2. Multiple backend instances
3. Database connection pooling
4. Redis for caching and sessions
5. CDN for static assets
6. Horizontal scaling with Kubernetes

---

Need help with deployment? Check the main README or open an issue!
