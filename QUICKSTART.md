# 🚀 Quick Start Guide - ITR Tax Chatbot

## Step-by-Step Setup (5 Minutes)

### 1️⃣ Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (keep it safe!)

### 2️⃣ Setup Backend (2 minutes)

```bash
# Navigate to backend folder
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=paste_your_key_here" > .env

# Start the server
python main.py
```

✅ Backend running at `http://localhost:8001`

### 3️⃣ Setup Frontend (2 minutes)

Open a NEW terminal:

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start the app
npm run dev
```

✅ Frontend running at `http://localhost:3000`

### 4️⃣ Open & Use

1. Open browser: `http://localhost:3000`
2. Start chatting with the AI tax advisor!
3. Try: "I'm a salaried employee, help me file ITR"

## 🎯 Test It Out

Try these queries:
- "What is ITR-1?"
- "Calculate tax on 10 lakh income"
- "Should I choose old or new regime?"
- "What deductions can I claim?"
- "Tell me about Section 80C"

## 🛠️ Troubleshooting

**Port already in use?**
```bash
# Backend - change port in main.py (last line)
uvicorn.run(app, host="0.0.0.0", port=8001)

# Frontend - change port in vite.config.js
server: { port: 3001 }
```

**Module not found?**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
npm install --force
```

**API not connecting?**
- Check backend is running at port 8001
- Check .env file has correct GEMINI_API_KEY
- Check no firewall blocking localhost

## 📞 Need Help?

Check the full README.md for detailed documentation.
