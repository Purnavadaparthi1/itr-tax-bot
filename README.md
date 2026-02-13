# 🇮🇳 ITR Tax Filing & Advisory Chatbot

A complete, production-ready AI-powered Chartered Accountant assistant for Indian Income Tax Return (ITR) filing. Built with modern technologies and beautiful UI design.

![ITR Tax Advisor](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🤖 AI-Powered Tax Advisory
- **Intelligent Chatbot**: Gemini 1.5 Pro powered conversational AI
- **CA-like Interview**: Step-by-step data collection like a Chartered Accountant
- **Context-Aware**: Remembers conversation history and user profile
- **Full Forms Helper**: Explains all tax abbreviations (ITR, PAN, AIS, etc.)

### 💰 Tax Calculation Engine
- **Rule-Based Calculator**: Accurate tax computation for FY 2024-25
- **Both Regimes**: Support for old and new tax regimes
- **Smart Recommendations**: Suggests best regime based on your profile
- **All Deductions**: Section 80C, 80D, 80E, 80G, 24(b), and more
- **Rebate u/s 87A**: Automatic rebate calculation

### 📋 ITR Form Selection
- **Intelligent Mapping**: Recommends correct ITR form (ITR-1 to ITR-4)
- **Income-Based**: Based on salary, business, capital gains, rental income
- **Alternative Suggestions**: Provides backup form options

### 🎨 Beautiful Modern UI
- **Glassmorphism Design**: Stunning frosted glass effects
- **Smooth Animations**: Framer Motion powered interactions
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Dark Theme**: Eye-friendly dark mode with gradient accents
- **Custom Fonts**: Manrope, Sora, and JetBrains Mono

### 📊 Interactive Features
- **Quick Suggestions**: Smart suggestion chips
- **Info Cards**: One-click access to common queries
- **Tax Calculator Widget**: Side-by-side calculation
- **Real-time Updates**: Live typing indicators
- **Session Management**: Persistent conversations

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI Model**: Google Gemini 1.5 Pro
- **API**: RESTful architecture
- **Validation**: Pydantic models
- **CORS**: Full cross-origin support

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Markdown**: React Markdown

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn
- Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

5. **Run the backend server**
```bash
python main.py
```

The backend will start at `http://localhost:8001`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The frontend will start at `http://localhost:3000`

## 🚀 Usage

1. **Open your browser** and navigate to `http://localhost:3000`

2. **Start chatting** with the AI tax advisor:
   - Click on info cards for quick queries
   - Type your questions in the input box
   - Use suggestion chips for common flows

3. **Tax Calculation**:
   - Click "Calculator" button in header
   - Enter your income and deductions
   - Get instant tax calculation

4. **Session Management**:
   - Conversations are preserved during session
   - Click "Clear" to reset and start fresh

## 📚 API Documentation

### Endpoints

#### Chat
```http
POST /api/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "string",
  "context": {}
}
```

#### Tax Calculation
```http
POST /api/calculate-tax
Content-Type: application/json

{
  "total_income": 1000000,
  "deductions": {
    "section_80c": 150000,
    "section_80d": 25000,
    ...
  },
  "regime": "new"
}
```

#### Regime Recommendation
```http
POST /api/recommend-regime
Content-Type: application/json

{
  "gross_income": 1000000,
  "deductions": {...}
}
```

#### ITR Form Recommendation
```http
POST /api/recommend-itr-form
Content-Type: application/json

{
  "profile": {...},
  "income": {...}
}
```

### Interactive API Docs
Visit `http://localhost:8001/docs` for Swagger UI documentation.

## 🎯 Key Capabilities

### Tax Knowledge Base
- ✅ Complete tax slabs for FY 2024-25
- ✅ All major deduction sections
- ✅ ITR form mappings
- ✅ Filing deadlines and penalties
- ✅ Compliance requirements
- ✅ Full forms and abbreviations

### Income Head Support
- **Salary**: Form 16, HRA, LTA, professional tax
- **Business**: Turnover, profit, presumptive taxation
- **Capital Gains**: STCG, LTCG, equity, property
- **House Property**: Rental income, home loan interest
- **Other Sources**: Interest, dividends, crypto

### Deduction Coverage
- Section 80C (₹1.5L): EPF, PPF, LIC, ELSS, NSC
- Section 80D: Health insurance (self + parents)
- Section 80E: Education loan interest
- Section 80G: Donations
- Section 24(b): Home loan interest
- Section 87A: Rebate for lower income

## 🔒 Security & Privacy

- **No Data Storage**: Conversations stored in memory only
- **Session-Based**: Each user gets unique session ID
- **API Security**: CORS protection enabled
- **Disclaimers**: Clear guidance that this is not official CA advice
- **Encryption Ready**: Environment for secure PAN/Aadhaar handling

## 📱 Screenshots

### Chat Interface
Beautiful glassmorphism design with smooth animations and intelligent suggestions.

### Tax Calculator
Side-by-side calculator with instant results and regime comparison.

### Info Cards
Quick access to common tax queries and information.

## 🎨 Design Philosophy

The UI follows a **modern, professional aesthetic** with:

- **Glassmorphism**: Frosted glass effects with backdrop blur
- **Gradient Accents**: Vibrant primary and accent colors
- **Smooth Animations**: Framer Motion for delightful interactions
- **Typography**: Custom font stack (Manrope, Sora, JetBrains Mono)
- **Responsive**: Mobile-first, works on all screen sizes
- **Accessibility**: High contrast, clear focus states

## 🚧 Production Deployment

### Backend

1. **Use production ASGI server**
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Add database** (PostgreSQL recommended)
```python
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@host:5432/db
```

3. **Enable caching** (Redis)
```python
# Add Redis for session storage
REDIS_URL=redis://localhost:6379/0
```

### Frontend

1. **Build for production**
```bash
npm run build
```

2. **Serve static files**
```bash
npm run preview
```

Or use Nginx/Apache to serve the `dist` folder.

### Environment Variables

**Production .env:**
```env
GEMINI_API_KEY=your_production_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
DEBUG=False
ALLOWED_ORIGINS=https://yourdomain.com
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This chatbot provides general tax guidance and information. It is **NOT** a substitute for professional Chartered Accountant advice. For complex tax situations, always consult with a qualified CA or tax professional.

## 💡 Future Enhancements

- [ ] File upload support (Form 16, 26AS, AIS)
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Voice input/output
- [ ] Tax saving recommendations with investment products
- [ ] Integration with Income Tax e-filing portal
- [ ] Historical ITR data storage
- [ ] Advanced analytics and insights
- [ ] Mobile apps (iOS/Android)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com

## 🙏 Acknowledgments

- Google Gemini for powerful AI capabilities
- FastAPI for excellent Python web framework
- React community for amazing frontend tools
- Tailwind CSS for utility-first styling
- Framer Motion for smooth animations

---

**Built with ❤️ for Indian Taxpayers**

*Version 1.0.0 - February 2025*
