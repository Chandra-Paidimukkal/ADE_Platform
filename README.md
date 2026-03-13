# DocExtract — Agentic Document Extraction Platform

> Production-ready AI-powered document extraction platform with schema-driven extraction, multi-provider LLM support, and an interactive UI.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                  │
│  Upload → Documents → Schema Builder → Extract → Jobs       │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│                                                              │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │  Documents  │  │   Schemas    │  │   Extraction     │  │
│   │  API        │  │   API        │  │   API            │  │
│   └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│          │                │                    │             │
│   ┌──────▼──────────────────────────────────────▼─────────┐ │
│   │            Agent Orchestrator                          │ │
│   │  Parser → Layout → Split → Schema → Extract → Validate│ │
│   └──────────────────────┬─────────────────────────────────┘ │
│                          │                                    │
│   ┌───────────────────────▼───────────────────────────────┐  │
│   │          Universal LLM Injection Layer                 │  │
│   │                                                        │  │
│   │  ┌─────────┐ ┌───────────┐ ┌────────┐ ┌──────────┐  │  │
│   │  │ OpenAI  │ │Anthropic  │ │Google  │ │ Ollama   │  │  │
│   │  │Provider │ │Provider   │ │Provider│ │Provider  │  │  │
│   │  └─────────┘ └───────────┘ └────────┘ └──────────┘  │  │
│   └────────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │              Database (SQLite/PostgreSQL)            │    │
│   │  Documents · Schemas · Extraction Results · Jobs    │    │
│   └─────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone <repo>
cd docextract
docker-compose up -d
```

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Option 2: Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install your chosen LLM provider SDK
pip install openai          # For OpenAI
pip install anthropic       # For Anthropic
pip install google-generativeai  # For Google AI

# Install document parsing libraries (optional, enhances parsing)
pip install PyMuPDF pdfplumber pytesseract Pillow

# Start the server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

---

## First-Time Setup

### 1. Connect an AI Provider

Open the UI → Settings → Add Provider

Or via API:

```bash
# OpenAI
curl -X POST http://localhost:8000/api/v1/jobs/providers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai",
    "provider_type": "openai",
    "config": {"api_key": "sk-YOUR_KEY", "model": "gpt-4o"},
    "is_default": true
  }'

# Anthropic
curl -X POST http://localhost:8000/api/v1/jobs/providers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "claude",
    "provider_type": "anthropic",
    "config": {"api_key": "sk-ant-YOUR_KEY"},
    "is_default": true
  }'

# Local Ollama
curl -X POST http://localhost:8000/api/v1/jobs/providers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "local",
    "provider_type": "ollama",
    "config": {"base_url": "http://localhost:11434", "model": "llama3"},
    "is_default": true
  }'
```

### 2. Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf"
```

### 3. Create a Schema

```bash
curl -X POST http://localhost:8000/api/v1/schemas/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invoice",
    "schema_definition": {
      "invoiceNumber": "string",
      "invoiceDate": "date",
      "totalAmount": "number",
      "lineItems": [{"description": "string", "amount": "number"}]
    }
  }'
```

### 4. Run Extraction

```bash
curl -X POST http://localhost:8000/api/v1/extraction/run \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "DOC_ID",
    "schema_id": "SCHEMA_ID"
  }'
```

### 5. Export Results

```bash
# JSON
curl http://localhost:8000/api/v1/export/DOC_ID/json -o results.json

# CSV
curl http://localhost:8000/api/v1/export/DOC_ID/csv -o results.csv

# Excel
curl http://localhost:8000/api/v1/export/DOC_ID/excel -o results.xlsx
```

---

## Project Structure

```
docextract/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── documents.py        # Document upload, parsing, splitting
│   │   ├── schemas.py          # Schema CRUD + templates
│   │   ├── extraction.py       # Extraction execution + results
│   │   ├── export.py           # JSON/CSV/Excel export
│   │   └── jobs.py             # Job monitoring + provider management
│   ├── core/
│   │   ├── llm_router.py       # ★ Universal LLM Injection Layer
│   │   ├── database.py         # SQLAlchemy models + async session
│   │   ├── parser.py           # Document parsing engine
│   │   └── queue.py            # Background task queue
│   ├── agents/
│   │   └── pipeline.py         # AI Agents + Orchestrator
│   └── utils/
│       └── logger.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       └── App.jsx             # Full React application
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── schemas/
│   └── examples/
│       └── invoice.json
├── docker-compose.yml
└── README.md
```

