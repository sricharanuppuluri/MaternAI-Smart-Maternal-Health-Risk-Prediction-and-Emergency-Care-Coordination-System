# MaternAI — Smart Maternal Health Risk Prediction & Care Coordination System

MaternAI is a multilingual maternal-health screening and care-coordination prototype designed to help mothers and ASHA/community health workers organize maternal health information, identify potentially higher-risk cases, support follow-up, and improve communication through multilingual voice and AI-assisted explanations.

> **Disclaimer**: MaternAI is a decision-support and workflow prototype, not a diagnostic or treatment system.

---

## Architecture

The system connects the end-to-end maternal care workflow:

```text
Frontend (React / TypeScript)
        ↓
Backend (FastAPI)
        ↓
Supabase PostgreSQL (Auth + RLS + Database)
```

With planned supporting intelligence layers:
- **Deterministic Safety Engine** (Emergency & concerning threshold escalation)
- **Machine Learning Risk Model** (Structured screening: Low / Medium / High)
- **Local LLM** (Natural language explanations and multilingual translation via Ollama)
- **AI Agent** (Authorized case query and follow-up tools)
- **AI4Bharat Voice** (IndicWhisper speech-to-text and Indic-TTS)

---

## Implementation Status (Developer 1 Phase 0)

- **Backend Foundation**: [IMPLEMENTED] Minimal FastAPI application with `/api/v1` versioned routing, root `/` health check, and modular layer structure.
- **Environment Configuration**: [IMPLEMENTED] Safe `.env.example` template with strict client/server secret boundary.
- **ML Contract**: [IMPLEMENTED] Documented `MLRiskInput` schema contract (`backend/app/schemas/ml.py`). Model training and selection are planned for Phase 5.
- **Safety Boundary**: [IMPLEMENTED] Safety status state definitions (`SafetyStatus`: `CLEAR`, `CONCERNING`, `EMERGENCY`). Clinical thresholds are planned for Phase 6.
- **Database Schema**: [PLANNED - Phase 2] Supabase migrations and RLS policies.
- **Authentication**: [PLANNED - Phase 3] Supabase Auth with server-side role validation.
- **Frontend**: [PLANNED - Developer 2 Phase 0/1] React + TypeScript client.

---

## Local Development Setup

### Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Node.js 18+ & npm
- Git

### 1. Environment Configuration

Copy the example environment configuration template:

```bash
cp .env.example .env
```

Ensure `.env` contains safe local development placeholders. **Never commit `.env` with actual production secrets.**

Key environment variables:
- **Frontend (Client-Safe / Public)**:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_API_BASE_URL`
- **Backend (Server-Only)**:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `MODEL_PATH`
  - `MODEL_VERSION`
  - `OLLAMA_BASE_URL`
  - `OLLAMA_MODEL`

### 2. Backend Setup & Startup

1. Set up a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment:
   - Windows PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```
3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Start the backend development server:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Verify health checks:
   - Root Health Check: [http://localhost:8000/](http://localhost:8000/)
   - API v1 Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - OpenAPI Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend Setup (Developer 2)

Frontend setup is owned by Developer 2 in their respective setup phase:
```bash
# When frontend is initialized by Developer 2:
cd frontend
npm install
npm run dev
```

### 4. Running Backend Tests

Run the test suite with pytest:

```bash
pytest backend/tests -v
```

---

## Repository Structure

```text
MaternAI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── api/             # API routing (v1)
│   │   ├── auth/            # Authentication & authorization checks
│   │   ├── db/              # Database connection
│   │   ├── schemas/         # Pydantic schemas (health, ML input)
│   │   ├── services/        # Business logic services
│   │   ├── safety/          # Safety rules & states
│   │   ├── ml/              # ML inference services
│   │   ├── llm/             # Local LLM integration
│   │   ├── agent/           # AI agent tooling
│   │   ├── voice/           # Voice pipeline integration
│   │   └── core/            # Configuration & constants
│   ├── tests/               # Test suites (unit, api, security, safety, integration)
│   ├── requirements.txt     # Python dependencies
│   └── pyproject.toml       # Python packaging configuration
├── ml/                      # ML datasets, models, and training docs
├── supabase/                # Supabase PostgreSQL migrations
├── docs/                    # Architecture and system documentation
├── .env.example             # Safe environment variable template
├── .gitignore               # Git ignore rules protecting secrets and artifacts
└── README.md                # Project documentation
```
