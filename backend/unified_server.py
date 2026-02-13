"""
Unified Server - Runs both Backend and Frontend on Single Host
Port: 8001 (Backend API + Frontend served from same port)
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from pathlib import Path
import logging

# Load environment variables
load_dotenv()

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "tax_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ITR Tax Chatbot API",
    description="Complete Income Tax Return Filing & Advisory Chatbot for India",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise ValueError("GEMINI_API_KEY environment variable not set")

logger.info(f"Configuring Gemini API with API key: {GEMINI_API_KEY[:10]}...")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
logger.info(f"Initializing Gemini model: {MODEL_NAME}")
model = genai.GenerativeModel(MODEL_NAME)

# In-memory storage
conversations = {}
user_profiles = {}


# ==================== Pydantic Models ====================

class TaxpayerProfile(BaseModel):
    age: Optional[int] = None
    residential_status: Optional[str] = None
    taxpayer_category: Optional[str] = None
    income_type: Optional[List[str]] = []
    pan_number: Optional[str] = None
    financial_year: str = "2024-25"


class IncomeDetails(BaseModel):
    salary_income: Optional[float] = 0
    business_income: Optional[float] = 0
    capital_gains_short: Optional[float] = 0
    capital_gains_long: Optional[float] = 0
    rental_income: Optional[float] = 0
    other_income: Optional[float] = 0
    

class DeductionDetails(BaseModel):
    section_80c: Optional[float] = 0
    section_80d: Optional[float] = 0
    section_80e: Optional[float] = 0
    section_80g: Optional[float] = 0
    section_80tta: Optional[float] = 0
    home_loan_interest: Optional[float] = 0


class ChatMessage(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = []
    data_collected: Optional[Dict[str, Any]] = {}
    next_step: Optional[str] = None


class TaxCalculationRequest(BaseModel):
    total_income: float
    deductions: DeductionDetails
    regime: str = "new"


class TaxCalculationResponse(BaseModel):
    gross_income: float
    total_deductions: float
    taxable_income: float
    tax_amount: float
    cess: float
    total_tax: float
    regime_used: str
    breakdown: Dict[str, float]


class ITRFormRecommendation(BaseModel):
    recommended_form: str
    reason: str
    alternative_forms: List[str]


# ==================== Tax Calculation Engine ====================

class TaxCalculator:
    """Rule-based tax calculation engine for Indian Income Tax"""
    
    NEW_REGIME_SLABS = [
        (300000, 0),
        (300000, 0.05),
        (300000, 0.10),
        (300000, 0.15),
        (300000, 0.20),
        (float('inf'), 0.30)
    ]
    
    OLD_REGIME_SLABS = [
        (250000, 0),
        (250000, 0.05),
        (500000, 0.20),
        (float('inf'), 0.30)
    ]
    
    @staticmethod
    def calculate_tax(taxable_income: float, regime: str = "new") -> Dict[str, float]:
        slabs = TaxCalculator.NEW_REGIME_SLABS if regime == "new" else TaxCalculator.OLD_REGIME_SLABS
        
        tax = 0
        remaining = taxable_income
        breakdown = {}
        
        for i, (limit, rate) in enumerate(slabs):
            if remaining <= 0:
                break
            
            taxable_in_slab = min(remaining, limit)
            tax_in_slab = taxable_in_slab * rate
            tax += tax_in_slab
            
            breakdown[f"slab_{i+1}"] = tax_in_slab
            remaining -= taxable_in_slab
        
        rebate = 0
        if regime == "new" and taxable_income <= 700000:
            rebate = min(tax, 25000)
        elif regime == "old" and taxable_income <= 500000:
            rebate = min(tax, 12500)
        
        tax_after_rebate = max(0, tax - rebate)
        cess = tax_after_rebate * 0.04
        
        return {
            "base_tax": tax,
            "rebate_87a": rebate,
            "tax_after_rebate": tax_after_rebate,
            "cess": cess,
            "total_tax": tax_after_rebate + cess,
            "breakdown": breakdown
        }
    
    @staticmethod
    def recommend_regime(gross_income: float, deductions: DeductionDetails) -> Dict[str, Any]:
        old_taxable = gross_income - (
            deductions.section_80c + deductions.section_80d + 
            deductions.section_80e + deductions.section_80g + 
            deductions.section_80tta + deductions.home_loan_interest + 50000
        )
        
        new_taxable = gross_income - 50000
        
        old_tax = TaxCalculator.calculate_tax(max(0, old_taxable), "old")
        new_tax = TaxCalculator.calculate_tax(max(0, new_taxable), "new")
        
        recommendation = "new" if new_tax["total_tax"] <= old_tax["total_tax"] else "old"
        savings = abs(new_tax["total_tax"] - old_tax["total_tax"])
        
        return {
            "recommended_regime": recommendation,
            "old_regime_tax": old_tax["total_tax"],
            "new_regime_tax": new_tax["total_tax"],
            "savings": savings,
            "old_regime_details": old_tax,
            "new_regime_details": new_tax
        }


class ITRFormSelector:
    @staticmethod
    def select_form(profile: TaxpayerProfile, income: IncomeDetails) -> ITRFormRecommendation:
        if (income.salary_income > 0 and 
            income.business_income == 0 and 
            income.capital_gains_short == 0 and 
            income.capital_gains_long == 0 and
            income.rental_income == 0 and
            profile.taxpayer_category == "Individual"):
            
            return ITRFormRecommendation(
                recommended_form="ITR-1",
                reason="Suitable for salaried individuals with salary and interest income only",
                alternative_forms=[]
            )
        
        if (income.capital_gains_short > 0 or 
            income.capital_gains_long > 0 or
            income.rental_income > 0):
            
            return ITRFormRecommendation(
                recommended_form="ITR-2",
                reason="Required for capital gains, foreign income, or income from multiple properties",
                alternative_forms=[]
            )
        
        if income.business_income > 0:
            return ITRFormRecommendation(
                recommended_form="ITR-3",
                reason="Required for income from business or profession",
                alternative_forms=["ITR-4"]
            )
        
        return ITRFormRecommendation(
            recommended_form="ITR-1",
            reason="Based on provided information",
            alternative_forms=["ITR-2"]
        )


# ==================== Knowledge Base ====================

TAX_KNOWLEDGE_BASE = """
# Indian Income Tax Knowledge Base

