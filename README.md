# AI-Powered CRM System

An intelligent CRM (Customer Relationship Management) system powered by AI agents built with **LangGraph**, **FastAPI** backend, **React** frontend, and **PostgreSQL** database. Pharmaceutical field representatives can log HCP interactions using natural language, and AI extracts structured data, generates insights, and suggests follow-up actions.

**Key Features:**
- 📝 Natural language interaction logging with LLM-powered extraction
- 🤖 LangGraph agent with 5 specialized tools
- 💬 Dual-mode UI: Structured form + AI chat
- 📊 Sentiment analysis & follow-up suggestions
- 🗄️ PostgreSQL database with full audit trails
- ⚡ Real-time Redux state management

---

## 🏗️ Architecture

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                   │
├─────────────────────────────────┬─────────────────────────┤
│                                 │                         │
│  LOG INTERACTION FORM            │   AI CHAT PANEL         │
│  (Structured Fields)             │   (Natural Language)    │
│  - HCP Name (search)             │   - Type interaction    │
│  - Date/Time                     │   - Click "Log"         │
│  - Attendance, Topics            │   - View extracted data │
│  - Materials, Samples            │   - See suggestions     │
│  - Sentiment (radio)             │                         │
│  - Outcomes, Follow-ups          │                         │
│                                 │                         │
│  Redux: interaction.*            │   Redux: chat.*         │
│  (Form State Tree)               │   (Chat State Tree)     │
└─────────────────────────────────┴─────────────────────────┘
                    ↓ (Independent HTTP)
        POST /api/interactions/log
        PUT  /api/interactions/{id}
        GET  /api/interactions/hcp/{hcp_id}
        POST /api/interactions/{id}/suggest-followup
        GET  /api/hcps/search?q=name
        POST /api/chat
                    ↓
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (Python 3.11+)                    │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LangGraph Agent (Stateful AI Orchestration)       │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ Agent Node (LLM Decision-Maker)              │  │   │
│  │  │ Model: Groq gemma2-9b-it (primary)          │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │           ↓                                         │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │ Tool Selection (ReAct Pattern)             │    │   │
│  │  │ ┌─────────────────────────────────────┐    │    │   │
│  │  │ │ TOOL 1: log_interaction             │    │    │   │
│  │  │ │ → Extract HCP, topics, sentiment    │    │    │   │
│  │  │ │ → Save to database                  │    │    │   │
│  │  │ │ ┌───────────────────────────────┐ │    │    │   │
│  │  │ │ │ TOOL 2: edit_interaction         │ │    │    │   │
│  │  │ │ │ → LLM interprets edit request   │ │    │    │   │
│  │  │ │ │ → Update DB fields             │ │    │    │   │
│  │  │ │ │ ┌─────────────────────────────┐ │ │    │    │   │
│  │  │ │ │ │ TOOL 3: get_hcp_history    │ │ │    │    │   │
│  │  │ │ │ │ → Retrieve last N records   │ │ │    │    │   │
│  │  │ │ │ │ → LLM summarize trends     │ │ │    │    │   │
│  │  │ │ │ │ ┌─────────────────────────┐ │ │ │    │    │   │
│  │  │ │ │ │ │ TOOL 4: suggest_follow_up│ │ │ │    │    │   │
│  │  │ │ │ │ │ → Generate 2-3 suggestions│ │ │ │    │    │   │
│  │  │ │ │ │ │ → Save to DB            │ │ │ │    │    │   │
│  │  │ │ │ │ │ ┌───────────────────────┐ │ │ │ │    │    │   │
│  │  │ │ │ │ │ │ TOOL 5: search_hcp    │ │ │ │ │    │    │   │
│  │  │ │ │ │ │ │ (Utility - optional)  │ │ │ │ │    │    │   │
│  │  │ │ │ │ │ └───────────────────────┘ │ │ │ │    │    │   │
│  │  │ │ │ │ └─────────────────────────┘ │ │ │ │    │    │   │
│  │  │ │ │ └─────────────────────────────┘ │ │ │ │    │    │   │
│  │  │ │ └─────────────────────────────────┘ │ │ │    │    │   │
│  │  │ └─────────────────────────────────────┘ │ │    │    │   │
│  │  │ Fallback LLM: Groq llama-3.3-70b      │ │    │    │   │
│  │  └──────────────────────────────────────────┘    │    │   │
│  └─────────────────────────────────────────────────┘   │   │
│                                                         │   │
│  Pydantic Schemas | SQLAlchemy ORM | Error Handling    │   │
└─────────────────────────────────────────────────────────┘
                    ↓ (SQL/Transactions)
