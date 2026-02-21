# Project Summary — LCA Multi-Agent Analysis System

**Project Overview**
- Purpose: Multi-agent document analysis system for Life Cycle Assessment (LCA) files. It ingests heterogeneous documents (Excel, PDF, images, mindmaps), routes each file to a specialist agent, extracts structured LCA data, validates against LCA taxonomies/rules, synthesizes cross-document findings, and produces Markdown and JSON reports.
- Location: All source is under the `lca-analysis-system` folder in this workspace.

**What I built (high-level layers)**
- Backend (FastAPI) — complete implementation of ingestion, processing, agents, normalization, validation, synthesis, output, and orchestration.
- Frontend (React + TypeScript + Vite + Tailwind) — SPA with Upload, Processing and Report pages plus UI components and state management (Zustand).
- Dev tooling — `requirements.txt`, `.env.example`, Dockerfiles, and `docker-compose.yml` for a local stack including DynamoDB Local and LocalStack for S3.

**Backend — major modules and purpose**
- `backend/config.py`: Pydantic settings loader for AWS, Bedrock, Textract, E2B, S3, DynamoDB, OpenSearch and runtime configs (CORS, max sizes).
- `backend/main.py`: FastAPI app, routes for job creation, job status, report download, logs (SSE), health endpoint and startup/shutdown hooks.
- `backend/models/enums.py` and `backend/models/schemas.py`: Enums and Pydantic models for file metadata, job status, analysis records, validation reports, and API responses.
- `backend/storage/*`: S3 client, DynamoDB client, OpenSearch client (indexing/search helpers).
- `backend/utils/*`: Logging (`structlog`), retry decorator, chunking helpers.
- `backend/ingestion/*`: File detection (`file_detector.py`), complexity scoring, ClamAV scanning wrapper, and the ingestion router which accepts multipart uploads and schedules pipeline execution.
- `backend/processing/*`: Bedrock client wrappers, Vision-LM (VLM) client, Textract integration for PDF OCR/tables, E2B sandbox runner for code-based Excel analysis, PDF page classifier.
- `backend/agents/*`: Agent implementations per file type (ExcelAgent, PDFAgent variants, ImageAgent, MindmapAgent, GenericAgent) with safe processing wrappers and retries.
- `backend/normalization/*`: Markdown conversion and normalization pipeline to produce consistent Markdown sections/tables for downstream steps.
- `backend/validation/*`: Rule-based validator, LCA taxonomy reference (EF/ReCiPe basics), and LLM-based validators for ambiguous checks.
- `backend/synthesis/*`: Per-document summarizer, cross-document synthesizer and structured insight extractor producing both Markdown and JSON outputs.
- `backend/output/*`: Report generator (Markdown), JSON exporter, visualization data builder (chart-ready payloads), and audit logger.
- `backend/orchestrator/*`: Router and dispatcher mapping files to agents, LangGraph pipeline graph (routing → agent_processing → normalization → validation → synthesis → output), and pipeline runner.

**Frontend — main files and components**
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js` — project config and dependencies.
- `frontend/src/api/client.ts` — Axios client and typed API helpers: `createJob`, `getJobStatus`, `getJobReport`, `getLogsSSEUrl`, download URL helpers.
- `frontend/src/store/jobStore.ts` and `frontend/src/store/reportStore.ts` — Zustand stores for job state, logs (capped), and report payload.
- `frontend/src/hooks/useJobPolling.ts` — polls the backend `GET /jobs/{id}` status every 3s and auto-navigates on completion/failure.
- Pages:
  - `frontend/src/pages/UploadPage.tsx` — drag+drop uploader, file list (`DropZone`, `FileCard`), context textarea, starts analysis job.
  - `frontend/src/pages/ProcessingPage.tsx` — pipeline view, per-file `AgentCard`s with progress ring, live SSE `LogStream` view.
  - `frontend/src/pages/ReportPage.tsx` — 5-tab report (Overview, Impact, Documents, Validation, Full Report) with charts and Markdown viewer.
- Components: `Layout`, `DropZone`, `FileCard`, `PipelineView`, `AgentCard`, `LogStream`, `ProgressRing`, `ImpactChart`, `HotspotChart`, `CompletenessGauge`, `MarkdownViewer`, `DocSummaryCard`, `ValidationTable`.

**Config & Environment**
- Example env file: [lca-analysis-system/.env.example](lca-analysis-system/.env.example). Copy it to `.env` and populate credentials.
- For local development without AWS services, set `MOCK_AWS=true` in `.env`.

**Docker & Localstack**
- `Dockerfile.backend` — Python 3.11 base, installs system deps (clamav, pandoc), installs Python deps from `requirements.txt`, runs `uvicorn backend.main:app`.
- `Dockerfile.frontend` — builds the Vite app and serves via Nginx.
- `docker-compose.yml` — brings up `backend`, `frontend`, `dynamodb-local`, and `localstack` (S3). Use `docker compose up --build`.

**Run instructions (development)**
- Ensure Python venv is activated and requirements are installed:

```powershell
# from repository root
cd "lca-analysis-system"
# activate venv (example)
..\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: set MOCK_AWS=true for local dev unless you have AWS/BEDROCK/E2B credentials
```

- Run backend (dev reload):

```powershell
cd lca-analysis-system
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- Run frontend (dev server):

