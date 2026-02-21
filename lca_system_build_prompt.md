# LCA Multi-Agent Document Analysis System — Full Build Specification

> **Instructions for the builder:** You are building a complete, production-ready multi-agent system for analysing Life Cycle Assessment (LCA) documents. This document is the single source of truth. Build every layer described here — backend agents, orchestration, API, and frontend — in full. Do not stub, skip, or placeholder any component. Read every section before writing a single line of code.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Tech Stack](#3-tech-stack)
4. [Environment & Configuration](#4-environment--configuration)
5. [Backend — Phase 1: Ingestion Service](#5-backend--phase-1-ingestion-service)
6. [Backend — Phase 2: Orchestrator](#6-backend--phase-2-orchestrator)
7. [Backend — Phase 3A: Excel Agent](#7-backend--phase-3a-excel-agent)
8. [Backend — Phase 3B: PDF Hybrid Agent](#8-backend--phase-3b-pdf-hybrid-agent)
9. [Backend — Phase 3C: Image VLM Agent](#9-backend--phase-3c-image-vlm-agent)
10. [Backend — Phase 3D: Mind Map Agent](#10-backend--phase-3d-mind-map-agent)
11. [Backend — Phase 3E: Generic Agent](#11-backend--phase-3e-generic-agent)
12. [Backend — Phase 4: Normalization Layer](#12-backend--phase-4-normalization-layer)
13. [Backend — Phase 5: LCA Validation Layer](#13-backend--phase-5-lca-validation-layer)
14. [Backend — Phase 6: Synthesis Agent](#14-backend--phase-6-synthesis-agent)
15. [Backend — Phase 7: Output Generator](#15-backend--phase-7-output-generator)
16. [REST API Layer](#16-rest-api-layer)
17. [Frontend — Design & Architecture](#17-frontend--design--architecture)
18. [Frontend — Pages & Components](#18-frontend--pages--components)
19. [Frontend — State Management & API Integration](#19-frontend--state-management--api-integration)
20. [Error Handling Strategy](#20-error-handling-strategy)
21. [Testing Requirements](#21-testing-requirements)
22. [Data Schemas — Complete Reference](#22-data-schemas--complete-reference)

---

## 1. Project Overview

### What This System Does

This system accepts LCA (Life Cycle Assessment) documents in any format — Excel workbooks, PDFs (text-based, scanned, or hybrid), images, mind maps, Word documents — and processes them through a coordinated multi-agent pipeline. Each file is routed to the specialist agent best suited for its format. Every agent extracts content, normalises it to Markdown and structured JSON, passes it through an LCA domain validation layer, and feeds the validated content into a synthesis agent that produces a unified, cross-document LCA analysis report.

### Who Uses It

Environmental consultants, sustainability analysts, LCA practitioners, and corporate ESG teams who need to rapidly synthesise large, heterogeneous LCA document sets.

### Core User Journey

1. User visits the web application and uploads one or more LCA documents (any mix of formats)
2. The system ingests the files, classifies them, and routes each to the correct agent
3. The user watches real-time progress: per-file status, agent assignments, live logs
4. Once all files are processed and validated, the synthesis agent produces the final report
5. User views the structured results dashboard: impact charts, hotspot breakdown, document summaries, data quality scores
6. User downloads the Markdown report, JSON data, or audit trail

---

## 2. Repository Structure

Build the project with this exact directory layout:

```
lca-analysis-system/
│
├── backend/
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # All environment variable loading + validation
│   ├── models/
│   │   ├── schemas.py                 # All Pydantic models (request/response/internal)
│   │   └── enums.py                   # Enums: AgentType, FileStatus, ValidationStatus
│   │
│   ├── ingestion/
│   │   ├── router.py                  # FastAPI router for /upload endpoints
│   │   ├── file_detector.py           # Magic-byte file type detection
│   │   ├── complexity_scorer.py       # File complexity scoring (0–1)
│   │   └── virus_scanner.py           # ClamAV integration (stub if unavailable)
│   │
│   ├── orchestrator/
│   │   ├── graph.py                   # LangGraph StateGraph definition
│   │   ├── state.py                   # AgentState TypedDict definition
│   │   ├── routing_node.py            # LLM-based routing decision node
│   │   └── dispatcher.py             # Parallel/sequential agent dispatch logic
│   │
│   ├── agents/
│   │   ├── base_agent.py              # Abstract base class all agents inherit
│   │   ├── excel_agent.py             # Excel parsing via E2B sandbox
│   │   ├── pdf_agent.py               # PDF hybrid agent (Textract + VLM)
│   │   ├── image_agent.py             # Image VLM agent (two-pass)
│   │   ├── mindmap_agent.py           # Mind map parser (native + VLM fallback)
│   │   └── generic_agent.py           # Fallback agent (pandoc + unstructured)
│   │
│   ├── processing/
│   │   ├── textract_client.py         # AWS Textract wrapper
│   │   ├── vlm_client.py              # Claude Vision wrapper (Bedrock)
│   │   ├── bedrock_client.py          # Claude Sonnet/Haiku text wrapper (Bedrock)
│   │   ├── e2b_sandbox.py             # E2B code execution wrapper
│   │   └── pdf_page_classifier.py     # Per-page pymupdf classification logic
│   │
│   ├── normalization/
│   │   ├── normalizer.py              # Converts all agent outputs to unified schema
│   │   └── markdown_converter.py      # Table/chart/list → Markdown helpers
│   │
│   ├── validation/
│   │   ├── rule_validator.py          # Deterministic LCA rule checks
│   │   ├── llm_validator.py           # LLM-based taxonomy + plausibility checks
│   │   └── lca_taxonomy.py            # EF 3.1 + ReCiPe 2016 reference data
│   │
│   ├── synthesis/
│   │   ├── synthesis_agent.py         # 3-stage synthesis orchestration
│   │   ├── per_doc_summarizer.py      # Stage 1: per-document summaries
│   │   ├── cross_doc_synthesizer.py   # Stage 2: cross-document synthesis
│   │   └── insight_extractor.py       # Stage 3: hotspots, uncertainty, completeness
│   │
│   ├── output/
│   │   ├── report_generator.py        # Markdown report builder
│   │   ├── json_exporter.py           # Structured JSON export
│   │   ├── viz_data_builder.py        # Chart-ready data builder
│   │   └── audit_logger.py            # Full audit trail writer
│   │
│   ├── storage/
│   │   ├── s3_client.py               # S3 read/write helpers
│   │   ├── dynamo_client.py           # DynamoDB helpers
│   │   └── opensearch_client.py       # OpenSearch indexing helpers
│   │
│   └── utils/
│       ├── logger.py                  # Structured logging setup
│       ├── retry.py                   # Retry decorator with backoff
│       └── chunker.py                 # Large-text chunking for LLM context limits
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts              # Axios instance with base URL + interceptors
│   │   │   ├── uploads.ts             # Upload API calls
│   │   │   ├── jobs.ts                # Job status polling
│   │   │   └── reports.ts             # Report retrieval
│   │   │
│   │   ├── store/
│   │   │   ├── jobStore.ts            # Zustand store for active jobs
│   │   │   └── reportStore.ts         # Zustand store for loaded reports
│   │   │
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx         # Main upload interface
│   │   │   ├── ProcessingPage.tsx     # Live pipeline progress view
│   │   │   └── ReportPage.tsx         # Final results dashboard
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Shell.tsx          # App shell with sidebar navigation
│   │   │   │   └── TopBar.tsx         # Top navigation bar
│   │   │   ├── upload/
│   │   │   │   ├── DropZone.tsx       # Drag-and-drop file upload area
│   │   │   │   ├── FileCard.tsx       # Per-file display card (type icon, name, size)
│   │   │   │   └── FormatBadge.tsx    # Color-coded format badge (PDF, Excel, etc.)
│   │   │   ├── processing/
│   │   │   │   ├── PipelineView.tsx   # Visual pipeline stages with live status
│   │   │   │   ├── AgentCard.tsx      # Per-agent live status card
│   │   │   │   ├── LogStream.tsx      # Real-time log output viewer
│   │   │   │   └── ProgressRing.tsx   # Circular progress indicator
│   │   │   └── report/
│   │   │       ├── ImpactChart.tsx    # Bar chart: impact categories
│   │   │       ├── HotspotChart.tsx   # Pareto chart: top hotspots
│   │   │       ├── CompletenessGauge.tsx  # Completeness score gauge
│   │   │       ├── DocSummaryCard.tsx # Per-document summary accordion
│   │   │       ├── ValidationBadge.tsx    # Pass/warn/fail validation indicator
│   │   │       └── MarkdownViewer.tsx # Rendered Markdown report viewer
│   │   │
│   │   └── hooks/
│   │       ├── useJobPolling.ts       # Polls job status every 3 s until complete
│   │       └── useSSE.ts              # Server-Sent Events hook for live logs
│
├── docker-compose.yml                 # Local dev: API + frontend + localstack
├── Dockerfile.backend
├── Dockerfile.frontend
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** — REST API framework with async support
- **LangGraph** (`langgraph>=0.2`) — Agent state machine orchestration
- **Anthropic Bedrock SDK** (`boto3` + `anthropic`) — Claude Sonnet, Claude Haiku, Claude Vision
- **AWS Textract** (`boto3`) — PDF OCR + table extraction
- **E2B Code Interpreter** (`e2b-code-interpreter`) — Sandboxed Python execution for Excel
- **pymupdf** (`fitz`) — PDF page analysis and image extraction
- **pandas + openpyxl + xlrd** — Excel structure inspection
- **python-magic** — True file-type detection from magic bytes
- **pandoc** (system binary) + **unstructured** (pip) — Generic document parsing
- **xmind-sdk** + **xml.etree** — Mind map native parsing
- **Pydantic v2** — Data validation and serialisation
- **boto3** — S3, DynamoDB, OpenSearch
- **uvicorn** — ASGI server
- **python-multipart** — File upload handling
- **structlog** — Structured logging

### Frontend
- **React 18 + TypeScript**
- **Vite** — Build tool
- **Tailwind CSS** — Utility-first styling
- **Zustand** — Lightweight global state management
- **Recharts** — Data visualisation (impact charts, hotspot Pareto)
- **React Dropzone** — Drag-and-drop file upload
- **React Markdown + remark-gfm** — Markdown report rendering
- **Axios** — HTTP client with interceptors
- **Framer Motion** — Animations and transitions
- **Lucide React** — Icon set
- **React Hot Toast** — Toast notifications

---

## 4. Environment & Configuration

Create a `config.py` that loads and validates all of the following from environment variables. The app must **refuse to start** if required variables are missing.

### Required Variables

```
# AWS Core
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# AWS Bedrock (LLM + Vision)
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_SONNET=anthropic.claude-sonnet-4-6       # Routing, validation, synthesis
BEDROCK_MODEL_HAIKU=anthropic.claude-haiku-4-5-20251001  # Code gen, per-doc summaries
BEDROCK_MODEL_VISION=anthropic.claude-sonnet-4-6       # Image + diagram VLM

# AWS Textract
TEXTRACT_REGION=us-east-1

# E2B (Code Sandbox)
E2B_API_KEY=

# AWS S3 Buckets
S3_BUCKET_UPLOADS=lca-uploads
S3_BUCKET_PARSED=lca-parsed
S3_BUCKET_REPORTS=lca-reports
S3_BUCKET_AUDIT=lca-audit-logs
S3_BUCKET_TEMP=lca-temp

# AWS DynamoDB Tables
DYNAMO_TABLE_FILES=lca-files
DYNAMO_TABLE_ANALYSES=lca-analyses

# AWS OpenSearch
OPENSEARCH_ENDPOINT=
OPENSEARCH_INDEX=lca-documents

# Application
MAX_FILE_SIZE_MB=100
MAX_FILES_PER_JOB=20
SANDBOX_TIMEOUT_SECONDS=120
VLM_MIN_CONFIDENCE=3
LOG_LEVEL=INFO
```

### Optional Variables
```
VIRUS_SCAN_ENABLED=true          # Set false for local dev to skip ClamAV
MOCK_AWS=false                   # Set true to use LocalStack for local dev
CORS_ORIGINS=http://localhost:5173
```

---

## 5. Backend — Phase 1: Ingestion Service

### Responsibility
Accept file uploads via the API, run pre-processing checks, extract metadata, and register each file in DynamoDB before handing off to the orchestrator.

### File Type Detection (`file_detector.py`)
Use `python-magic` to read the first 2048 bytes of each uploaded file and determine the actual MIME type, regardless of the file extension. Map the detected MIME type to an internal `FileType` enum:

| Detected MIME | Internal FileType |
|---|---|
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `EXCEL` |
| `application/vnd.ms-excel` | `EXCEL` |
| `text/csv` | `CSV` |
| `application/pdf` | `PDF` |
| `image/png`, `image/jpeg`, `image/tiff`, `image/webp` | `IMAGE` |
| `application/zip` (then probe for `.xmind` structure) | `MINDMAP_XMIND` |
| `text/xml` (then check for FreeMind schema) | `MINDMAP_FREEMIND` |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `DOCX` |
| `text/plain` | `TEXT` |
| `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `PPTX` |
| Anything else | `UNKNOWN` |

### PDF Structure Probing
When the detected type is `PDF`, perform additional structure analysis using pymupdf to populate these fields:
- `has_text_layer`: True if any page contains extractable text (text length > 50 chars per page on average)
- `has_embedded_images`: True if any page contains embedded image objects
- `is_scanned`: True if `has_text_layer` is False, or if average text density per page is below 50 characters despite page count > 3
- `has_tables_heuristic`: True if line-detection heuristics suggest tabular structure on any page
- `page_count`: integer

### Complexity Scoring (`complexity_scorer.py`)
Return a float 0.0–1.0. Higher means more complex (longer processing time expected). Base the score on:
- PDF: `page_count / 200` capped at 0.6, plus 0.2 if `has_embedded_images`, plus 0.2 if `is_scanned`
- Excel: `sheet_count / 20` capped at 0.5, plus `estimated_row_count / 100000` capped at 0.5
- Image: fixed 0.4 (VLM is always called)
- Mind map: fixed 0.3
- Generic: fixed 0.2
- Unknown: fixed 0.5

### DynamoDB Registration
Write the following record to the `lca-files` table with `file_id` as the partition key:

```
file_id             (String, PK)      — UUID v4
job_id              (String, GSI)     — UUID v4, groups files that were uploaded together
original_name       (String)
s3_key              (String)          — e.g. uploads/{job_id}/{file_id}/{original_name}
actual_mime         (String)
file_type           (String)          — from FileType enum
size_bytes          (Number)
is_scanned          (Boolean)
has_text_layer      (Boolean)
has_embedded_images (Boolean)
page_count          (Number or null)
sheet_count         (Number or null)
complexity_score    (Number)
status              (String)          — PENDING | PROCESSING | COMPLETED | FAILED | QUARANTINED
upload_timestamp    (String, ISO8601)
agent_assigned      (String or null)
```

### Upload Endpoint Behaviour
- Accept multipart/form-data with 1–20 files
- Validate file size against `MAX_FILE_SIZE_MB`
- Run magic-byte detection for every file
- Run complexity scoring
- Upload each file to S3 at `uploads/{job_id}/{file_id}/{original_name}`
- Write DynamoDB record for each file
- Create a job-level record in `lca-analyses` table with `job_id` and `status: PENDING`
- Return the `job_id` immediately — processing happens asynchronously (FastAPI `BackgroundTasks`)

---

## 6. Backend — Phase 2: Orchestrator

### Responsibility
The orchestrator is the brain of the system. It is implemented as a LangGraph `StateGraph`. It reads all file metadata for a job, decides which agent handles each file, dispatches files to agents (in parallel where possible), and coordinates the flow through validation and synthesis.

### AgentState Definition (`state.py`)
This is the single shared state object that flows through the entire LangGraph graph. Define it as a `TypedDict`:

```
files                  List[FileMetadata]      — File metadata records from DynamoDB
job_id                 str
user_context           Dict                    — Optional: methodology, industry, scope hint
routing_decisions      Dict[str, str]          — file_id → agent_name
processing_plan        Dict                    — { execution: "parallel"|"sequential", estimated_seconds: int }
current_processing     List[str]               — file_ids currently being processed
parsed_outputs         List[ParsedOutput]      — Accumulated results from all agents
errors                 List[ErrorRecord]       — All failures across the pipeline
validation_results     Dict[str, ValidationReport]   — file_id → validation report
synthesis_ready        bool
final_output           FinalOutput
progress               Dict[str, float]        — file_id → 0.0–1.0 progress
```

### Routing Node (`routing_node.py`)
This node calls Claude Sonnet via Bedrock to decide which agent handles each file. It receives the full list of file metadata records. The prompt must instruct the model to consider:
- The `file_type` field (primary signal)
- For PDFs: `is_scanned`, `has_text_layer`, `has_embedded_images` to pick between `pdf_text_agent`, `pdf_hybrid_agent`, or `pdf_scanned_agent`
- The `complexity_score` and whether parallel or sequential execution is more appropriate

The model must return a structured JSON object with `routing` (file_id → agent name mapping), `execution_plan` (`parallel` or `sequential`), and `estimated_time_seconds`.

The valid agent names are: `excel_agent`, `pdf_text_agent`, `pdf_hybrid_agent`, `pdf_scanned_agent`, `image_vlm_agent`, `mindmap_agent`, `generic_agent`.

Parse the response strictly. If JSON parsing fails, fall back to rule-based routing using the `file_type` enum directly (no LLM required for the fallback).

### LangGraph Graph Structure (`graph.py`)
Define the following nodes in the StateGraph:
- `routing_node` — entry point; sets `routing_decisions` in state
- `excel_agent_node` — processes files routed to `excel_agent`
- `pdf_hybrid_agent_node` — processes files routed to `pdf_hybrid_agent` or `pdf_scanned_agent`
- `pdf_text_agent_node` — processes files routed to `pdf_text_agent`
- `image_vlm_agent_node` — processes files routed to `image_vlm_agent`
- `mindmap_agent_node` — processes files routed to `mindmap_agent`
- `generic_agent_node` — processes files routed to `generic_agent`
- `normalization_node` — runs after all agent nodes complete; normalises all outputs
- `validation_node` — runs LCA validation on all normalised outputs
- `synthesis_node` — runs 3-stage synthesis
- `output_node` — generates final outputs and stores them

Define conditional edges so that after `routing_node`, the graph fans out to whichever agent nodes are needed for that job (only the agents actually required run; skip the rest). All agent nodes converge at `normalization_node`. From there the flow is linear: normalization → validation → synthesis → output.

For parallel execution, use LangGraph's `Send` API to dispatch multiple files to the same agent node concurrently.

### Progress Updates
Every time a node completes processing a file, update the DynamoDB `lca-files` record with `status: COMPLETED` and write the progress to the job record. This is what the frontend polls.

---

## 7. Backend — Phase 3A: Excel Agent

### Responsibility
Parse Excel files (`.xlsx`, `.xls`, `.xlsm`) and CSV files. Extract all tabular data, convert to Markdown, identify LCA-relevant content, and return the normalised output.

### Step 1 — Structure Inspection (no sandbox)
Before generating any code, open the file locally with openpyxl to read sheet names, estimated row counts per sheet, and detect any named ranges or pivot tables. This takes < 1 second and does not require sandboxing.

### Step 2 — Code Generation (Claude Haiku)
Send the sheet names, row counts, and sample column headers to Claude Haiku with a prompt that instructs it to generate a complete Python pandas script that:
- Reads all sheets into DataFrames
- Skips empty sheets
- Converts each non-empty DataFrame to Markdown table format (using `df.to_markdown()`)
- Detects LCA-relevant column names (match against a list including: `Impact Category`, `CO2`, `GWP`, `Functional Unit`, `Process`, `Ecoinvent`, `CO2 eq`, `kg CO2`, `MJ`, `LCA`, `emission`, `inventory`, `impact`, `characterisation`, `normalisation`)
- For any detected LCA columns, flags `lca_relevant: True`
- Extracts any numeric summary statistics for LCA columns
- Outputs a single JSON object with keys: `sheets` (list of `{name, markdown, lca_relevant, columns}`), `lca_data_found`, `errors`
- Contains no network calls, no shell commands, no file system access beyond reading the input file (which will be available at `/home/user/input_file`)

The prompt to Haiku must explicitly say: "Return ONLY the Python code block. No explanation, no preamble."

### Step 3 — Sandbox Execution (E2B)
Use the E2B Code Interpreter SDK to:
1. Create a new sandbox session
2. Upload the Excel file to `/home/user/input_file` in the sandbox
3. Execute the generated code
4. If exit code is 0, parse stdout as JSON
5. If exit code is non-zero or execution exceeds `SANDBOX_TIMEOUT_SECONDS`, trigger retry

### Retry Strategy
- **Attempt 2:** Ask Haiku for simpler code (just `pd.read_excel(file, sheet_name=None)` for each sheet, no fancy detection, just raw read and `to_markdown`)
- **Attempt 3 (fallback):** Use openpyxl locally (outside sandbox) to read cell values row by row; convert each sheet to a basic Markdown table manually in Python

### Output
Produce a `ParsedOutput` object with:
- `markdown`: All sheets concatenated as `## Sheet: {name}` sections with Markdown tables underneath
- `structured_json`: The parsed JSON from the sandbox execution
- `lca_relevant`: from `lca_data_found` field
- `confidence`: 0.95 for successful sandbox execution, 0.70 for openpyxl fallback

---

## 8. Backend — Phase 3B: PDF Hybrid Agent

### Responsibility
Process PDFs that may contain any mix of text, scanned pages, data tables, images, diagrams, system boundary flowcharts, and equations. This is the most complex agent.

### Step 1 — Per-Page Classification (`pdf_page_classifier.py`)
Open the PDF with pymupdf. For every page, extract:
- `text_length`: length of `page.get_text()` result
- `image_count`: `len(page.get_images(full=True))`
- `has_table_heuristic`: check if `page.get_drawings()` returns many horizontal/vertical lines in grid-like patterns (simple heuristic: > 10 lines with alignment suggests a table)

Classify each page into one of four types:
- `text_heavy`: `text_length > 500` AND `image_count == 0`
- `table_heavy`: `has_table_heuristic == True`
- `image_heavy`: `image_count > 0` AND `text_length < 200`
- `mixed`: anything else with both text and images

### Step 2 — Process Each Page by Its Type

**For `text_heavy` pages:**
Call AWS Textract `DetectDocumentText` on the page (converted to a PNG byte stream via pymupdf). Extract all `LINE` blocks. Join them with newlines. This gives clean text even from text-layer PDFs, and is more reliable than pymupdf text extraction for columnar layouts.

**For `table_heavy` pages:**
Call AWS Textract `AnalyzeDocument` with `FeatureTypes=["TABLES", "FORMS"]`. Parse the `TABLE`, `CELL`, and `MERGED_CELL` blocks from the response. Reconstruct each table as a Markdown table (with proper column alignment). If FORMS blocks are present, extract them as a key-value list.

**For `image_heavy` pages:**
Extract all embedded images from the page using `page.get_images(full=True)` and `doc.extract_image(xref)`. Send each image to the VLM client (Claude Vision). Use the two-pass prompt strategy described in Phase 3C (Image Agent). Combine all VLM outputs for the page.

**For `mixed` pages:**
Run both the Textract text extraction AND the image VLM extraction. Merge the outputs in reading order: interleave text blocks and VLM descriptions based on their vertical position on the page (use Textract bounding box Y coordinates and image Y positions from pymupdf `page.get_image_info()`).

**For fully scanned PDFs (`is_scanned == True`):**
Skip page classification. For every page, render it to PNG at 200 DPI using pymupdf `page.get_pixmap()`. Send the entire page PNG to Textract `AnalyzeDocument` with `TABLES` enabled. Then additionally send each page to Claude Vision for a holistic description, since Textract may miss context that VLM captures.

### Step 3 — Assembly
Combine all page outputs into a single Markdown document with page-break markers (`---`). Write the full Markdown to S3 at `parsed/{job_id}/{file_id}/content.md`.

### Confidence Scoring
Average the per-page Textract confidence scores (available in the Textract response blocks) and blend with a fixed VLM confidence (from the VLM's self-reported score). A page with no Textract blocks AND VLM confidence < 3 should be flagged as `low_confidence`.

---

## 9. Backend — Phase 3C: Image VLM Agent

### Responsibility
Process standalone image files (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.webp`) using a two-pass VLM prompting strategy.

### Pass 1 — Visual Classification Prompt
Send the image to Claude Vision (Bedrock) with the following system context:

> "You are an LCA (Life Cycle Assessment) document analyst specialising in visual content extraction. Classify the type of visual content in this image."

And a user prompt asking the model to identify which of these types best describes the image:
- `bar_chart` — bar, column, or stacked chart
- `pie_chart` — pie or donut chart
- `line_chart` — line or area chart
- `table_screenshot` — a photograph or screenshot of a table
- `system_boundary_diagram` — boxes and arrows showing a product system
- `process_flowchart` — flowchart with decision nodes
- `mind_map` — radial or hierarchical mind map
- `equation` — mathematical formula or calculation
- `photograph` — real-world photograph of a product, facility, or material
- `mixed` — combination of the above
- `other` — none of the above

The model must also return a confidence score (1–5) for its classification. Return format: JSON `{"visual_type": "...", "confidence": N, "brief_description": "..."}`.

### Pass 2 — Type-Specific Extraction Prompt
Based on the classification from Pass 1, call Claude Vision again with a type-specific extraction prompt:

**For `bar_chart`, `pie_chart`, `line_chart`:**
Prompt the model to extract every visible data label, axis label, legend entry, title, unit, and numeric value. Ask it to present the data as a Markdown table where rows are categories and columns are series.

**For `table_screenshot`:**
Prompt the model to reconstruct the table exactly as a Markdown table, preserving all column headers, row labels, and cell values. Preserve units in the header row.

**For `system_boundary_diagram` or `process_flowchart`:**
Prompt the model to list every box/node, every arrow and its direction, every label on arrows, and every boundary line. Format as a structured description with sub-sections for Inputs, Processes, Outputs, and System Boundary.

**For `mind_map`:**
Prompt the model to reconstruct the mind map as a nested Markdown list, preserving the hierarchy from the central node outward.

**For `equation`:**
Prompt the model to transcribe the equation in both LaTeX syntax and plain English prose.

**For `photograph`:**
Prompt the model to describe what is shown and identify any LCA-relevant context (materials, processes, transportation, energy sources visible).

**For `mixed` or `other`:**
Use a general extraction prompt asking the model to describe all visible content section by section, presenting any data as Markdown tables and any hierarchies as nested lists.

### Confidence Gate
If Pass 1 returns `confidence < VLM_MIN_CONFIDENCE` (default: 3), flag the output with `low_confidence: True` and include a warning in the agent output. Do not skip — include the best-effort extraction but mark it for human review.

---

## 10. Backend — Phase 3D: Mind Map Agent

### Responsibility
Parse mind map files in native formats. Use VLM only as a last resort.

### Native Format Parsing

**XMind (`.xmind`):**
XMind files are ZIP archives. Unzip in memory. Look for `content.json` (XMind 8+) or `content.xml` (older). Parse the JSON/XML to extract the root topic and all child topics recursively. Reconstruct as a nested Markdown list where the root topic is the `#` heading and each level of children is an additional level of indentation.

**MindManager (`.mmap`):**
`.mmap` files are XML. Parse with `xml.etree.ElementTree`. The root element is `<Map>` with nested `<Topic>` elements. Recursively extract `Text` attributes from each `<Topic>` element. Reconstruct as nested Markdown list.

**FreeMind (`.mm`):**
FreeMind files are XML with `<map>` root and `<node>` elements. Parse with `xml.etree.ElementTree`. Extract `TEXT` attributes recursively. Reconstruct as nested Markdown list.

### VLM Fallback
If the file is an image export of a mind map (identified by the routing node as `IMAGE` type with a mind-map-like visual classification in Pass 1), route it through the Image VLM Agent with the `mind_map` extraction prompt.

### LCA Context Summary
After reconstructing the nested Markdown list, send it to Claude Haiku with a prompt asking: "This is a mind map from an LCA study. Summarise the key topics, identify any LCA-specific nodes (impact categories, processes, life cycle stages, methodologies), and flag missing standard LCA components." Append the summary under a `## Mind Map Summary` heading in the output.

---

## 11. Backend — Phase 3E: Generic Agent

### Responsibility
Handle all file types not covered by the specialist agents: `.docx`, `.txt`, `.rtf`, `.pptx`, `.odt`. Convert to plain Markdown and extract LCA-relevant content.

### Conversion
Use the system `pandoc` binary via `subprocess` to convert the input file to Markdown. Command: `pandoc -f {input_format} -t markdown --wrap=none {input_path} -o {output_path}`. Map file extensions to pandoc input formats: `docx → docx`, `txt → plain`, `rtf → rtf`, `pptx → pptx`, `odt → odt`.

If pandoc is unavailable or fails, use the `unstructured` Python library as fallback: `partition(filename=input_path)` returns a list of elements. Convert each element to Markdown based on its type (Title → `##`, NarrativeText → paragraph, Table → Markdown table, Image → `[Image: embedded image]`).

### LCA Section Detection
After converting to Markdown, send the text to Claude Haiku with a prompt to identify and extract sections that are LCA-relevant. The model should return a JSON list of `{section_title, content, lca_relevance_score (0-10)}`. Only include sections with `lca_relevance_score >= 5` in the primary Markdown output. Include all sections in the `structured_json` output.

---

## 12. Backend — Phase 4: Normalization Layer

### Responsibility
Every agent produces output in a slightly different internal format. The normalisation layer converts all of them to a single unified `ParsedOutput` schema. This is the contract that all downstream phases (validation, synthesis) depend on.

### ParsedOutput Schema
```
file_id              str
job_id               str
agent                str              — which agent produced this
markdown             str              — full extracted content as Markdown
structured_json      Dict             — agent-specific structured data
lca_relevant         bool             — is this file LCA data?
confidence           float            — 0.0–1.0
low_confidence_pages List[int]        — page numbers flagged as low confidence (PDFs)
word_count           int              — word count of the Markdown
processing_time_s    float
errors               List[str]        — non-fatal errors encountered
warnings             List[str]        — quality warnings
```

### Normalisation Steps
1. Trim all Markdown to remove leading/trailing whitespace
2. Ensure every Markdown table has a separator row (`|---|---|`)
3. Deduplicate identical consecutive lines (artifact of some Textract responses)
4. Count words
5. Cap `confidence` at 1.0
6. Store the Markdown to S3 at `parsed/{job_id}/{file_id}/content.md`
7. Store the `ParsedOutput` JSON to S3 at `parsed/{job_id}/{file_id}/metadata.json`
8. Update DynamoDB `lca-files` record: `status = COMPLETED`, append parsed S3 paths

---

## 13. Backend — Phase 5: LCA Validation Layer

### Responsibility
Before synthesis, validate that the extracted content is LCA-coherent. Two-track validation: deterministic rule checks first, then LLM checks.

### Track A — Rule-Based Validation (`rule_validator.py`)

Run the following checks on the Markdown and structured JSON of each file:

**Unit Check:** Scan all Markdown tables for numeric cells adjacent to unit strings. The unit must be in the recognised LCA unit set. Build this set from the `lca_taxonomy.py` reference file, which must include at minimum:
- Mass: `kg`, `g`, `t`, `tonne`
- GWP: `kg CO2 eq`, `kg CO2-eq`, `CO2e`, `kg CO2`
- Energy: `MJ`, `kWh`, `GJ`
- Acidification: `mol H+ eq`, `kg SO2 eq`
- Eutrophication: `kg P eq`, `kg N eq`, `mol N eq`
- Water: `m3`, `l`, `litre`
- Ecotoxicity: `CTUe`
- Human toxicity: `CTUh`
- Land use: `m2`, `m2*year`
- Any string ending in `eq`

If a numeric value is found in an LCA-relevant column but has no recognisable unit, add a warning: `"Numeric value in column '{col}' has unrecognised unit '{unit}'"`

**Plausibility Check:** Flag any negative numeric values in impact category columns as suspicious (LCA impact values should not be negative, except in specific system expansion scenarios). Add a warning if found.

**Functional Unit Check:** Search the Markdown for the phrase `functional unit` (case-insensitive). If not found in any file for the entire job, add a job-level error: `"No functional unit identified in any document"`.

**System Boundary Check:** Search for `system boundary`, `cradle-to`, `gate-to`, `A1`, `A2`, `A3`, `B`, `C` (life cycle stage codes). If none found in any file, add a warning.

**Required Sections Check:** For files with `lca_relevant == True` and `word_count > 500`, check that at least 2 of these 4 section types are identifiable: Goal & Scope, Inventory Analysis (LCI), Impact Assessment (LCIA), Interpretation. If fewer than 2, add a warning.

### Track B — LLM-Based Validation (`llm_validator.py`)

After rule checks, send the Markdown (chunked if > 3000 words) to Claude Sonnet with this structured prompt:

> "You are an LCA (Life Cycle Assessment) expert validator. Review the following extracted LCA document content and assess:
> 1. Are impact category names consistent with EF 3.1 (Environmental Footprint 3.1) or ReCiPe 2016 taxonomy? List any unrecognised category names.
> 2. Are there any conflicts between documents in this job? (If multiple documents are provided, compare their functional units, system boundaries, and impact method.)
> 3. Are numeric values plausible for the apparent product system and industry? Flag any values that seem implausibly high or low.
> 4. Rate the overall data quality: Excellent / Good / Fair / Poor.
> Return your response as a JSON object with keys: `taxonomy_issues` (list of strings), `cross_doc_conflicts` (list of strings), `plausibility_flags` (list of strings), `data_quality_rating` (string), `confidence_score` (0.0–1.0)."

### Validation Report Schema (`ValidationReport`)
```
file_id                  str
status                   str       — passed | passed_with_warnings | failed
rule_errors              List[str]
rule_warnings            List[str]
taxonomy_issues          List[str]
cross_doc_conflicts      List[str]
plausibility_flags       List[str]
data_quality_rating      str       — Excellent | Good | Fair | Poor
llm_confidence_score     float
```

### Quarantine Logic
If `status == failed` AND `rule_errors` contains critical errors (missing functional unit across all docs, or all impact values have unrecognised units), mark the file as `status: QUARANTINED` in DynamoDB. Quarantined files are excluded from synthesis unless the API is called with `force_include_quarantined: True`.

---

## 14. Backend — Phase 6: Synthesis Agent

### Responsibility
Produce the final unified LCA analysis from all validated parsed outputs. Three sequential stages, each calling Claude Sonnet.

### Stage 1 — Per-Document Summaries (`per_doc_summarizer.py`)

For each non-quarantined `ParsedOutput`, send the Markdown to Claude Sonnet with a prompt asking for a structured 300–500 word summary covering:
- What document this is (type, apparent purpose)
- What LCA data it contains (which impact categories, functional unit if identified, system boundary if stated)
- Data quality assessment based on the validation report
- Any red flags or missing information
- Key numeric findings (up to 5 most significant values)

Format the summary as Markdown with sub-headings: `### Document Overview`, `### LCA Content`, `### Data Quality`, `### Key Findings`, `### Flags`.

### Stage 2 — Cross-Document Synthesis (`cross_doc_synthesizer.py`)

Send all Stage 1 summaries together to Claude Sonnet with a long-context prompt that asks the model to:
- Identify which documents cover which life cycle stages (A1–C)
- Detect any conflicts (different functional units, conflicting impact values for the same process)
- Identify complementary data (documents that together cover a complete cradle-to-grave scope)
- Assess overall methodological consistency (is the same impact assessment method used throughout?)
- Write a unified narrative that describes the complete LCA study covered by all documents

The output is a Markdown document with sections: `## Study Overview`, `## Functional Unit`, `## System Boundary`, `## Coverage by Life Cycle Stage`, `## Methodological Consistency`, `## Conflicts and Discrepancies`, `## Cross-Document Synthesis`.

### Stage 3 — LCA-Specific Insight Extraction (`insight_extractor.py`)

Send the Stage 2 synthesis to Claude Sonnet with a prompt to extract:

**Hotspot Analysis:** Which processes, materials, or life cycle stages contribute most to environmental impact? List the top 5 hotspots with estimated percentage contribution if data allows.

**Uncertainty Assessment:** Where is data quality weakest? Which results are most uncertain and why?

**Completeness Assessment:** What percentage of the product system is covered? What is missing?

**Impact Results Table:** Extract all impact category results into a single consolidated table: `| Impact Category | Value | Unit | Life Cycle Stage | Source Document |`

**Recommendations:** 3–5 specific, actionable recommendations for reducing the identified environmental hotspots.

Format the output as Markdown with sections: `## Environmental Hotspots`, `## Consolidated Impact Results`, `## Uncertainty Assessment`, `## Completeness`, `## Recommendations`.

---

## 15. Backend — Phase 7: Output Generator

### Responsibility
Assemble all synthesis outputs into the four final deliverables and store them.

### Output 1 — Markdown Report (`report_generator.py`)
Concatenate into a single Markdown document:
1. Title section: `# LCA Analysis Report`, job ID, date, list of files processed
2. Stage 2 cross-document synthesis
3. Stage 3 insights (hotspots, consolidated table, uncertainty, completeness, recommendations)
4. Per-document summaries (Stage 1) as an appendix
5. Validation results summary table
6. Metadata footer

Store to S3 at `reports/{job_id}/full_report.md`.

### Output 2 — Structured JSON (`json_exporter.py`)
Build and store a JSON object at `reports/{job_id}/analysis.json`:
```json
{
  "job_id": "...",
  "analysis_date": "ISO8601",
  "functional_unit": "1 kg product",
  "system_boundary": "cradle-to-gate",
  "impact_method": "ReCiPe 2016 H",
  "impact_results": [
    {"category": "Global Warming Potential", "value": 4.5, "unit": "kg CO2 eq", "stage": "A1-A3"}
  ],
  "hotspots": [
    {"process": "electricity consumption", "contribution_pct": 45, "impact_category": "GWP"}
  ],
  "data_quality": "Good",
  "completeness": 0.82,
  "files_processed": 5,
  "validation_summary": {"passed": 4, "warnings": 1, "failed": 0, "quarantined": 0}
}
```

### Output 3 — Visualization Data (`viz_data_builder.py`)
Build chart-ready data objects and store at `reports/{job_id}/viz_data.json`:
- `impact_bar_chart`: `{ labels: [...], values: [...], units: [...] }` — one entry per impact category
- `hotspot_pareto`: `{ labels: [...], values: [...], cumulative_pct: [...] }` — sorted descending
- `completeness_gauge`: `{ value: 0.82, label: "82% Complete" }`
- `stage_coverage_heatmap`: `{ stages: ["A1","A2","A3",...], covered: [true, true, false,...] }`
- `data_quality_scores`: `{ file_ids: [...], scores: [...], labels: [...] }`

### Output 4 — Audit Trail (`audit_logger.py`)
Store a full JSON audit log at `audit/{job_id}/audit.json`:
```json
{
  "job_id": "...",
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "total_duration_seconds": 142,
  "files": [
    {
      "file_id": "...",
      "original_name": "lca_results.xlsx",
      "agent_assigned": "excel_agent",
      "routing_reason": "Detected as Excel file with LCA columns",
      "processing_time_s": 34,
      "confidence": 0.95,
      "validation_status": "passed",
      "errors": []
    }
  ],
  "models_used": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
  "total_tokens": 823400,
  "validation_summary": {...},
  "errors": []
}
```

Finally, update the `lca-analyses` DynamoDB record: `status = COMPLETED`, store S3 paths for all four outputs.

---

## 16. REST API Layer

Build all routes in FastAPI. All routes are under `/api/v1`.

### Endpoints

**POST `/api/v1/jobs`**
- Accept: `multipart/form-data` with files + optional `user_context` JSON string
- Validate: file count (1–20), file sizes (< MAX_FILE_SIZE_MB)
- Trigger background processing via `BackgroundTasks`
- Return: `{ job_id, file_count, estimated_seconds, status: "PENDING" }`

**GET `/api/v1/jobs/{job_id}`**
- Return full job status: `{ job_id, status, progress (0–100), files: [{ file_id, name, type, agent, status, confidence }], errors }`
- Used by the frontend for polling every 3 seconds

**GET `/api/v1/jobs/{job_id}/report`**
- Return the full analysis result: `{ markdown_report, structured_json, viz_data, validation_summary, audit_summary }`
- Only available when `status == COMPLETED`
- Return 202 with `{ status: "PROCESSING" }` if still running

**GET `/api/v1/jobs/{job_id}/download/report`**
- Stream the Markdown report file from S3 as a file download
- Content-Type: `text/markdown`, Content-Disposition: `attachment; filename="lca_report_{job_id}.md"`

**GET `/api/v1/jobs/{job_id}/download/json`**
- Stream the structured JSON from S3 as a file download
- Content-Type: `application/json`

**GET `/api/v1/jobs/{job_id}/download/audit`**
- Stream the audit trail JSON from S3

**GET `/api/v1/jobs/{job_id}/logs`**
- Server-Sent Events (SSE) endpoint that streams live processing logs as events
- Event format: `data: {"timestamp": "...", "level": "INFO", "agent": "pdf_hybrid_agent", "file_id": "...", "message": "Processing page 3/42"}`
- Close the stream when `status == COMPLETED` or `FAILED`

**POST `/api/v1/jobs/{job_id}/force-include-quarantined`**
- Re-run synthesis including quarantined files
- Return: new job record or updated synthesis

**GET `/api/v1/health`**
- Return: `{ status: "ok", bedrock: "connected", s3: "connected", dynamo: "connected" }`

### Error Response Format
All error responses use:
```json
{
  "error": "VALIDATION_FAILED",
  "message": "Human-readable description",
  "details": {}
}
```

### CORS
Configure CORS to allow origins from `CORS_ORIGINS` env var. Allow methods: GET, POST. Allow headers: Content-Type, Authorization.

---

## 17. Frontend — Design & Architecture

### Design Direction
The frontend uses a **dark, precision-instrument aesthetic** — reminiscent of scientific software and environmental monitoring dashboards. The palette is deep charcoal (`#0F1117`) with off-white text (`#E8EAF0`), accents in a muted sage green (`#4CAF7D`) for positive states and amber (`#F59E0B`) for warnings. The feel is serious and data-centric, not consumer-app cheerful. Think: lab instrument meets design studio.

**Typography:** Use `IBM Plex Mono` for data values and code, `Fraunces` (from Google Fonts) for headings, and `IBM Plex Sans` for body text. These choices convey precision and environmental seriousness.

**Animations:** Use Framer Motion for page transitions (slide + fade), and CSS transitions for micro-interactions. Agent cards animate in with a staggered entrance when the processing page loads. Progress rings animate smoothly. Do not animate things that update rapidly (log streams, progress numbers) — only animate structural changes.

**Layout:** Three-column responsive grid on desktop (sidebar + main content + detail panel). Single column on mobile. The sidebar shows navigation and job history.

### Framework & Build
React 18 + TypeScript + Vite + Tailwind CSS. The Tailwind config must define the custom color palette, custom font stacks, and any custom spacing values needed.

---

## 18. Frontend — Pages & Components

### Upload Page (`UploadPage.tsx`)

This is the landing page. It must feel like a serious scientific tool, not a SaaS marketing page.

**DropZone Component:**
- Full-width drag-and-drop area with a dashed border that glows green when a file is dragged over
- Supporting text: "Drop LCA documents here — Excel, PDF, Images, Mind Maps"
- Below the drop zone, a horizontal list of supported format badges (colour-coded pills: green for Excel, blue for PDF, purple for Image, amber for Mind Map, grey for Other)
- On file drop or click-to-browse, files appear below as `FileCard` components
- Each `FileCard` shows: format icon, filename, file size, a detected format badge, and a remove button
- A text input field (optional) for "Additional Context" (e.g., "This is a cradle-to-gate study for a polyethylene product"). This maps to `user_context`.
- A prominent "Analyse Documents" submit button — disabled until at least 1 file is added

**Validation:**
- Show an inline error under any file that exceeds the size limit
- Show a toast if more than 20 files are added: "Maximum 20 files per analysis"
- Show a toast if a file type is completely unsupported (e.g., `.exe`, `.zip` that isn't a `.xmind`)

**On Submit:**
- Call `POST /api/v1/jobs` with the files
- On success, navigate to `/processing/{job_id}`
- On error, show a toast with the error message

---

### Processing Page (`ProcessingPage.tsx`)

This page shows live pipeline progress. The user watches the system work in real time.

**Layout:**
- Top: Job summary bar — number of files, estimated completion time, elapsed time counter
- Left panel: `PipelineView` — a vertical diagram of the 7 pipeline phases with live status indicators (pending / active / complete / error) for each phase
- Centre: A grid of `AgentCard` components, one per file being processed
- Right panel: `LogStream` — scrollable live log output

**PipelineView Component:**
Show the 7 phases as vertical nodes connected by lines: Ingestion → Orchestration → Agent Processing → Normalization → Validation → Synthesis → Output. Each node has a status icon (clock for pending, spinner for active, checkmark for complete, X for error). The active node pulses with a subtle animation. The connecting line fills in green as phases complete.

**AgentCard Component:**
One card per file. Shows:
- File icon (by type) and filename
- Assigned agent name (e.g., "PDF Hybrid Agent")
- `ProgressRing` — circular progress indicator with percentage
- Current action label (from the last log event for this file)
- Status badge: PENDING / PROCESSING / COMPLETED / FAILED

Cards animate in with a staggered entrance delay (50ms per card). On completion, the card border flashes green briefly.

**LogStream Component:**
- Fixed-height scrollable container (dark background, monospace font)
- Each log line shows timestamp, log level badge (INFO / WARN / ERROR), agent name, and message
- Auto-scroll to bottom as new lines arrive
- Subscribe to the SSE endpoint `GET /api/v1/jobs/{job_id}/logs`
- Show a "Paused — scroll up" indicator if the user scrolls up; auto-resume on scroll to bottom

**Polling:**
Use `useJobPolling` hook to poll `GET /api/v1/jobs/{job_id}` every 3 seconds. When `status == COMPLETED`, navigate to `/report/{job_id}` with a smooth transition. When `status == FAILED`, show an error state with details and a "Try Again" button.

---

### Report Page (`ReportPage.tsx`)

The final analysis dashboard. This is the centrepiece of the application.

**Layout:**
- Top bar: report title, date, number of files analysed, download buttons (Markdown, JSON, Audit)
- Tab navigation: "Overview" | "Impact Analysis" | "Documents" | "Validation" | "Full Report"

**Overview Tab:**
- A grid of 4 key metrics cards: Functional Unit, System Boundary, Data Quality Rating, Completeness Score
- `CompletenessGauge` — a semicircular gauge showing the completeness percentage
- `HotspotChart` — a horizontal Pareto bar chart of the top 5 environmental hotspots (process name on Y axis, percentage contribution on X axis, with a cumulative line)
- A `ValidationBadge` summary row: "4 Passed, 1 Warning, 0 Failed"

**Impact Analysis Tab:**
- `ImpactChart` — a vertical grouped bar chart with one bar per impact category. Bars are segmented by life cycle stage if stage data is available. X axis: impact categories, Y axis: numeric values, units shown in the legend.
- Below the chart: the consolidated impact results table rendered as a Markdown table with sortable columns (sort by value, by category name, by stage)
- Stage Coverage Heatmap: a grid showing which life cycle stages (A1, A2, A3, B1, etc.) are covered by the data

**Documents Tab:**
- An accordion list of `DocSummaryCard` components, one per processed file
- Each accordion header shows: file icon, filename, agent used, confidence score, validation status badge
- Expanded content shows the per-document summary Markdown rendered via `MarkdownViewer`
- A "View Raw Extracted Content" button that opens a modal with the raw extracted Markdown for that file

**Validation Tab:**
- A table: one row per file, columns: File Name | Agent | Status | Rule Errors | Rule Warnings | Taxonomy Issues | Data Quality
- Expandable rows to see full validation detail
- A job-level conflict/cross-doc analysis section at the top

**Full Report Tab:**
- The complete Markdown report rendered via `MarkdownViewer` with a table of contents sidebar generated from headings
- A floating "Copy Markdown" button
- Full-width layout with good typographic line length (max 75ch)

---

## 19. Frontend — State Management & API Integration

### Zustand Stores

**`jobStore.ts`:**
```
activeJobId         string | null
jobStatus           JobStatus | null
files               FileRecord[]
progress            number             — 0–100
logs                LogEntry[]
setActiveJob        (jobId) => void
updateStatus        (status) => void
appendLog           (entry) => void
resetJob            () => void
```

**`reportStore.ts`:**
```
report              AnalysisReport | null
isLoading           bool
error               string | null
fetchReport         (jobId) => Promise<void>
```

### API Client (`client.ts`)
Configure Axios with:
- `baseURL` from `VITE_API_BASE_URL` environment variable (e.g., `http://localhost:8000/api/v1`)
- Request interceptor: add `Content-Type: application/json` for non-multipart requests
- Response interceptor: normalise error responses to `{ error, message, details }` shape
- Timeout: 30 seconds for regular requests, 0 (no timeout) for SSE streams

### `useJobPolling` Hook
- Accepts `jobId: string`
- Polls `GET /api/v1/jobs/{jobId}` every 3000ms using `setInterval`
- Updates `jobStore` on each response
- Clears interval when `status == COMPLETED` or `FAILED`
- Cleans up interval on component unmount

### `useSSE` Hook
- Accepts `jobId: string`
- Opens `EventSource` to `/api/v1/jobs/{jobId}/logs`
- On each message, appends to `jobStore.logs`
- Closes `EventSource` on unmount or when job completes

---

## 20. Error Handling Strategy

### Backend
- Every agent node is wrapped in a try-except. On exception, append to `state['errors']` and set the file's DynamoDB status to `FAILED`. Do not re-raise — the pipeline continues with other files.
- The LangGraph graph has a global error handler node that catches any unhandled node failures. It logs the full traceback, updates the job status, and triggers the output node with whatever partial results exist.
- All Bedrock/Textract/E2B calls use the `retry` decorator from `utils/retry.py`: exponential backoff starting at 2 seconds, up to 3 retries, on `ThrottlingException`, `ServiceUnavailableException`, and network timeouts.
- S3 and DynamoDB calls: single retry after 1 second. If both fail, raise and let the agent node catch it.

### Frontend
- Every API call is wrapped in try-catch. Errors are surfaced via React Hot Toast with actionable messages ("Upload failed — check your file sizes and try again").
- If the SSE connection drops, the `useSSE` hook attempts to reconnect once after 5 seconds before giving up and falling back to polling.
- If polling returns `status == FAILED`, show a dedicated error state on the Processing Page with the error details from the API and a "Start New Analysis" button.
- Loading states: every data-fetching action sets a loading state in the relevant Zustand store. UI shows skeleton loaders or spinners during loading.

---

## 21. Testing Requirements

Write tests for the following. Use `pytest` for backend, `vitest` for frontend.

### Backend Tests

**`test_file_detector.py`:** Test that each supported file format is correctly detected from magic bytes alone (not from the file extension). Include edge cases: a PDF renamed to `.txt`, a JPEG renamed to `.pdf`.

**`test_routing_node.py`:** Test the routing logic. Mock the Bedrock client. Test that a scanned PDF is routed to `pdf_scanned_agent`, a text-only PDF to `pdf_text_agent`, an Excel file to `excel_agent`. Test the fallback rule-based routing when the LLM returns malformed JSON.

**`test_rule_validator.py`:** Test each rule check in isolation: unit recognition (valid and invalid units), negative value detection, functional unit presence check. Use synthetic Markdown inputs.

**`test_pdf_page_classifier.py`:** Test with synthetic pymupdf page objects. Test that a page with text_length=600 and no images is classified as `text_heavy`. Test that a page with image_count=3 and text_length=50 is classified as `image_heavy`.

**`test_normalizer.py`:** Test that the normaliser correctly converts each agent's raw output format to the `ParsedOutput` schema. Test edge cases: empty Markdown, Markdown tables without separator rows (verify they are fixed).

**`test_api_routes.py`:** Integration tests using FastAPI `TestClient`. Test the upload endpoint with 1 file and 20 files. Test that the job status endpoint returns 404 for unknown job IDs. Test that the report endpoint returns 202 when the job is still processing.

### Frontend Tests

**`DropZone.test.tsx`:** Test that dropping a file triggers the file list to update. Test that dropping more than 20 files shows an error toast.

**`useJobPolling.test.ts`:** Test that polling stops when status is COMPLETED. Test that the hook cleans up its interval on unmount.

**`reportStore.test.ts`:** Test that `fetchReport` populates the store on success and sets an error on failure.

---

## 22. Data Schemas — Complete Reference

### FileMetadata
```
file_id             str
job_id              str
original_name       str
s3_key              str
actual_mime         str
file_type           FileType enum
size_bytes          int
is_scanned          bool
has_text_layer      bool
has_embedded_images bool
page_count          int | None
sheet_count         int | None
complexity_score    float
status              FileStatus enum
upload_timestamp    str  (ISO8601)
agent_assigned      str | None
```

### ParsedOutput
```
file_id             str
job_id              str
agent               str
markdown            str
structured_json     Dict
lca_relevant        bool
confidence          float
low_confidence_pages  List[int]
word_count          int
processing_time_s   float
errors              List[str]
warnings            List[str]
```

### ValidationReport
```
file_id                 str
status                  ValidationStatus enum  (passed | passed_with_warnings | failed)
rule_errors             List[str]
rule_warnings           List[str]
taxonomy_issues         List[str]
cross_doc_conflicts     List[str]
plausibility_flags      List[str]
data_quality_rating     str
llm_confidence_score    float
```

### FinalOutput
```
markdown_report         str
structured_json         Dict
viz_data                Dict
per_doc_summaries       List[Dict]
processing_metadata     Dict
```

### LogEntry (Frontend)
```
timestamp           str
level               "INFO" | "WARN" | "ERROR"
agent               str
file_id             str | null
message             str
```

### AnalysisReport (Frontend)
```
job_id              str
analysis_date       str
functional_unit     str
system_boundary     str
impact_method       str
impact_results      ImpactResult[]
hotspots            Hotspot[]
data_quality        str
completeness        number
files_processed     number
validation_summary  ValidationSummary
markdown_report     str
viz_data            VizData
per_doc_summaries   DocSummary[]
```

---

## Build Order

Build in this exact sequence to avoid dependency issues:

1. `config.py`, `models/schemas.py`, `models/enums.py`
2. `storage/` layer (S3, DynamoDB, OpenSearch clients)
3. `ingestion/` layer (file detector, complexity scorer, ingestion router)
4. `processing/` layer (Bedrock, Textract, VLM, E2B clients)
5. `agents/` — start with `base_agent.py`, then `excel_agent.py`, then `pdf_agent.py`, `image_agent.py`, `mindmap_agent.py`, `generic_agent.py`
6. `normalization/` layer
7. `validation/` layer
8. `synthesis/` layer
9. `output/` layer
10. `orchestrator/` — wire the LangGraph graph using all the above
11. `main.py` — mount all FastAPI routers, configure CORS and middleware
12. Frontend — build in this order: `api/` clients → Zustand stores → hooks → components → pages
13. Tests — write alongside the corresponding backend and frontend modules
14. `docker-compose.yml`, `Dockerfile.*` — containerise everything

---

*End of specification. Build every component described. Do not omit any layer. Treat this document as the complete, authoritative design.*