┌─────────────────────────────────────────────────────────────┐
│           PostgreSQL Database (Relational)                  │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  Tables:                                                    │
│  ├─ hcps                        (HCP profiles)              │
│  ├─ interactions                (Logged interactions)       │
│  ├─ materials_shared            (Materials given)           │
│  ├─ samples_distributed         (Samples given)            │
│  └─ follow_up_suggestions       (AI-generated actions)     │
│                                                             │
│  Features: UUIDs, timestamps, foreign keys, indices        │
│  Audit trail: created_at, updated_at on all records       │
└─────────────────────────────────────────────────────────────┘
```

### Component Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend UI** | React 18 + Redux Toolkit + Vite | Dual form + chat interface with shared state |
| **API Layer** | FastAPI + Pydantic | RESTful endpoints with validation |
| **AI Agent** | LangGraph + LangChain | Multi-step stateful agent with tool routing |
| **LLM** | Groq API (gemma2-9b-it, llama-3.3-70b-versatile) | Fast inference for entity extraction & analysis |
| **Database** | PostgreSQL + SQLAlchemy + Alembic | Persistent relational storage |
| **Styling** | CSS + Google Inter Font | Dark theme UI |

---

## 🚀 Setup

### Prerequisites
- **Node.js** >= 18.x
- **Python** >= 3.11
- **PostgreSQL** >= 15
- **Groq API Key** — [Get one here](https://console.groq.com/)

### 1. Clone the Repository
```bash
git clone <repo-url>
cd crm
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your API URL
```

### 4. Database Setup
```bash
# Create a PostgreSQL database
createdb crm_db

# Run migrations (once implemented)
# alembic upgrade head
```

---

## ▶️ How to Run

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
API will be available at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`

### Start Frontend
```bash
cd frontend
npm run dev
```
Frontend will be available at: `http://localhost:5173`

---

## 📝 Environment Variables

### Backend `.backend/.env`

```bash
# ═══════════════════════════════════════════════════════════════
# Database Configuration
# ═══════════════════════════════════════════════════════════════

# PostgreSQL connection URL
# Format: postgresql://user:password@host:port/database
# Example: postgresql://postgres:mypassword@localhost:5432/crm_db
DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_db

# ═══════════════════════════════════════════════════════════════
# Groq API Configuration (LLM Inference)
# ═══════════════════════════════════════════════════════════════

# Groq API Key — Get from https://console.groq.com
# Required for all LLM operations
GROQ_API_KEY=gsk_your_groq_api_key_here

# ═══════════════════════════════════════════════════════════════
# LLM Model Selection
# ═══════════════════════════════════════════════════════════════

# Primary model for fast, lightweight tasks (extraction, routing)
# Options: gemma2-9b-it (recommended), llama-3.3-70b-versatile
LLM_MODEL=gemma2-9b-it

# ═══════════════════════════════════════════════════════════════
# Application Settings
# ═══════════════════════════════════════════════════════════════

# Environment mode: development, staging, production
ENVIRONMENT=development

# CORS allowed origins (comma-separated)
# For local development: http://localhost:5173,http://localhost:3000
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Application logging level
LOG_LEVEL=INFO
```

### Frontend `frontend/.env`

```bash
# ═══════════════════════════════════════════════════════════════
# API Configuration
# ═══════════════════════════════════════════════════════════════

# Backend API base URL
# Development: http://localhost:8000/api
# Production: https://api.yourdomain.com/api
VITE_API_BASE_URL=http://localhost:8000/api
```

**Important Notes:**
- ⚠️ **Never commit `.env` files to version control** — use `.env.example` only
- 🔐 **Groq API Key** is sensitive — rotate regularly or use environment secrets in production
- 🌐 **CORS Origins** must match your frontend URL exactly
- 📊 **DATABASE_URL** determines where interaction records are stored