```bash
cd lca-analysis-system/frontend
npm run dev
# open http://localhost:5173
```

**Run instructions (Docker)**

```bash
cd lca-analysis-system
docker compose up --build
# frontend: http://localhost:3000
# backend health: http://localhost:8000/health
```

**Quick test flow**
1. Open the frontend URL, upload a small Excel/PDF, provide optional context and click "Analyse Documents".
2. Watch the Processing page for per-file progress and live logs.
3. When complete, open the Report page and download the Markdown/JSON/Audit outputs.

**Testing & Validation**
- There are no automated test suites added yet. Recommended next steps: add unit tests for core backend modules (ingestion router, agent wrappers, validation rules) with pytest and small fixtures.

**Known issues, notes and recommendations**
- Large repo size: Many `frontend/node_modules` files were committed and pushed to the remote. Your `.gitignore` currently contains `/node_modules` which ignores only top-level `node_modules` and not nested ones (i.e., `lca-analysis-system/frontend/node_modules`).
  - Recommended fix (I can run this):

```powershell
# from repo root
# update .gitignore to include frontend/node_modules
# then remove tracked files and commit
git rm -r --cached lca-analysis-system/frontend/node_modules
git rm -r --cached lca-analysis-system/frontend/dist
git add .gitignore
git commit -m "chore: remove tracked node_modules and update .gitignore"
git push origin main
```

  - If you want to shrink repository history (purge node_modules from past commits), use `git filter-repo` or BFG — note this rewrites history and collaborators will need to re-clone.

- Kluster automated review: Found one medium issue (unbounded frontend log growth). I fixed it by capping logs to 2000 entries in the Zustand store and the SSE `LogStream` handler. Files changed:
  - `lca-analysis-system/frontend/src/store/jobStore.ts` (added `MAX_LOG_ENTRIES` cap in `appendLog`)
  - `lca-analysis-system/frontend/src/components/processing/LogStream.tsx` (added `MAX_DISPLAY_LOGS` cap while appending SSE logs)

- Bedrock / E2B / Textract: These integrations are implemented as clients/wrappers but require real credentials to operate. Use `MOCK_AWS=true` for local development or provide real values in `.env`.

**Next recommended tasks (prioritized)**
- Remove `node_modules` from Git and update `.gitignore` (high). I can handle this now if you confirm.
- Add basic pytest tests for the ingestion and agent dispatch (medium).
- Add CI pipeline (GitHub Actions) to run lint, tests, and kluster verification on PRs (medium).
- Add simple seeded sample documents and an end-to-end integration test that runs in mock mode (medium).

**Files of interest (quick links)**
- Backend entry: [lca-analysis-system/backend/main.py](lca-analysis-system/backend/main.py)
- Ingestion router: [lca-analysis-system/backend/ingestion/router.py](lca-analysis-system/backend/ingestion/router.py)
- Agent registry / dispatcher: [lca-analysis-system/backend/orchestrator/dispatcher.py](lca-analysis-system/backend/orchestrator/dispatcher.py)
- Synthesis: [lca-analysis-system/backend/synthesis/synthesis_agent.py](lca-analysis-system/backend/synthesis/synthesis_agent.py)
- Frontend entry: [lca-analysis-system/frontend/src/main.tsx](lca-analysis-system/frontend/src/main.tsx)
- Upload page: [lca-analysis-system/frontend/src/pages/UploadPage.tsx](lca-analysis-system/frontend/src/pages/UploadPage.tsx)
- Processing page: [lca-analysis-system/frontend/src/pages/ProcessingPage.tsx](lca-analysis-system/frontend/src/pages/ProcessingPage.tsx)
- Report page: [lca-analysis-system/frontend/src/pages/ReportPage.tsx](lca-analysis-system/frontend/src/pages/ReportPage.tsx)

---

If you want, I can now:
- A) Run the `.gitignore` cleanup and remove tracked `frontend/node_modules` (safe, quick),
- B) Also rewrite history to purge node_modules (requires confirmation), or
- C) Add a minimal `pytest` suite and GitHub Actions workflow.

Tell me which action to take next and I will proceed. 
