"""
ITR Tax Filing & Advisory Chatbot - Main Application
Complete CA-like tax advisory system for Indian Income Tax Returns
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import logging
import re
from pathlib import Path

# Load environment variables
load_dotenv()

# Setup logging
from datetime import datetime as _dt
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging early so we can use `logger` during startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "tax_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure extractions log file exists so reads won't fail
try:
    (log_dir / "extractions.log").touch(exist_ok=True)
except Exception:
    # If touch fails, keep going; _append_extraction_log will attempt again
    logger.exception("Could not create extractions.log at startup")


# Helper: append structured extraction logs to a file
def _append_extraction_log(record: dict):
    try:
        log_file = log_dir / "extractions.log"
        # ensure directory exists
        log_dir.mkdir(exist_ok=True)
        # ensure file exists
        try:
            log_file.touch(exist_ok=True)
        except Exception:
            logger.debug("Could not touch extractions.log; will attempt to open directly")
        # Sanitize record (mask PANs) before persisting/logging
        safe_record = _sanitize_record_for_logging(record)

        # append structured JSON line
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(safe_record, ensure_ascii=False) + "\n")

        # Also write a compact JSON line into the main service log for immediate visibility
        try:
            logger.info("Extraction record appended: %s", json.dumps(safe_record, ensure_ascii=False))
        except Exception:
            logger.info("Extraction record appended for file: %s", safe_record.get("filename"))
    except Exception:
        logger.exception("Failed to write extraction log")


def _mask_pan_value(val: str) -> str:
    """Mask PAN-like strings leaving only last 4 characters visible.
    PAN format (India) is 10 chars: 5 letters + 4 digits + 1 letter, but we'll mask any alphanumeric token of length >=6 containing digits.
    """
    if not isinstance(val, str):
        return val
    # Simple PAN regex: 5 letters, 4 digits, 1 letter (case-insensitive)
    pan_match = re.search(r"([A-Za-z]{5}[0-9]{4}[A-Za-z])", val)
    if pan_match:
        pan = pan_match.group(1)
        return val.replace(pan, 'X' * (len(pan) - 4) + pan[-4:])

    # fallback: mask tokens that look like sensitive identifiers (>=6 alnum chars with digits)
    token_match = re.search(r"([A-Za-z0-9]{6,})", val)
    if token_match and re.search(r"\d", token_match.group(1)):
        t = token_match.group(1)
        return val.replace(t, 'X' * (len(t) - 4) + t[-4:])

    return val


def _sanitize_obj(obj):
    """Recursively sanitize an object by masking PAN-like values when keys indicate PAN or values match patterns."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if v is None:
                out[k] = v
                continue
            key_lower = str(k).lower()
            if 'pan' in key_lower or key_lower in ('pan_number', 'pan_no'):
                # Mask if it's a PAN string
                out[k] = _mask_pan_value(str(v))
            else:
                out[k] = _sanitize_obj(v)
        return out
    elif isinstance(obj, list):
        return [_sanitize_obj(x) for x in obj]
    elif isinstance(obj, str):
        return _mask_pan_value(obj)
    else:
        return obj


def _sanitize_record_for_logging(record: dict) -> dict:
    """Return a sanitized copy of record suitable for logs (masks PANs and raw AI responses optionally).
    Keeps structure but masks PAN values and truncates long raw_text_preview for safety.
    """
    try:
        safe = dict(record)
        # Sanitize nested extracted_data and form16 payloads
        if 'extracted_data' in safe and isinstance(safe['extracted_data'], dict):
            safe['extracted_data'] = _sanitize_obj(safe['extracted_data'])
        if 'data_collected' in safe and isinstance(safe['data_collected'], dict):
            safe['data_collected'] = _sanitize_obj(safe['data_collected'])
        # Truncate raw text preview to 1000 chars to avoid sensitive leakage
        if 'raw_text_preview' in safe and isinstance(safe['raw_text_preview'], str):
            safe['raw_text_preview'] = safe['raw_text_preview'][:1000]
        return safe
    except Exception:
        logger.exception('Error sanitizing extraction record')
        return record