---

## 🚀 Quick Start

### Prerequisites

Ensure you have installed:
- **Node.js** >= 18.x ([Download](https://nodejs.org/))
- **Python** >= 3.11 ([Download](https://www.python.org/))
- **PostgreSQL** >= 15 ([Download](https://www.postgresql.org/))
- **Git** ([Download](https://git-scm.com/))
- **Groq API Key** ([Get here](https://console.groq.com/))

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/crm.git
cd crm
```

### 2️⃣ Backend Setup

**Create Python virtual environment:**
```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure environment:**
```bash
cp .env.example .env
# Edit .env and add:
#   - DATABASE_URL (PostgreSQL connection)
#   - GROQ_API_KEY (from https://console.groq.com)
```

**Create database:**
```bash
# Using psql command line
createdb crm_db

# Or connect to your PostgreSQL server and run:
# CREATE DATABASE crm_db;
```

### 3️⃣ Frontend Setup

**Install dependencies:**
```bash
cd frontend
npm install
```

**Configure environment:**
```bash
cp .env.example .env
# Edit .env with your backend URL
# VITE_API_BASE_URL=http://localhost:8000/api
```

### 4️⃣ Start Services

**In one terminal — Start Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at:
- 🌐 **API**: `http://localhost:8000`
- 📚 **Swagger Docs**: `http://localhost:8000/docs`
- 🔄 **ReDoc**: `http://localhost:8000/redoc`

**In another terminal — Start Frontend:**
```bash
cd frontend
npm run dev
```

The frontend will be available at:
- 🎨 **UI**: `http://localhost:5173`

### 5️⃣ Test the System

Refer to [`TESTING.md`](./TESTING.md) for comprehensive integration tests including:
- ✅ All 5 LangGraph tools via cURL
- ✅ Form submission flow
- ✅ Chat submission flow
- ✅ Database record verification

---

## 📖 Usage

### Log Interaction via Form (Left Panel)

1. Access `http://localhost:5173` in your browser
2. Fill the **Log Interaction Form** (left panel):
   - 🔍 **HCP Name**: Search and select from database
   - 📅 **Date & Time**: Interaction date/time
   - 👥 **Attendees**: Add multiple attendees
   - 📝 **Topics Discussed**: Summarize conversation
   - 📦 **Materials & Samples**: Add items shared
   - 😊 **Sentiment**: Select Positive / Neutral / Negative
   - 💼 **Outcomes**: Decision or result from meeting
3. Click **Submit Interaction**
4. ✅ Success message displays with interaction ID
5. 💡 Use "Generate Suggestions" to get AI follow-up actions

### Log Interaction via Chat (Right Panel)

1. In the **AI Chat Panel** (right side):
   - Type natural language description:
     ```
     "Met Dr. Smith today, discussed Product X efficacy, 
      very positive sentiment, shared brochure and samples"
     ```
2. Click **Log** button
3. 🤖 AI extracts and displays structured summary
4. 💡 View AI suggested follow-ups

**Key Difference**: Form = structured input, Chat = natural language input

---

## 🧪 Testing & Verification

### Test All 5 Tools

See [`TESTING.md`](./TESTING.md) for detailed cURL examples:

**Quick Test — Log an Interaction:**
```bash
curl -X POST http://localhost:8000/api/interactions/log \
  -H "Content-Type: application/json" \
  -d '{
    "note": "Met Dr. Thompson today in her office. Discussed efficacy of our new therapeutics. Positive reception. Shared clinical data."
  }'
```

**View Database Records (psql):**
```sql
-- Connect to database
psql -U postgres -d crm_db

-- Check interactions
SELECT id, hcp_id, sentiment, created_at FROM interactions LIMIT 5;

-- Check follow-up suggestions
SELECT interaction_id, suggestion_text, generated_by_ai FROM follow_up_suggestions LIMIT 5;
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'langraph'`
- **Fix**: Ensure virtual environment is activated and `pip install -r requirements.txt` was run

**Error**: `psycopg2.OperationalError: could not connect to server`
- **Fix**: Check PostgreSQL is running and `DATABASE_URL` in `.env` is correct

**Error**: `ValueError: GROQ_API_KEY not set`
- **Fix**: Add your Groq API key to `.env`

### Frontend Won't Start

**Error**: `Error: ENOENT: no such file or directory, open 'vite.config.js'`
- **Fix**: Ensure you're in the `frontend/` directory when running `npm install && npm run dev`

**Error**: API calls failing with CORS errors
- **Fix**: Verify `DATABASE_URL` in backend `.env` matches your frontend origin

### Zero Interactions Showing

- **Check**: Is the backend running? (`http://localhost:8000/docs` accessible?)
- **Check**: Did you submit via form or chat? (Check Redux DevTools)
- **Check**: Look at database: `SELECT * FROM interactions;` in psql

---

## 📚 Project Structure

```
crm/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── graph.py           # LangGraph StateGraph build
│   │   │   ├── tools.py           # 5 LangChain @tool decorators
│   │   │   ├── prompts.py         # LLM prompt templates
│   │   │   └── crm_agent.py       # Agent setup
│   │   ├── api/v1/
│   │   │   ├── interactions.py    # Endpoints wired to tools
│   │   │   ├── hcps.py            # HCP search
│   │   │   ├── chat.py            # Chat agent endpoint
│   │   │   └── router.py          # Route aggregation
│   │   ├── db/
│   │   │   ├── schema.sql          # PostgreSQL DDL
│   │   │   ├── models.py          # SQLAlchemy ORM models
│   │   │   └── database.py        # Connection & session
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic request/response
│   │   ├── main.py                # FastAPI app entry
│   │   └── core/config.py         # Settings
│   ├── tests/
│   │   └── test_tools.py          # Unit tests for all 5 tools
│   ├── requirements.txt           # Python dependencies
│   ├── alembic.ini                # DB migrations config
│   └── .env.example               # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LogInteractionForm.jsx    # Left panel form
│   │   │   ├── ChatPanel.jsx             # Right panel chat
│   │   ├── features/
│   │   │   ├── interactionSlice.js       # Form Redux state
│   │   │   ├── chatSlice.js              # Chat Redux state
│   │   ├── api/api.js                    # Axios API client
│   │   ├── app/store.js                  # Redux store config
│   │   ├── App.jsx                       # Main layout
│   │   ├── App.css                       # Layout styling
│   │   └── styles/index.css              # Global styles
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── TESTING.md                     # Integration test guide
├── README.md                      # This file
└── .gitignore
```

---

## 🤝 API Endpoints

All endpoints are **independent** — submitting via one doesn't affect others.

| Method | Endpoint | Tool | Input | Output |
|--------|----------|------|-------|--------|
| **POST** | `/api/interactions/log` | `log_interaction` | Natural language note | Extracted interaction record |
| **PUT** | `/api/interactions/{id}` | `edit_interaction` | Edit request (text) | Updated interaction |
| **GET** | `/api/interactions/hcp/{hcp_id}` | `get_hcp_history` | HCP UUID or name | LLM-summarized history |
| **POST** | `/api/interactions/{id}/suggest-followup` | `suggest_follow_up` | Interaction ID | 2-3 AI suggestions |
| **GET** | `/api/hcps/search?q=name` | `search_hcp` | Partial name or specialty | Matching HCP records |
| **POST** | `/api/chat` | Full LangGraph Agent | Free-text message | Agent response (auto-routes to tools) |

Full API documentation: `http://localhost:8000/docs`

---

## 🛠️ LangGraph Tools Reference

| # | Tool Name | Purpose | Input | Output |
|---|-----------|---------|-------|--------|
| 1 | `log_interaction` | Parse natural language note, extract entities via LLM, save structured interaction to DB | Free-text note (e.g. "Met Dr. Smith...") | Confirmation with interaction ID, extracted HCP, topics, sentiment, materials, samples |
| 2 | `edit_interaction` | Interpret a natural language edit request, map to DB fields, update record | `interaction_id` + edit text (e.g. "change sentiment to positive") | Confirmation with updated fields shown |
| 3 | `get_hcp_history` | Retrieve last N interactions for an HCP, summarize via LLM | HCP name (partial) or UUID | LLM-generated summary with themes, sentiment trends, last visit |
| 4 | `suggest_follow_up` | Analyze interaction context, generate 2-3 actionable follow-up suggestions | `interaction_id` | Saved suggestions returned to user (persisted in `follow_up_suggestions` table) |
| 5 | `search_hcp` | Search HCPs by partial name or specialty (case-insensitive) | Search query string | Matching HCP records (name, specialty, hospital, location, ID) |

Full API documentation: `http://localhost:8000/docs`

---

## 🔐 Security Notes

- **API Keys**: Never hardcode `GROQ_API_KEY` in code — use environment variables
- **Database**: Use strong PostgreSQL passwords in production
- **CORS**: Configure `ALLOWED_ORIGINS` to your production domain
- **Secrets Management**: Use AWS Secrets Manager, HashiCorp Vault, or similar in production

---

## 🚢 Deployment

### For Production:

1. **Backend**:
   - Use production database (RDS, Azure Database, etc.)
   - Set `ENVIRONMENT=production`
   - Use strong `DATABASE_URL` & rotate regularly
   - Deploy via Docker, AWS Lambda, or dedicated server

2. **Frontend**:
   - Build: `npm run build`
   - Deploy to Vercel, Netlify, S3+CloudFront, etc.
   - Update `VITE_API_BASE_URL` to production backend

3. **Database**:
   - Use managed PostgreSQL (AWS RDS, Azure Database)
   - Enable automated backups
   - Set up monitoring & alerts

---

## 📞 Support

- 📧 **Issue Tracker**: [GitHub Issues](https://github.com/yourusername/crm/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/crm/discussions)
- 📖 **Docs**: [TESTING.md](./TESTING.md) for integration tests

---

## ⚠️ Known Limitations

1. **Voice Note Summarization** — The "Summarize from Voice Note" button is scaffolded but not yet functional (requires audio transcription integration).
2. **Single-Session Chat** — Chat history is stored in Redux only and not persisted across page reloads or sessions.
3. **Groq API Downtime** — If the Groq API is unreachable, tool calls will return error messages. No automatic retry or fallback model switching is implemented at the tool level.
4. **Database Migrations** — Alembic is configured but no migration scripts are generated yet. Tables are auto-created via `create_all()` on startup.
5. **Authentication** — No user authentication or authorization is implemented. All endpoints are publicly accessible.
6. **LLM JSON Parsing** — If the LLM returns malformed JSON, the tool will return a graceful error message rather than crashing, but no automatic retry is implemented.

---

### 🎯 Key Achievements

- ✅ **Full-stack integration** from React form → FastAPI → LangGraph → PostgreSQL
- ✅ **Two submission modes**: Structured form + Natural language chat
- ✅ **Independent state trees**: Form & chat don't interfere with each other
- ✅ **LLM-powered data extraction**: All interaction parsing via Groq API
- ✅ **Production-ready code**: Error handling, validation, logging
- ✅ **Comprehensive documentation**: README + testing guide + API docs

---

## 🎓 Learning Resources

- **LangGraph**: [Documentation](https://python.langchain.com/docs/langgraph/)
- **FastAPI**: [Tutorial](https://fastapi.tiangolo.com/)
- **React + Redux**: [Official Docs](https://react.dev/) + [Redux Toolkit](https://redux-toolkit.js.org/)
- **SQLAlchemy**: [ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- **Groq API**: [API Reference](https://console.groq.com/docs)
- **PostgreSQL**: [Documentation](https://www.postgresql.org/docs/)

---

## 📋 Checklist for First-Time Users

- [ ] Read this README completely
- [ ] Review [TESTING.md](./TESTING.md) for endpoint examples
- [ ] Clone repository: `git clone ...`
- [ ] Set up backend (Python, venv, `.env`, PostgreSQL)
- [ ] Set up frontend (Node.js, `.env`, `npm install`)
- [ ] Start both services
- [ ] Test via Swagger docs: `http://localhost:8000/docs`
- [ ] Test frontend at: `http://localhost:5173`
- [ ] Run cURL commands from TESTING.md
- [ ] Verify records in PostgreSQL: `SELECT * FROM interactions;`

---

**Version**: 1.0  
**Last Updated**: April 16, 2026  
**Status**: Production-Ready ✅