## Tax Slabs FY 2024-25 (AY 2025-26)

### New Tax Regime:
- ₹0 to ₹3,00,000: Nil
- ₹3,00,001 to ₹6,00,000: 5%
- ₹6,00,001 to ₹9,00,000: 10%
- ₹9,00,001 to ₹12,00,000: 15%
- ₹12,00,001 to ₹15,00,000: 20%
- Above ₹15,00,000: 30%

### Old Tax Regime:
- ₹0 to ₹2,50,000: Nil
- ₹2,50,001 to ₹5,00,000: 5%
- ₹5,00,001 to ₹10,00,000: 20%
- Above ₹10,00,000: 30%

## Major Deductions & Full Forms - Complete Reference

[Complete tax knowledge base content here...]
"""


# ==================== AI Chatbot Logic ====================

class TaxChatbot:
    def __init__(self):
        self.system_prompt = f"""You are an expert Indian Chartered Accountant (CA) specializing in Income Tax Returns (ITR).

Your role:
- Guide users through ITR filing step-by-step
- Answer tax-related queries accurately
- Suggest deductions and tax-saving options
- Recommend appropriate tax regime
- Provide compliance guidance
- Explain full forms and abbreviations
- Maintain professional, polite tone

Knowledge Base:
{TAX_KNOWLEDGE_BASE}

Always include a disclaimer that this is guidance and users should verify with a professional CA for complex cases."""
    
    async def chat(self, session_id: str, user_message: str, context: Dict = None) -> ChatResponse:
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversations[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        context_str = ""
        if context:
            context_str = f"\n\nCurrent user context:\n{json.dumps(context, indent=2)}"
        
        chat_history = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversations[session_id][-10:]
        ])
        
        full_prompt = f"""{self.system_prompt}

{context_str}

Conversation so far:
{chat_history}