# Initialize FastAPI app
app = FastAPI(
    title="ITR Tax Chatbot API",
    description="Complete Income Tax Return Filing & Advisory Chatbot for India",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,

    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise ValueError("GEMINI_API_KEY environment variable not set")

logger.info("Configuring Gemini API (API key loaded from environment)")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
logger.info(f"Initializing Gemini model: {MODEL_NAME}")
model = genai.GenerativeModel(MODEL_NAME)

# Metro Cities List for HRA Exemption (50% of salary) vs Non-Metro (40% of salary)
METRO_CITIES = {
    "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Gandhinagar",
    "Gurugram", "Noida", "Gurgaon", "Thane", "Navi Mumbai", "Indore"
}

# In-memory storage (replace with database in production)
conversations = {}
user_profiles = {}


# ==================== Pydantic Models ====================

class TaxpayerProfile(BaseModel):
    age: Optional[int] = None
    residential_status: Optional[str] = None  # Resident, NRI, RNOR
    taxpayer_category: Optional[str] = None  # Individual, HUF, Firm, Company
    income_type: Optional[List[str]] = []  # Salaried, Freelancer, Business, etc.
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


class Form16Data(BaseModel):
    """Form 16 extracted data"""
    employee_name: Optional[str] = None
    pan: Optional[str] = None
    financial_year: Optional[str] = "2024-25"
    gross_salary: Optional[float] = 0
    basic_salary: Optional[float] = 0
    hra: Optional[float] = 0
    dearness_allowance: Optional[float] = 0
    other_allowances: Optional[float] = 0
    total_salary: Optional[float] = 0
    epf_contribution: Optional[float] = 0
    tds_deducted: Optional[float] = 0
    income_tax_deducted: Optional[float] = 0
    employer_name: Optional[str] = None
    employer_tan: Optional[str] = None
    form_16_part_a: Optional[Dict[str, Any]] = {}
    form_16_part_b: Optional[Dict[str, Any]] = {}
    extraction_confidence: Optional[float] = 0.0


class ChatMessage(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}
    form16_data: Optional[Form16Data] = None


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = []
    data_collected: Optional[Dict[str, Any]] = {}
    next_step: Optional[str] = None


class TaxCalculationRequest(BaseModel):
    total_income: float
    deductions: DeductionDetails
    regime: str = "new"  # old or new


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


class PayslipAnalysisResponse(BaseModel):
    """Response from payslip analysis"""
    success: bool
    message: str
    extracted_data: Optional[Dict[str, Any]] = {}
    confidence: Optional[float] = 0.0  # Confidence score 0-1
    data_collected: Optional[Dict[str, Any]] = {}


class Form16AnalysisResponse(BaseModel):
    """Response from Form 16 analysis"""
    success: bool
    message: str
    extracted_data: Optional[Form16Data] = None
    confidence: Optional[float] = 0.0  # Confidence score 0-1
    warnings: Optional[List[str]] = []


# ==================== Tax Calculation Engine ====================

class TaxCalculator:
    """Rule-based tax calculation engine for Indian Income Tax"""
    
    # Tax slabs for FY 2024-25
    NEW_REGIME_SLABS = [
        (300000, 0),      # 0-3L: 0%
        (300000, 0.05),   # 3-6L: 5%
        (300000, 0.10),   # 6-9L: 10%
        (300000, 0.15),   # 9-12L: 15%
        (300000, 0.20),   # 12-15L: 20%
        (float('inf'), 0.30)  # 15L+: 30%
    ]
    
    OLD_REGIME_SLABS = [
        (250000, 0),      # 0-2.5L: 0%
        (250000, 0.05),   # 2.5-5L: 5%
        (500000, 0.20),   # 5-10L: 20%
        (float('inf'), 0.30)  # 10L+: 30%
    ]
    
    @staticmethod
    def calculate_tax(taxable_income: float, regime: str = "new") -> Dict[str, float]:
        """Calculate tax based on regime"""
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
        
        # Apply rebate u/s 87A
        rebate = 0
        if regime == "new" and taxable_income <= 700000:
            rebate = min(tax, 25000)
        elif regime == "old" and taxable_income <= 500000:
            rebate = min(tax, 12500)
        
        tax_after_rebate = max(0, tax - rebate)
        
        # Health and Education Cess (4%)
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
        """Recommend best tax regime"""
        # Calculate under both regimes
        old_taxable = gross_income - (
            deductions.section_80c + deductions.section_80d + 
            deductions.section_80e + deductions.section_80g + 
            deductions.section_80tta + deductions.home_loan_interest +
            50000  # Standard deduction in old regime
        )
        
        new_taxable = gross_income - 50000  # Only standard deduction in new regime
        
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
    """Determine appropriate ITR form based on income sources"""
    
    @staticmethod
    def select_form(profile: TaxpayerProfile, income: IncomeDetails) -> ITRFormRecommendation:
        """Select appropriate ITR form"""
        
        # ITR-1 (Sahaj): Salaried + interest only
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
        
        # ITR-2: Capital gains or multiple house properties
        if (income.capital_gains_short > 0 or 
            income.capital_gains_long > 0 or
            income.rental_income > 0):
            
            return ITRFormRecommendation(
                recommended_form="ITR-2",
                reason="Required for capital gains, foreign income, or income from multiple properties",
                alternative_forms=[]
            )
        
        # ITR-3: Business/Professional income
        if income.business_income > 0:
            return ITRFormRecommendation(
                recommended_form="ITR-3",
                reason="Required for income from business or profession",
                alternative_forms=["ITR-4"]
            )
        
        # Default
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

## Major Deductions:

### Section 80C (Max ₹1,50,000):
- Employee Provident Fund (EPF)
- Public Provident Fund (PPF)
- Life Insurance Premium (LIC)
- Equity Linked Savings Scheme (ELSS)
- National Savings Certificate (NSC)
- Sukanya Samriddhi Yojana
- Home Loan Principal Repayment
- Tuition Fees (2 children)

### Section 80D (Health Insurance):
- Self, spouse, children: Up to ₹25,000
- Parents (below 60): Additional ₹25,000
- Parents (above 60): Additional ₹50,000

### Section 80E:
- Interest on education loan (no limit)

### Section 80G:
- Donations to specified funds/charities (50% or 100%)

### Section 24(b):
- Home loan interest: Up to ₹2,00,000

### Section 87A (Rebate):
- New Regime: ₹25,000 rebate if income ≤ ₹7,00,000
- Old Regime: ₹12,500 rebate if income ≤ ₹5,00,000

## ITR Forms:

### ITR-1 (Sahaj):
- For resident individuals
- Income from salary, one house property, other sources
- Total income up to ₹50 lakhs

### ITR-2:
- For individuals/HUFs not having business income
- Capital gains income
- Foreign assets/income
- Multiple house properties

### ITR-3:
- Income from business/profession
- Partners in firms

### ITR-4 (Sugam):
- Presumptive income from business/profession
- Turnover up to ₹2 crores

## Important Compliance:

### Filing Deadlines:
- Non-audit cases: July 31
- Audit cases: October 31

### Late Filing Penalties:
- Up to ₹5,000 if filed after due date
- ₹1,000 if income below ₹5 lakhs

### Mandatory Filing:
- Income exceeds basic exemption limit
- Total sales/turnover/gross receipts exceed prescribed limits
- Foreign assets or signing authority
- Claiming refund

## Full Forms & Abbreviations:

- **ITR**: Income Tax Return
- **PAN**: Permanent Account Number
- **AIS**: Annual Information Statement
- **TIS**: Taxpayer Information Summary
- **TDS**: Tax Deducted at Source
- **AY**: Assessment Year
- **FY**: Financial Year
- **HRA**: House Rent Allowance
- **LTA**: Leave Travel Allowance
- **EPF**: Employee Provident Fund
- **PPF**: Public Provident Fund
- **ELSS**: Equity Linked Savings Scheme
- **NSC**: National Savings Certificate
- **NRI**: Non-Resident Indian
- **RNOR**: Resident but Not Ordinarily Resident
- **HUF**: Hindu Undivided Family
- **LTCG**: Long Term Capital Gains
- **STCG**: Short Term Capital Gains
- **CBDT**: Central Board of Direct Taxes

## Common Questions:

**Q: Which regime should I choose?**
A: Compare both regimes. New regime has lower rates but no deductions. Old regime allows deductions but higher rates. Choose based on your deduction amounts.

**Q: What documents do I need?**
A: Form 16, Form 26AS, AIS/TIS, bank interest certificates, investment proofs, rent receipts, home loan certificates.

**Q: How to claim HRA exemption?**
A: Least of: (a) Actual HRA received, (b) Rent paid minus 10% of salary, (c) 50% of salary (metro cities like Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune) or 40% (non-metro cities). Hyderabad is a metro city, so 50% of salary applies.

**Q: What is standard deduction?**
A: ₹50,000 deduction available to salaried individuals in both regimes.
"""


# ==================== AI Chatbot Logic ====================

class TaxChatbot:
    """AI-powered tax chatbot using Gemini"""
    
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

Guidelines:
1. Always ask clarifying questions before giving advice
2. Collect information systematically (like a CA interview)
3. Provide specific, actionable guidance
4. Include disclaimers when needed
5. Explain complex terms in simple language
6. When asked about full forms, provide clear explanations
7. Be accurate with tax calculations and rules

Conversation Flow:
1. Identify taxpayer type and category
2. Collect income details by heads
3. Ask about deductions and investments
4. Recommend tax regime
5. Suggest ITR form
6. Provide filing guidance

IMPORTANT: Always include a disclaimer that this is guidance and users should verify with a professional CA for complex cases.

Respond conversationally but professionally."""
    
    async def chat(self, session_id: str, user_message: str, context: Dict = None, form16_data: Form16Data = None) -> ChatResponse:
        """Process chat message and return response"""
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        # Store Form 16 data in session if provided
        if form16_data and session_id not in user_profiles:
            user_profiles[session_id] = {}
        if form16_data:
            user_profiles[session_id]["form16_data"] = form16_data
        
        # Add user message to history
        conversations[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Build context-aware prompt with Form 16 information
        context_str = ""
        form16_context = ""
        
        if form16_data:
            form16_context = f"""

=== IMPORTANT: Form 16 Data Already Extracted ===
The user has uploaded Form 16. Use this information and DO NOT ask about these details:
- Employee Name: {form16_data.employee_name}
- PAN: {form16_data.pan}
- Gross Salary: ₹{form16_data.gross_salary:,.0f}
- Basic Salary: ₹{form16_data.basic_salary:,.0f}
- HRA: ₹{form16_data.hra:,.0f}
- Dearness Allowance: ₹{form16_data.dearness_allowance:,.0f}
- Other Allowances: ₹{form16_data.other_allowances:,.0f}
- Total Salary: ₹{form16_data.total_salary:,.0f}
- EPF Contribution: ₹{form16_data.epf_contribution:,.0f}
- TDS Deducted: ₹{form16_data.tds_deducted:,.0f}
- Income Tax Deducted: ₹{form16_data.income_tax_deducted:,.0f}
- Employer: {form16_data.employer_name}
- Financial Year: {form16_data.financial_year}
- Extraction Confidence: {form16_data.extraction_confidence:.0%}

Focus on:
1. Confirming if the extracted details are correct
2. Asking about OTHER income sources (if any)
3. Asking about deductions NOT visible in Form 16
4. Tax regime recommendation
5. Remaining questions for ITR filing
==================================================="""
        
        if context:
            context_str = f"\n\nCurrent user context:\n{json.dumps(context, indent=2)}"
        
        # Prepare messages for Gemini
        chat_history = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversations[session_id][-10:]  # Last 10 messages
        ])
        
        full_prompt = f"""{self.system_prompt}{form16_context}{context_str}

Conversation so far:
{chat_history}

Provide a helpful, accurate response. If you're collecting information, suggest the next logical question."""
        
        try:
            # Generate response using Gemini
            logger.info(f"Calling Gemini API with model: {MODEL_NAME} for session: {session_id}")
            logger.debug(f"Prompt length: {len(full_prompt)} characters")
            
            response = model.generate_content(full_prompt)
            ai_response = response.text
            
            logger.info(f"Successfully received response from Gemini API for session: {session_id}")
            
            # Add assistant response to history
            conversations[session_id].append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Generate suggestions based on conversation stage
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
        """Generate contextual suggestions"""
        suggestions = []
        
        if not context or not context.get("taxpayer_profile"):
            suggestions = [
                "I'm a salaried employee",
                "I have business income",
                "I have capital gains",
                "Tell me about deductions"
            ]
        elif not context.get("income_details"):
            suggestions = [
                "Enter my salary details",
                "I have multiple income sources",
                "Calculate my tax",
                "Which ITR form should I use?"
            ]
        else:
            suggestions = [
                "Compare old vs new regime",
                "Show me deduction options",
                "Calculate final tax",
                "How to file ITR online?"
            ]
        
        return suggestions
    
    def _determine_next_step(self, context: Dict) -> str:
        """Determine next logical step in conversation"""
        if not context:
            return "profile_collection"
        elif not context.get("taxpayer_profile"):
            return "profile_collection"
        elif not context.get("income_details"):
            return "income_collection"
        elif not context.get("deduction_details"):
            return "deduction_collection"
        else:
            return "tax_calculation"


