# 📝 Commands Reference - ITR Tax Chatbot

Quick reference for all commands you'll need.

## 🐍 Backend Commands

### Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Then edit .env and add your GEMINI_API_KEY
```

### Run Development Server
```bash
# Standard way
python main.py

# With uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# With custom port
uvicorn main:app --reload --port 8001
```

### Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

# Run with more workers (8)
gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### Dependency Management
```bash
# Add new dependency
pip install package-name
pip freeze > requirements.txt

# Update all dependencies
pip install --upgrade -r requirements.txt

# Check installed packages
pip list

# Check outdated packages
pip list --outdated
```

### Testing
```bash
# Install pytest
pip install pytest pytest-cov

# Run tests (when you create them)
pytest

# Run with coverage
pytest --cov=.
```

---

## ⚛️ Frontend Commands

### Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Or with yarn
yarn install

# Or with pnpm
pnpm install
```

### Development
```bash
# Start development server
npm run dev

# Start with custom port
npm run dev -- --port 3001

# Start with custom host
npm run dev -- --host 0.0.0.0

# Open in browser automatically
npm run dev -- --open
```

### Build & Production
```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Build and preview
npm run build && npm run preview
```

### Dependency Management
```bash
# Add new dependency
npm install package-name

# Add dev dependency
npm install -D package-name

# Update all dependencies
npm update

# Check outdated packages
npm outdated

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Linting & Formatting
```bash
# Run linter
npm run lint

# Fix linting issues
npm run lint -- --fix

# Install prettier (optional)
npm install -D prettier
npx prettier --write src/**/*.{js,jsx,css}
```

---

## 🔧 Environment Configuration

### Backend .env
```bash
# View current environment
cat .env

# Edit environment file (Windows)
notepad .env

# Edit environment file (Mac/Linux)
nano .env
# or
vim .env

# Set environment variable (Linux/Mac - temporary)
export GEMINI_API_KEY=your_key_here

# Set environment variable (Windows - temporary)
set GEMINI_API_KEY=your_key_here
```

### Frontend Environment
```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8001" > .env

# For production
echo "VITE_API_URL=https://your-production-api.com" > .env.production
```

---

## 🐳 Docker Commands (Optional)

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    env_file:
      - ./backend/.env
    
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### Docker Commands
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose up --build backend
```

---

## 🔍 Debugging Commands

### Backend Debugging
```bash
# Run with debug mode
DEBUG=True python main.py

# Check FastAPI docs
# Open: http://localhost:8001/docs

# Test endpoint
curl http://localhost:8001/
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"Hello"}'

# View logs
tail -f logs/app.log
```

### Frontend Debugging
```bash
# Check for errors in build
npm run build 2>&1 | tee build-errors.log

# Analyze bundle size
npm install -D vite-plugin-visualizer
# Add to vite.config.js and run build

# Clear cache
rm -rf node_modules/.vite
npm run dev
```

---

## 📊 Monitoring Commands

### Check if servers are running
```bash
# Check backend
curl http://localhost:8001/

# Check frontend
curl http://localhost:3000/

# Check if port is in use (Linux/Mac)
lsof -i :8001
lsof -i :3000

# Check if port is in use (Windows)
netstat -ano | findstr :8001
netstat -ano | findstr :3000
```

### Kill process on port
```bash
# Linux/Mac
kill -9 $(lsof -t -i:8001)
kill -9 $(lsof -t -i:3000)

# Windows
# Find PID from netstat, then:
taskkill /PID <PID> /F
```

---

## 🚀 Deployment Commands

### Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Deploy to Vercel (Frontend)
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

### Deploy to Render
```bash
# Just push to Git
git add .
git commit -m "Deploy to Render"
git push origin main

# Render auto-deploys from Git
```

---

## 🔄 Git Commands

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Add remote
git remote add origin https://github.com/username/itr-tax-bot.git

# Push
git push -u origin main

# Pull latest
git pull origin main

# Create new branch
git checkout -b feature/new-feature

# Switch branch
git checkout main

# Merge branch
git merge feature/new-feature
```

---

## 🧪 Testing API Endpoints

### Using curl
```bash
# Health check
curl http://localhost:8001/

# Chat endpoint
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "message": "What is ITR-1?",
    "context": {}
  }'

# Calculate tax
curl -X POST http://localhost:8001/api/calculate-tax \
  -H "Content-Type: application/json" \
  -d '{
    "total_income": 1000000,
    "deductions": {
      "section_80c": 150000,
      "section_80d": 25000
    },
    "regime": "new"
  }'

# Get tax slabs
curl http://localhost:8001/api/tax-info/slabs

# Get full forms
curl http://localhost:8001/api/full-forms
```

### Using Python requests
```python
import requests

# Chat
response = requests.post(
    'http://localhost:8001/api/chat',
    json={
        'session_id': 'test123',
        'message': 'Hello',
        'context': {}
    }
)
print(response.json())
```

---

## 💾 Backup & Restore

```bash
# Backup entire project
tar -czf itr-tax-bot-backup.tar.gz itr-tax-bot/

# Restore
tar -xzf itr-tax-bot-backup.tar.gz

# Backup just database (if using one)
pg_dump dbname > backup.sql

# Restore database
psql dbname < backup.sql
```

---

## 🆘 Troubleshooting Commands

```bash
# Check Python version
python --version

# Check Node version
node --version
npm --version

# Check if Gemini API key is set
echo $GEMINI_API_KEY  # Linux/Mac
echo %GEMINI_API_KEY%  # Windows

# Reinstall everything
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
rm -rf node_modules package-lock.json
npm install

# Check network connectivity
ping google.com
curl https://generativelanguage.googleapis.com
```

---

Save this file for quick reference! 🚀