Provide a helpful, accurate response."""
        
        try:
            logger.info(f"Calling Gemini API with model: {MODEL_NAME} for session: {session_id}")
            logger.debug(f"Prompt length: {len(full_prompt)} characters")
            
            response = model.generate_content(full_prompt)
            ai_response = response.text
            
            logger.info(f"Successfully received response from Gemini API for session: {session_id}")
            
            conversations[session_id].append({
                "role": "assistant",
                "content": ai_response
            })
            
            suggestions = self._generate_suggestions(user_message, context)
            
            return ChatResponse(
                response=ai_response,
                suggestions=suggestions,
                data_collected=context or {},
                next_step=self._determine_next_step(context)
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in chat response for session {session_id}: {error_msg}", exc_info=True)
            logger.error(f"Model being used: {MODEL_NAME}")
            logger.error(f"API Key status: {'Set' if GEMINI_API_KEY else 'Not set'}")
            
            return ChatResponse(
                response=f"I apologize, but I encountered an error: {error_msg}. Please try again.",
                suggestions=["Start over", "Contact support"],
                data_collected=context or {}
            )
    
    def _generate_suggestions(self, user_message: str, context: Dict) -> List[str]:
        if not context or not context.get("taxpayer_profile"):
            return [
                "I'm a salaried employee",
                "I have business income",
                "I have capital gains",
                "Tell me about deductions"
            ]
        elif not context.get("income_details"):
            return [
                "Enter my salary details",
                "I have multiple income sources",
                "Calculate my tax",
                "Which ITR form should I use?"
            ]
        else:
            return [
                "Compare old vs new regime",
                "Show me deduction options",
                "Calculate final tax",
                "How to file ITR online?"
            ]
    
    def _determine_next_step(self, context: Dict) -> str:
        if not context or not context.get("taxpayer_profile"):
            return "profile_collection"
        elif not context.get("income_details"):
            return "income_collection"
        elif not context.get("deduction_details"):
            return "deduction_collection"
        else:
            return "tax_calculation"


chatbot = TaxChatbot()


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "ITR Tax Chatbot API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    try:
        response = await chatbot.chat(
            session_id=chat_request.session_id,
            user_message=chat_request.message,
            context=chat_request.context
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_tax(request: TaxCalculationRequest):
    try:
        total_deductions = (
            request.deductions.section_80c +
            request.deductions.section_80d +
            request.deductions.section_80e +
            request.deductions.section_80g +
            request.deductions.section_80tta +
            request.deductions.home_loan_interest
        )
        
        if request.regime == "old":
            total_deductions += 50000
        
        taxable_income = max(0, request.total_income - total_deductions - 50000)
        tax_result = TaxCalculator.calculate_tax(taxable_income, request.regime)
        
        return TaxCalculationResponse(
            gross_income=request.total_income,
            total_deductions=total_deductions,
            taxable_income=taxable_income,
            tax_amount=tax_result["tax_after_rebate"],
            cess=tax_result["cess"],
            total_tax=tax_result["total_tax"],
            regime_used=request.regime,
            breakdown=tax_result["breakdown"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend-regime")
async def recommend_regime(gross_income: float, deductions: DeductionDetails):
    try:
        recommendation = TaxCalculator.recommend_regime(gross_income, deductions)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend-itr-form", response_model=ITRFormRecommendation)
async def recommend_itr_form(profile: TaxpayerProfile, income: IncomeDetails):
    try:
        recommendation = ITRFormSelector.select_form(profile, income)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    if session_id not in conversations:
        return {"messages": []}
    return {"messages": conversations[session_id]}


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in conversations:
        del conversations[session_id]
    if session_id in user_profiles:
        del user_profiles[session_id]
    return {"status": "cleared"}


@app.get("/api/tax-info/slabs")
async def get_tax_slabs():
    return {
        "new_regime": TaxCalculator.NEW_REGIME_SLABS,
        "old_regime": TaxCalculator.OLD_REGIME_SLABS,
        "financial_year": "2024-25",
        "assessment_year": "2025-26"
    }


@app.get("/api/tax-info/deductions")
async def get_deductions_info():
    return {
        "section_80c": {
            "limit": 150000,
            "includes": ["EPF", "PPF", "LIC", "ELSS", "NSC", "Tuition fees", "Home loan principal"]
        },
        "section_80d": {
            "self_family": 25000,
            "parents_below_60": 25000,
            "parents_above_60": 50000
        },
        "section_80e": {
            "limit": "No limit",
            "description": "Interest on education loan"
        },
        "section_80g": {
            "description": "Donations to specified funds",
            "deduction": "50% or 100% based on organization"
        },
        "section_24b": {
            "limit": 200000,
            "description": "Home loan interest"
        }
    }


@app.get("/api/full-forms")
async def get_full_forms():
    return {
        "ITR": "Income Tax Return",
        "PAN": "Permanent Account Number",
        "AIS": "Annual Information Statement",
        "TIS": "Taxpayer Information Summary",
        "TDS": "Tax Deducted at Source",
        "AY": "Assessment Year",
        "FY": "Financial Year",
        "HRA": "House Rent Allowance",
        "LTA": "Leave Travel Allowance",
        "EPF": "Employee Provident Fund",
        "PPF": "Public Provident Fund",
        "ELSS": "Equity Linked Savings Scheme",
        "NSC": "National Savings Certificate",
        "NRI": "Non-Resident Indian",
        "RNOR": "Resident but Not Ordinarily Resident",
        "HUF": "Hindu Undivided Family",
        "LTCG": "Long Term Capital Gains",
        "STCG": "Short Term Capital Gains",
        "CBDT": "Central Board of Direct Taxes"
    }


# Mount static files (frontend) - Serve React app
# After building frontend with "npm run build", copy dist folder here
static_path = Path(__file__).parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
    print(f"✅ Serving frontend from: {static_path}")
else:
    print(f"⚠️  Frontend not built yet. Run 'npm run build' in frontend folder.")
    print(f"   Looking for: {static_path}")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ITR Tax Chatbot - Unified Server")
    print("📡 Backend API: http://localhost:8001/api")
    print("🌐 Frontend: http://localhost:8001")
    print("📚 API Docs: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
