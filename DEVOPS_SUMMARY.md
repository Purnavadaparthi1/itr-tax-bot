# ITR Tax Chatbot - DevOps Summary for Manager

**Project:** ITR Tax Filing & Advisory Chatbot  
**Status:** POC Ready for Deployment  
**Prepared:** February 20, 2026  

---

## 1. Technology Stack

- **Backend:** FastAPI (Python 3.13) + Uvicorn server on port 8001; async/await for non-blocking I/O
- **Frontend:** React 18+ with Vite bundler; communicates via REST API with Axios HTTP client
- **Dependencies:** google-generativeai (Gemini AI), pydantic (validation), python-dotenv (env vars)

---

## 2. Database Dependency

- **Current State:** In-memory Python dictionaries (conversations, user_profiles); NO external database
- **File-Based Logs:** Application logs (tax_bot.log) + JSON Lines extraction logs (extractions.log) in `/backend/logs/`
- **Recommended for Production:** PostgreSQL 14+ for persistent user sessions, profiles, and audit trail; replace in-memory storage

---

## 3. Data Stored, PII, and PCI

### Data Stored
- Chat conversation history (user messages + AI responses) per session
- User tax profiles (taxpayer category, income type, age, residential status)
- Extracted Form 16 data (employee name, PAN, salary components, TDS, employer info)
- Extraction logs with timestamps and confidence scores

### PII Present: **YES**
- **Fields:** PAN, Employee Name, Date of Birth, Salary Details, TDS, Employer Info
- **Protection:** ✓ PAN masked in logs (XXXXXX + last 4 chars); ✓ Raw text truncated (1000 chars max); ✓ 30-day retention policy enforced

### PCI Present: **NO**
- No payment card information processed; no billing/payment integration

---

## 4. Containerization

- **Docker Image:** python:3.13-slim base (~350-400 MB final); Dockerfile copies code, installs requirements, runs uvicorn
- **Docker Compose:** Single-service setup for local testing; binds `/backend/logs` volume for persistence; injects GEMINI_API_KEY env var
- **Production Ready:** Image can be pushed to AWS ECR, GCR, or Azure ACR for orchestration (ECS, K8s, App Service)

---

## 5. Third-Party Integrations

- **Google Gemini API:** Only external integration; used for document vision analysis (Form 16/Payslip OCR) and conversational AI
  - Model: gemini-2.5-flash (fast, cost-effective)
  - Rate Limit: Free tier 20 req/min; upgrade to paid for production
  - Estimated Cost: $20-50/month for light usage (2,400 vision calls/year, 60K text calls/year)

---

## 6. AI Integrations

- **Model:** Google Gemini 2.5-flash (configurable via MODEL_NAME env var)
- **Capabilities:** Vision API for PDF/image OCR (payslip, Form 16), Text API for tax advisory chatbot
- **Data Flow:** Documents sent as base64 to Gemini; PII sanitized before logging (PAN masked, raw text truncated to 1000 chars)

---

## 7. Infrastructure Requirements

| Layer | Minimum (POC) | Recommended (Prod) |
|-------|---------------|--------------------|
| **Compute** | 1 vCPU, 512 MB RAM | 2-4 vCPU, 2-4 GB RAM per instance (multi-instance behind ALB) |
| **Storage** | 10 GB disk | 50+ GB; S3 for log archival with lifecycle policy (30-day retention) |
| **Database** | In-memory (POC) | PostgreSQL 14+ (RDS) for session persistence |
| **Network** | 1 Mbps outbound | Outbound HTTPS to Google APIs; TLS termination (reverse proxy / ALB) |
| **Uptime SLA** | 95% | 99.5% business hours (multi-AZ with auto-failover) |

**Deployment Platforms:** AWS (ECS + ALB + RDS), Azure (App Service + SQL DB), GCP (Cloud Run + Cloud SQL), or Kubernetes (EKS/AKS/GKE)

---

## Key Deployment Checklist

- [ ] Repository pushed to private GitHub
- [ ] GEMINI_API_KEY stored in secrets manager (not hardcoded)
- [ ] Docker image tested locally (`docker-compose up`)
- [ ] PAN masking verified in logs
- [ ] Extraction log purge endpoint tested (DELETE `/api/extractions/purge?older_than_days=30`)
- [ ] CORS origins whitelisted for frontend domain
- [ ] TLS/HTTPS configured (reverse proxy)
- [ ] Monitoring/logging aggregation set up (CloudWatch / ELK)
- [ ] Auto-scaling policy configured (CPU/memory based)
- [ ] Database backups automated (if DB added)

---

**Prepared by:** Development Team  
**Next Steps:** Share with DevOps team for infrastructure provisioning and CI/CD pipeline setup
