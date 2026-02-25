# LCA Multi-Agent Analysis System

> **Automated Life Cycle Assessment (LCA) document analysis powered by a multi-agent AI pipeline.**

Upload your LCA documents (Excel, PDF, images, or CSV) and receive structured environmental impact analysis, validation results, and downloadable reports — all driven by AWS Bedrock-hosted LLMs and a LangGraph orchestration layer.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start (Local Development)](#quick-start-local-development)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Docker Deployment](#docker-deployment)
- [Agent Pipeline](#agent-pipeline)
- [Contributing](#contributing)

---

## Overview

The LCA Multi-Agent Analysis System automates the labour-intensive process of reviewing Life Cycle Assessment documents. Users upload one or more files through a React frontend; the backend spins up a job, routes each file to the appropriate specialist agent, validates the extracted data, synthesises cross-document insights, and persists all outputs to AWS S3/DynamoDB.

**Key capabilities:**

| Feature | Details |
|---|---|
| Multi-format ingestion | Excel/CSV, PDF (text & scanned), images, mind maps |
| Specialist AI agents | Dedicated agents per file type, using AWS Bedrock LLMs |
| LangGraph orchestration | Stateful DAG-based workflow with parallel agent execution |
| Dual validation | Rule-based checks + LLM plausibility/taxonomy scoring |
| Cross-document synthesis | Insight extraction and hotspot identification across all uploads |
| Structured outputs | Markdown report, analysis JSON, viz data, full audit trail |
| Live progress streaming | Server-Sent Events (SSE) log stream for real-time UI updates |
| Local code sandbox | Safe subprocess-based Excel/CSV analysis (no external sandbox API) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│              (Vite + TypeScript + Tailwind CSS)                 │
│         File Upload → Job Polling → Report Visualisation        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST / SSE
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                               │
│                                                                  │
│  ┌─────────────┐   ┌──────────────────────────────────────────┐ │
│  │  Ingestion  │   │         LangGraph Pipeline               │ │
│  │   Router    │──▶│                                          │ │
│  │  (S3 + DB)  │   │  ┌──────────┐  ┌──────────────────────┐ │ │
│  └─────────────┘   │  │ Routing  │  │   Specialist Agents  │ │ │
│                    │  │  Node    │─▶│  Excel / PDF / Image  │ │ │
│  ┌─────────────┐   │  └──────────┘  │  Generic / MindMap   │ │ │
│  │  DynamoDB   │   │                └──────────┬───────────┘ │ │
│  │  (job state)│   │  ┌─────────────────────────▼──────────┐ │ │
│  └─────────────┘   │  │  Validation (Rule + LLM)           │ │ │
│                    │  └─────────────────────────┬──────────┘ │ │
│  ┌─────────────┐   │  ┌─────────────────────────▼──────────┐ │ │
│  │   AWS S3    │   │  │  Synthesis + Report Generation     │ │ │
│  │  (outputs)  │   │  └────────────────────────────────────┘ │ │
│  └─────────────┘   └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────▼────────────────┐
           │        AWS Bedrock              │
           │  Meta Llama 4 Maverick/Scout   │
           └────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI** and **Uvicorn**
- **LangGraph** — stateful multi-agent orchestration
- **AWS Bedrock** — LLM inference (Meta Llama 4 Maverick / Scout)
- **AWS S3** — file storage and output persistence
- **AWS DynamoDB** — job and file record state
- **AWS Textract** — OCR for scanned PDFs
- **PyMuPDF** — PDF text extraction
- **pandas + openpyxl** — Excel/CSV processing via local subprocess sandbox
- **structlog** — structured JSON logging

### Frontend
- **React 18** + **TypeScript** via **Vite**
- **Tailwind CSS** — styling
- **Zustand** — state management
- **Recharts** — impact result visualisations
- **Framer Motion** — animations
- **react-dropzone** — drag-and-drop file upload

---

## Project Structure

```
lca-analysis-system/
├── backend/
│   ├── main.py                  # FastAPI app, all routes
│   ├── config.py                # Pydantic settings (env-driven)
│   ├── agents/
│   │   ├── base_agent.py        # Abstract BaseAgent
│   │   ├── excel_agent.py       # Excel/CSV specialist
│   │   ├── pdf_agent.py         # PDF (text/scanned/hybrid)
│   │   ├── image_agent.py       # Image/diagram analysis
│   │   ├── generic_agent.py     # Fallback for misc docs
│   │   └── mindmap_agent.py     # Mind map parsing
│   ├── ingestion/
│   │   ├── router.py            # Upload endpoint, S3 + DynamoDB write
│   │   ├── file_detector.py     # MIME + extension detection
│   │   └── complexity_scorer.py # Estimates processing time
│   ├── orchestrator/
│   │   ├── graph.py             # LangGraph pipeline definition
│   │   ├── dispatcher.py        # Routes files to agents
│   │   ├── routing_node.py      # Parallel routing logic
│   │   └── state.py             # AgentState TypedDict
│   ├── processing/
│   │   ├── bedrock_client.py    # Bedrock invoke wrappers
│   │   ├── local_sandbox.py     # Safe subprocess Excel execution
│   │   └── textract_client.py   # AWS Textract OCR
│   ├── validation/
│   │   ├── rule_validator.py    # Schema / completeness checks
│   │   └── llm_validator.py     # LLM-based plausibility scoring
│   ├── synthesis/
│   │   ├── synthesis_agent.py   # Orchestrates synthesis stages
│   │   └── cross_doc_synthesizer.py
│   ├── output/
│   │   ├── report_generator.py  # Markdown report builder
│   │   ├── json_exporter.py     # Structured JSON output
│   │   ├── viz_data_builder.py  # Chart-ready data
│   │   └── audit_logger.py      # Full audit trail
│   ├── storage/
│   │   ├── s3_client.py
│   │   └── dynamo_client.py
│   ├── normalization/
│   │   └── normalizer.py
│   └── utils/
│       └── logger.py
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Route pages
│   │   ├── store/               # Zustand stores
│   │   └── api/                 # Axios API client
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── aws/                         # AWS infra scripts / CloudFormation
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or higher |
| Node.js | 18 or higher |
| AWS Account | With Bedrock, S3, DynamoDB, Textract access |
| AWS CLI | Configured with appropriate IAM credentials |

> **AWS Bedrock model access:** You must request access to **Meta Llama 4 Maverick** (`us.meta.llama4-maverick-17b-instruct-v1:0`) and **Meta Llama 4 Scout** (`us.meta.llama4-scout-17b-instruct-v1:0`) in the Bedrock console before running the system.

---

## Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/krishnahn/multiagent_LCA.git
cd multiagent_LCA/lca-analysis-system
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your AWS credentials and config (see Environment Variables section)
```

### 3. Set up the Python backend

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\Activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start the backend server

> **Important:** Run from inside `lca-analysis-system/`, not from inside `backend/`.

```bash
# From lca-analysis-system/
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 5. Set up and start the frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# ─── AWS Core (required) ───
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# ─── Bedrock Models ───
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_SONNET=us.meta.llama4-maverick-17b-instruct-v1:0
BEDROCK_MODEL_HAIKU=us.meta.llama4-scout-17b-instruct-v1:0
BEDROCK_MODEL_VISION=us.meta.llama4-maverick-17b-instruct-v1:0

# ─── Textract ───
TEXTRACT_REGION=us-east-1

# ─── S3 Buckets ───
S3_BUCKET_UPLOADS=lca-uploads
S3_BUCKET_PARSED=lca-parsed
S3_BUCKET_REPORTS=lca-reports
S3_BUCKET_AUDIT=lca-audit-logs
S3_BUCKET_TEMP=lca-temp

# ─── DynamoDB Tables ───
DYNAMO_TABLE_FILES=lca-files
DYNAMO_TABLE_ANALYSES=lca-analyses

# ─── Application ───
MAX_FILE_SIZE_MB=100
MAX_FILES_PER_JOB=20
SANDBOX_TIMEOUT_SECONDS=120
VLM_MIN_CONFIDENCE=3
LOG_LEVEL=INFO
VIRUS_SCAN_ENABLED=false
MOCK_AWS=false
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

> ⚠️ **Never commit your real `.env` file.** It is listed in `.gitignore`. Use `.env.example` as the template.

---

## API Reference

All routes are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/jobs` | Create a new job, upload files |
| `GET` | `/api/v1/jobs/{job_id}` | Poll job status and file processing state |
| `GET` | `/api/v1/jobs/{job_id}/report` | Retrieve full analysis result (Markdown + JSON + viz data) |
| `GET` | `/api/v1/jobs/{job_id}/logs` | SSE stream of live processing logs |
| `GET` | `/api/v1/jobs/{job_id}/download/report` | Download Markdown report as `.md` file |
| `GET` | `/api/v1/jobs/{job_id}/download/json` | Download structured analysis as `.json` file |
| `GET` | `/api/v1/jobs/{job_id}/download/audit` | Download audit trail as `.json` file |
| `POST` | `/api/v1/jobs/{job_id}/force-include-quarantined` | Re-run synthesis including quarantined files |
| `GET` | `/api/v1/health` | Health check (Bedrock, S3, DynamoDB connectivity) |

Full interactive docs available at `http://localhost:8000/docs` when running locally.

---

## Docker Deployment

The project ships with Docker Compose including a local DynamoDB and LocalStack S3:

```bash
cd lca-analysis-system

# Build and start all services
docker-compose up --build

# Services:
# Backend API   → http://localhost:8000
# Frontend      → http://localhost:3000
# DynamoDB local → http://localhost:8100
# LocalStack S3  → http://localhost:4566
```

For production deployment, set `MOCK_AWS=false` and provide real AWS credentials via environment variables or an IAM role.

---

## Agent Pipeline

Each uploaded file passes through the following stages:

```
Upload → File Detection → Routing → Specialist Agent → Validation → Synthesis → Output
```

### Specialist Agents

| Agent | File Types | Method |
|---|---|---|
| `ExcelAgent` | `.xlsx`, `.xls`, `.csv` | Local subprocess sandbox (`pandas`) with openpyxl fallback |
| `PDFTextAgent` | Text-native PDFs | PyMuPDF text extraction + Bedrock summarisation |
| `PDFScannedAgent` | Image-based PDFs | AWS Textract OCR + Bedrock analysis |
| `PDFHybridAgent` | Mixed PDFs | Combined Textract + PyMuPDF |
| `ImageAgent` | `.png`, `.jpg`, `.gif`, etc. | Bedrock vision model (Llama 4 Maverick) |
| `MindMapAgent` | Mind map exports | Structure extraction + Bedrock |
| `GenericAgent` | All other formats | Fallback Bedrock text analysis |

### Validation

- **Rule Validator** — checks for required LCA fields, numeric ranges, unit consistency, and data completeness (27 checks)
- **LLM Validator** — uses Bedrock to score methodology quality, data quality, completeness, and plausibility

### Outputs (per job)

| Output | S3 Path |
|---|---|
| Markdown report | `reports/{job_id}/full_report.md` |
| Structured JSON | `reports/{job_id}/analysis.json` |
| Visualisation data | `reports/{job_id}/viz_data.json` |
| Audit trail | `audit/{job_id}/audit.json` |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please ensure all Python code passes `ruff` linting and `mypy` type checks before submitting.

---

