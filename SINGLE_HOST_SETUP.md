# 🚀 Single Host Setup - Run Everything on Port 8001

## Simple 3-Step Process

### Step 1: Build Frontend (One-time)
```bash
cd frontend
npm install
npm run build
```

This creates a `dist` folder with your compiled React app.

### Step 2: Setup Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key to .env file
# Edit .env and replace with your actual key
```

### Step 3: Run Single Server
```bash
cd backend
python unified_server.py
```

That's it! Everything runs on **http://localhost:8001** 🎉

---

## What This Does

The unified server:
✅ Runs backend API on `/api/*` routes
✅ Serves frontend React app on `/` route  
✅ Single port: 8001
✅ No CORS issues
✅ Easy to deploy

---

## Quick Commands

```bash
# From project root (itr-tax-bot/)

# Build frontend (do this once, or after any frontend changes)
cd frontend && npm run build && cd ..

# Run everything
cd backend && python unified_server.py
```

---

## If You Want Development Mode (Hot Reload)

For development with auto-reload:

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend  
npm run dev
```

Then access at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

---

## Troubleshooting

**Frontend not showing?**
```bash
# Make sure you built the frontend first
cd frontend
npm run build

# Check if dist folder exists
ls dist/
```

**Still not working?**
The unified server looks for `frontend/dist` folder. Make sure:
1. You ran `npm run build` in frontend folder
2. The `dist` folder exists with index.html inside
3. You're running from `backend/` folder

---

## Production Deployment

For production, just:
1. Build frontend: `npm run build`
2. Run unified server: `python unified_server.py`
3. Everything is on port 8001!

Perfect for deploying to Railway, Render, or any cloud platform! 🚀