# Initialize chatbot
chatbot = TaxChatbot()


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ITR Tax Chatbot API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint"""
    try:
        response = await chatbot.chat(
            session_id=chat_request.session_id,
            user_message=chat_request.message,
            context=chat_request.context,
            form16_data=chat_request.form16_data
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_tax(request: TaxCalculationRequest):
    """Calculate tax based on income and deductions"""
    try:
        # Calculate total deductions
        total_deductions = (
            request.deductions.section_80c +
            request.deductions.section_80d +
            request.deductions.section_80e +
            request.deductions.section_80g +
            request.deductions.section_80tta +
            request.deductions.home_loan_interest
        )
        
        # Add standard deduction
        if request.regime == "old":
            total_deductions += 50000
        
        # Calculate taxable income
        taxable_income = max(0, request.total_income - total_deductions - 50000)  # Standard deduction
        
        # Calculate tax
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
async def recommend_regime(
    gross_income: float,
    deductions: DeductionDetails
):
    """Recommend best tax regime"""
    try:
        recommendation = TaxCalculator.recommend_regime(gross_income, deductions)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend-itr-form", response_model=ITRFormRecommendation)
async def recommend_itr_form(
    profile: TaxpayerProfile,
    income: IncomeDetails
):
    """Recommend appropriate ITR form"""
    try:
        recommendation = ITRFormSelector.select_form(profile, income)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in conversations:
        return {"messages": []}
    return {"messages": conversations[session_id]}


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversations:
        del conversations[session_id]
    if session_id in user_profiles:
        del user_profiles[session_id]
    return {"status": "cleared"}


@app.get("/api/tax-info/slabs")
async def get_tax_slabs():
    """Get current tax slabs"""
    return {
        "new_regime": TaxCalculator.NEW_REGIME_SLABS,
        "old_regime": TaxCalculator.OLD_REGIME_SLABS,
        "financial_year": "2024-25",
        "assessment_year": "2025-26"
    }


@app.get("/api/tax-info/deductions")
async def get_deductions_info():
    """Get information about tax deductions"""
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


@app.get("/api/extractions")
async def get_extractions(tail: int = 50):
    """Return last N extraction records from logs/extractions.log"""
    try:
        log_file = log_dir / "extractions.log"
        if not log_file.exists():
            return []

        results = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except Exception:
                    # skip malformed lines
                    continue

        return results[-tail:]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/extractions/purge")
async def purge_extractions(older_than_days: int = 30):
    """Purge extraction records older than `older_than_days` from extractions.log.
    WARNING: This rewrites the log file and cannot be undone. Requires caution in production.
    """
    try:
        log_file = log_dir / "extractions.log"
        if not log_file.exists():
            return {"purged": 0, "message": "No extraction log present"}

        cutoff = _dt.utcnow() - timedelta(days=older_than_days)
        kept = []
        purged_count = 0
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts = obj.get("timestamp")
                    if ts:
                        try:
                            obj_dt = datetime.fromisoformat(ts)
                        except Exception:
                            obj_dt = None
                    else:
                        obj_dt = None

                    if obj_dt and obj_dt < cutoff:
                        purged_count += 1
                        continue
                    kept.append(line)
                except Exception:
                    # Keep malformed lines to avoid accidental loss
                    kept.append(line)

        # Rewrite file with kept lines
        with open(log_file, "w", encoding="utf-8") as f:
            for l in kept:
                f.write(l + "\n")

        return {"purged": purged_count, "kept": len(kept)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/full-forms")
async def get_full_forms():
    """Get full forms of tax abbreviations"""
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


@app.post("/api/upload-payslip", response_model=PayslipAnalysisResponse)
async def upload_payslip(file: UploadFile = File(...)):
    """
    Upload and analyze payslip (PDF/Image)
    Extracts income components and tax details
    """
    try:
        if not file.filename:
            return PayslipAnalysisResponse(
                success=False,
                message="No file provided"
            )
        
        # Log file upload
        logger.info(f"Payslip upload received: {file.filename} (Size: {file.size} bytes)")
        
        # Read file content
        content = await file.read()
        
        # Check file type
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in ['pdf', 'png', 'jpg', 'jpeg']:
            return PayslipAnalysisResponse(
                success=False,
                message=f"Unsupported file format. Please upload PDF or image (PNG/JPG)"
            )
        
        try:
            # Convert file to base64 for Gemini Vision API
            import base64
            file_base64 = base64.b64encode(content).decode('utf-8')
            
            # Prepare the analysis prompt
            analysis_prompt = """
            Please analyze this payslip and extract the following information:
            1. Salary components:
               - Basic salary
               - House Rent Allowance (HRA)
               - Dearness Allowance (DA)
               - Conveyance allowance
               - Medical allowance
               - Other allowances
            2. Deductions:
               - Employee Provident Fund (EPF)
               - Income Tax / TDS
               - Other deductions
            3. Employee details:
               - Employee name
               - Designation
               - Department
               - PAN (if visible)
            4. Tax information:
               - Total TDS deducted
               - Tax regime (if mentioned)
            5. Pay period and payment details
            
            Please provide the response in JSON format with keys matching the above structure.
            If any field is not visible, mark it as null.
            Include a confidence score (0-1) for the accuracy of extraction.
            """
            
            # Use Gemini Vision API to analyze payslip
            import base64
            
            # Determine MIME type
            mime_type = f"image/{file_ext}" if file_ext in ['png', 'jpg', 'jpeg'] else "application/pdf"
            
            # Create the vision request
            vision_model = genai.GenerativeModel('gemini-2.5-flash')
            
            file_part = {
                'mime_type': mime_type,
                'data': file_base64
            }
            
            response = vision_model.generate_content([analysis_prompt, file_part])
            
            # Parse the response
            logger.info(f"Gemini vision analysis completed for {file.filename}")
            
            # Try to extract JSON from response
            response_text = response.text
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            extracted_data = {}
            confidence = 0.8  # Default confidence
            
            if json_match:
                try:
                    extracted_data = json.loads(json_match.group())
                    confidence = extracted_data.pop('confidence', 0.8)
                except json.JSONDecodeError:
                    extracted_data = {"raw_text": response_text}
                    confidence = 0.5
            else:
                extracted_data = {"raw_text": response_text}
                confidence = 0.5
            
            # Extract income components into structured format
                # Helper: robust number parsing and flexible key matching
                def _parse_number(val):
                    if val is None:
                        return 0.0
                    if isinstance(val, (int, float)):
                        return float(val)
                    s = str(val)
                    # remove common currency symbols and whitespace
                    s = re.sub(r'[₹$,\s]', '', s)
                    # handle parentheses as negative
                    s = s.replace('(', '-').replace(')', '')
                    try:
                        return float(s)
                    except Exception:
                        m = re.search(r'-?\d[\d,\.]*', str(val))
                        if m:
                            try:
                                return float(m.group().replace(',', ''))
                            except Exception:
                                return 0.0
                        return 0.0

                def _find_amount(data, candidates):
                    # exact key match (case-insensitive)
                    for cand in candidates:
                        for k in data.keys():
                            if k and k.lower() == cand.lower():
                                return _parse_number(data.get(k))
                    # nested dicts
                    for v in data.values():
                        if isinstance(v, dict):
                            for cand in candidates:
                                for k2 in v.keys():
                                    if k2 and k2.lower() == cand.lower():
                                        return _parse_number(v.get(k2))
                    # substring match
                    for k in data.keys():
                        if not isinstance(k, str):
                            continue
                        for cand in candidates:
                            if cand.lower() in k.lower():
                                return _parse_number(data.get(k))
                    # try raw text
                    raw = data.get('raw_text') or data.get('text') or ''
                    if raw:
                        pattern = r'(' + '|'.join([re.escape(c) for c in candidates]) + r')[^\d\n\r]{0,30}([₹₹]?\s*[\d,]+\.?\d*)'
                        m = re.search(pattern, raw, re.IGNORECASE)
                        if m:
                            return _parse_number(m.group(2))
                    return 0.0

                # Extract income components into structured format (robust)
                data_collected = {
                    "salary_income": _find_amount(extracted_data, [
                        "basic_salary", "basic", "basic pay", "basic salary", "basic_salary"
                    ]),
                    "hra": _find_amount(extracted_data, [
                        "hra", "house rent allowance", "house rent", "h r a"
                    ]),
                    "conveyance": _find_amount(extracted_data, [
                        "conveyance", "conveyance allowance", "conveyance allowance"
                    ]),
                    "medical_allowance": _find_amount(extracted_data, [
                        "medical", "medical allowance", "med allowance"
                    ]),
                    "education_allowance": _find_amount(extracted_data, [
                        "education", "education allowance", "edu allowance"
                    ]),
                    "special_allowance": _find_amount(extracted_data, [
                        "special", "special allowance", "special al"
                    ]),
                    "net_pay": _find_amount(extracted_data, [
                        "net_pay", "net pay", "net salary", "take home", "take_home", "take-home"
                    ]),
                    "allowances": extracted_data.get("allowances", {}),
                    "tax_deducted": _find_amount(extracted_data, [
                        "tax_deducted", "tds", "total tax deducted", "income tax deducted"
                    ]),
                    "epf": _find_amount(extracted_data, [
                        "epf", "employee provident fund", "epf contribution", "pf", "provident fund"
                    ]),
                    "professional_tax": _find_amount(extracted_data, ["professional_tax", "pt", "professional tax"]),
                    "employee_name": extracted_data.get("employee_name", extracted_data.get("Employee Name", "")),
                    "pay_period": extracted_data.get("pay_period", extracted_data.get("pay_period", ""))
                }

                # Fallback: if basic salary not found, use gross or net pay as salary_income
                if data_collected["salary_income"] == 0:
                    fallback_salary = _find_amount(extracted_data, ["gross_salary", "gross pay", "gross", "total earnings"]) or data_collected.get("net_pay", 0)
                    if fallback_salary and fallback_salary > 0:
                        data_collected["salary_income"] = fallback_salary

                # Log the raw extraction and final values for debugging
                try:
                    logger.info(f"Payslip extracted_data keys: {list(extracted_data.keys())}")
                    raw_preview = (extracted_data.get('raw_text') or '')[:1200]
                    if raw_preview:
                        logger.debug(f"Payslip raw_text preview: {raw_preview}")
                    logger.info(f"Payslip final data_collected: {data_collected}")
                except Exception:
                    logger.exception("Error logging payslip extraction details")
            
            logger.info(f"Payslip analysis successful. Confidence: {confidence}")
            
            # Persist extraction log
            try:
                record = {
                    "timestamp": _dt.utcnow().isoformat(),
                    "type": "payslip",
                    "filename": file.filename,
                    "extracted_data_keys": list(extracted_data.keys()),
                    "extracted_data": extracted_data,
                    "data_collected": data_collected,
                    "confidence": confidence,
                    "message": f"Payslip analyzed successfully. Confidence: {confidence:.2f}",
                    "raw_text_preview": (response_text or '')[:2000]
                }
                _append_extraction_log(record)
            except Exception:
                logger.exception("Failed to persist payslip extraction log")

            return PayslipAnalysisResponse(
                success=True,
                message=f"Payslip analyzed successfully. Confidence: {confidence:.0%}",
                extracted_data=extracted_data,
                confidence=confidence,
                data_collected=data_collected
            )
            
        except Exception as e:
            logger.error(f"Error analyzing payslip with Gemini: {str(e)}", exc_info=True)
            return PayslipAnalysisResponse(
                success=False,
                message=f"Could not analyze payslip: {str(e)}. Please enter details manually."
            )
        
    except Exception as e:
        logger.error(f"Error in payslip upload endpoint: {str(e)}", exc_info=True)
        return PayslipAnalysisResponse(
            success=False,
            message=f"Error processing file: {str(e)}"
        )


@app.post("/api/upload-form16", response_model=Form16AnalysisResponse)
async def upload_form16(file: UploadFile = File(...)):
    """
    Upload and analyze Form 16 (PDF/Image)
    Extracts all salary and tax information from Form 16
    Form 16 is critical for salaried individuals as it contains:
    - Complete salary breakdown (basic, HRA, DA, allowances)
    - TDS deducted details
    - Employer information
    - PAN and other personal details
    """
    try:
        if not file.filename:
            return Form16AnalysisResponse(
                success=False,
                message="No file provided"
            )
        
        # Log file upload
        logger.info(f"Form 16 upload received: {file.filename} (Size: {file.size} bytes)")
        
        # Read file content
        content = await file.read()
        
        # Check file type
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in ['pdf', 'png', 'jpg', 'jpeg']:
            return Form16AnalysisResponse(
                success=False,
                message=f"Unsupported file format. Please upload PDF or image (PNG/JPG)"
            )
        
        try:
            # Convert file to base64 for Gemini Vision API
            import base64
            file_base64 = base64.b64encode(content).decode('utf-8')
            
            # Comprehensive Form 16 analysis prompt
            analysis_prompt = """
            Please carefully analyze this Form 16 document and extract ALL the following information:
            
            SECTION A - EMPLOYEE DETAILS:
            1. Full Name of Employee
            2. PAN (Permanent Account Number)
            3. Date of Birth
            4. Financial Year (e.g., 2024-25)
            5. Assessment Year
            
            SECTION B - EMPLOYER DETAILS:
            1. Employer Name
            2. TAN (Tax Account Number)
            3. Address
            
            SECTION C - SALARY DETAILS (Annual):
            1. Basic Salary
            2. House Rent Allowance (HRA)
            3. Dearness Allowance (DA)
            4. Conveyance Allowance
            5. Medical Allowance
            6. Bonus
            7. Other Allowances/Perquisites
            8. Gross Salary (Total of all above)
            
            SECTION D - DEDUCTIONS:
            1. Employee Provident Fund (EPF) / Contrib to Superannuation
            2. Professional Tax
            3. Income Tax
            4. Other Deductions
            5. Total Deductions
            
            SECTION E - TAX INFORMATION:
            1. Total Income
            2. Total Tax Deducted
            3. Relief under Section 89(1)
            4. Net Tax Payable
            5. Refund Due (if any)
            
            SECTION F - CERTIFICATION:
            1. Date of Issuance
            2. Employer's Signature/authorized person
            
            Additional Notes:
            - If any field is not visible in the document, explicitly state it as "Not visible"
            - Provide only ANNUAL amounts for salary components
            - Extract EXACT amounts as shown in the form
            - If Form 16 Part B is visible, also extract deductions claimed (Section 80C, 80D, etc.)
            
            Respond ONLY in valid JSON format with these exact keys:
            {
                "employee_name": "value",
                "pan": "value",
                "date_of_birth": "value",
                "financial_year": "value",
                "assessment_year": "value",
                "employer_name": "value",
                "employer_tan": "value",
                "basic_salary": numeric_value,
                "hra": numeric_value,
                "dearness_allowance": numeric_value,
                "conveyance_allowance": numeric_value,
                "medical_allowance": numeric_value,
                "bonus": numeric_value,
                "other_allowances": numeric_value,
                "gross_salary": numeric_value,
                "epf_contribution": numeric_value,
                "professional_tax": numeric_value,
                "income_tax_deducted": numeric_value,
                "other_deductions": numeric_value,
                "total_deductions": numeric_value,
                "total_income": numeric_value,
                "total_tax_deducted": numeric_value,
                "relief_89_1": numeric_value,
                "net_tax_payable": numeric_value,
                "refund_due": numeric_value,
                "form16_date": "value",
                "part_b_deductions": {
                    "section_80c": numeric_value,
                    "section_80d": numeric_value,
                    "section_80e": numeric_value,
                    "section_80g": numeric_value,
                    "other_deductions": numeric_value
                },
                "confidence_score": 0.0 to 1.0,
                "notes": "any important notes or missing fields"
            }
            """
            
            # Determine MIME type
            mime_type = f"image/{file_ext}" if file_ext in ['png', 'jpg', 'jpeg'] else "application/pdf"
            
            # Use Gemini Vision API to analyze Form 16
            vision_model = genai.GenerativeModel('gemini-2.5-flash')
            
            file_part = {
                'mime_type': mime_type,
                'data': file_base64
            }
            
            response = vision_model.generate_content([analysis_prompt, file_part])
            
            # Parse the response
            logger.info(f"Gemini vision analysis completed for Form 16: {file.filename}")
            
            # Try to extract JSON from response
            response_text = response.text
            
            # Parse JSON from response with better error handling
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text, re.DOTALL)
            
            extracted_form16 = None
            confidence = 0.5
            warnings = []
            
            if json_match:
                try:
                    json_data = json.loads(json_match.group())
                    confidence = json_data.pop('confidence_score', 0.7)
                    notes = json_data.pop('notes', "")
                    
                    # Create Form16Data object
                    extracted_form16 = Form16Data(
                        employee_name=json_data.get("employee_name"),
                        pan=json_data.get("pan"),
                        financial_year=json_data.get("financial_year", "2024-25"),
                        gross_salary=float(json_data.get("gross_salary", 0)),
                        basic_salary=float(json_data.get("basic_salary", 0)),
                        hra=float(json_data.get("hra", 0)),
                        dearness_allowance=float(json_data.get("dearness_allowance", 0)),
                        other_allowances=float(json_data.get("other_allowances", 0)),
                        total_salary=float(json_data.get("gross_salary", 0)),
                        epf_contribution=float(json_data.get("epf_contribution", 0)),
                        tds_deducted=float(json_data.get("total_tax_deducted", 0)),
                        income_tax_deducted=float(json_data.get("income_tax_deducted", 0)),
                        employer_name=json_data.get("employer_name"),
                        employer_tan=json_data.get("employer_tan"),
                        form_16_part_a=json_data,
                        form_16_part_b=json_data.get("part_b_deductions", {}),
                        extraction_confidence=confidence
                    )
                    
                    # Add warnings if confidence is low or important fields missing
                    if confidence < 0.7:
                        warnings.append(f"Low confidence extraction ({confidence:.0%}). Please verify all details.")
                    if not extracted_form16.pan:
                        warnings.append("PAN not clearly extracted. Please verify.")
                    if notes:
                        warnings.append(f"Notes from analysis: {notes}")
                    
                    logger.info(f"Form 16 analysis successful. Confidence: {confidence:.0%}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {str(e)}")
                    warnings.append("Could not parse extracted data as JSON")
                    confidence = 0.3
            else:
                warnings.append("Could not extract structured data from Form 16")
                confidence = 0.2
            
            if not extracted_form16:
                return Form16AnalysisResponse(
                    success=False,
                    message="Could not extract Form 16 data. Please ensure the image/PDF is clear and contains the complete form.",
                    confidence=confidence,
                    warnings=warnings
                )

            # Persist extraction log for Form 16
            try:
                record = {
                    "timestamp": _dt.utcnow().isoformat(),
                    "type": "form16",
                    "filename": file.filename,
                    "extracted_data": extracted_form16.dict() if hasattr(extracted_form16, 'dict') else {},
                    "confidence": confidence,
                    "warnings": warnings,
                }
                _append_extraction_log(record)
            except Exception:
                logger.exception("Failed to persist Form 16 extraction log")

            return Form16AnalysisResponse(
                success=True,
                message=f"Form 16 analyzed successfully. Confidence: {confidence:.0%}" + 
                        (f" ({len(warnings)} warnings)" if warnings else ""),
                extracted_data=extracted_form16,
                confidence=confidence,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error analyzing Form 16 with Gemini: {str(e)}", exc_info=True)
            return Form16AnalysisResponse(
                success=False,
                message=f"Could not analyze Form 16: {str(e)}. Please try again.",
                warnings=[str(e)]
            )
        
    except Exception as e:
        logger.error(f"Error in Form 16 upload endpoint: {str(e)}", exc_info=True)
        return Form16AnalysisResponse(
            success=False,
            message=f"Error processing file: {str(e)}",
            warnings=[str(e)]
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