---

## LLM Injection Layer

The `LLMRouter` in `core/llm_router.py` is the heart of the LLM-agnostic architecture.

**All LLM calls in the platform route through a single interface:**

```python
from core.llm_router import LLMRouter, LLMRequest, LLMMessage, LLMRole

router = LLMRouter()

# Register any provider
router.register_provider("my-model", "openai", {"api_key": "..."})
router.register_provider("claude", "anthropic", {"api_key": "..."})
router.register_provider("local", "ollama", {"base_url": "http://localhost:11434"})

# All agents use the same interface
request = LLMRequest(
    messages=[LLMMessage(role=LLMRole.USER, content="Extract data from...")],
    system_prompt="You are an extraction expert...",
)

response = await router.complete(request)  # Routes to default provider
response = await router.complete(request, provider_name="claude")  # Explicit
```

### Adding a Custom Provider

```python
from core.llm_router import BaseLLMProvider, LLMRequest, LLMResponse

class MyCustomProvider(BaseLLMProvider):
    async def complete(self, request: LLMRequest) -> LLMResponse:
        # Call your API here
        result = await my_api.call(request.messages)
        return LLMResponse(content=result.text, provider="my-custom")
    
    async def stream(self, request): ...
    def is_available(self): return True

# Register it
from core.llm_router import PROVIDER_REGISTRY
PROVIDER_REGISTRY["my-custom"] = MyCustomProvider
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload a document |
| POST | `/api/v1/documents/upload/batch` | Batch upload |
| GET | `/api/v1/documents/` | List documents |
| GET | `/api/v1/documents/{id}` | Get document + parsed content |
| POST | `/api/v1/documents/{id}/suggest-schema` | AI schema suggestion |
| POST | `/api/v1/documents/{id}/split` | Split document into segments |
| POST | `/api/v1/schemas/` | Create schema |
| GET | `/api/v1/schemas/` | List schemas |
| GET | `/api/v1/schemas/templates/list` | Get built-in templates |
| POST | `/api/v1/extraction/run` | Run extraction |
| POST | `/api/v1/extraction/batch` | Batch extraction |
| GET | `/api/v1/extraction/results/{doc_id}` | Get results |
| POST | `/api/v1/extraction/result/{id}/correct` | Apply corrections |
| GET | `/api/v1/export/{doc_id}/json` | Export as JSON |
| GET | `/api/v1/export/{doc_id}/csv` | Export as CSV |
| GET | `/api/v1/export/{doc_id}/excel` | Export as Excel |
| GET | `/api/v1/jobs/` | List jobs |
| GET | `/api/v1/jobs/{id}` | Get job status |
| GET | `/api/v1/jobs/providers/list` | List LLM providers |
| POST | `/api/v1/jobs/providers/register` | Register LLM provider |

Full interactive docs at: http://localhost:8000/docs

---

## Supported Document Types

| Type | Parser | Notes |
|------|--------|-------|
| PDF | PyMuPDF (preferred), pdfplumber (fallback) | Full layout + table detection |
| PNG | Tesseract OCR + Pillow | Image preprocessing + OCR |
| JPEG | Tesseract OCR + Pillow | Same as PNG |

---

## Schema Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"invoiceNumber": "string"` |
| `number` | Numeric value | `"totalAmount": "number"` |
| `boolean` | True/false | `"isPaid": "boolean"` |
| `date` | ISO date string | `"invoiceDate": "date"` |
| `object` | Nested object | `"vendor": {"name": "string"}` |
| `array` | Array of objects | `"lineItems": [{"desc": "string"}]` |

---

## Agentic Pipeline

The platform uses 6 specialized AI agents coordinated by an `AgentOrchestrator`:

1. **Parser Agent** — Converts documents to structured JSON
2. **Layout Agent** — Detects headers, tables, sections, reading order
3. **Split Agent** — Identifies logical document boundaries
4. **Schema Suggestion Agent** — Analyzes content and proposes schemas
5. **Extraction Agent** — Extracts data guided by schema
6. **Validation Agent** — Validates extracted data with corrections

---

## Configuration

Environment variables:

```env
DATABASE_URL=sqlite+aiosqlite:///./docextract.db
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

---

## License

MIT — Use freely in commercial and personal projects.
