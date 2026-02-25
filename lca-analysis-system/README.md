# Lifecycle Twin: Multi-Agent LCA Analysis System

Lifecycle Twin is a state-of-the-art **Multi-Agent System (MAS)** designed to automate the ingestion, analysis, and synthesis of **Life Cycle Assessment (LCA)** data. By leveraging advanced Large Language Models (LLMs) and specialized agents, it transforms manual, time-consuming LCA processes into a streamlined, high-integrity digital workflow.

## 🚀 Key Features

- **Multi-Agent Orchestration**: Specialized agents for different file types (Excel, PDF, Images) coordinated by a central dispatcher.
- **Deep Ingestion**:
  - **Excel Agent**: Executes local sandboxed code to extract structured data from complex workbooks.
  - **PDF Agents**: Multiple strategies (Text, Scanned, Hybrid) to handle various report formats.
  - **Vision Agent**: Extracts data from charts, tables, and images using VLMs.
- **Intelligent Synthesis**: Cross-document analysis to identify hotspots, emission factors, and data gaps across multiple sources.
- **Rigorous Validation**: LLM-based taxonomy and plausibility checks combined with deterministic rule-based validation.
- **Premium UI**: Modern, responsive dashboard built with React and Tailwind CSS for visualizing analysis results and audit trails.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.12+), Pydantic, Uvicorn.
- **AI/ML**: AWS Bedrock (Llama 4 Maverick/Scout, Mistral Pixtral), LangChain/LangGraph.
- **Infrastructure**: AWS S3 (Storage), AWS DynamoDB (Metadata), Docker & Docker Compose.
- **Frontend**: React, Vite, Tailwind CSS, Shadcn UI (Lucide Icons).
- **Execution**: Local Sandbox for secure code execution during Excel parsing.

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- AWS CLI configured with appropriate credentials (Bedrock, S3, DynamoDB access)

## ⚙️ Project Structure

```text
├── lca-analysis-system/
│   ├── backend/            # FastAPI Application
│   │   ├── agents/         # Specialized AI Agent logic
│   │   ├── ingestion/      # File detection and routing
│   │   ├── models/         # Pydantic schemas and enums
│   │   ├── orchestrator/   # Graph-based workflow management
│   │   └── storage/        # AWS DynamoDB & S3 clients
│   ├── frontend/           # Vite + React Application
│   ├── docker-compose.yml  # Container orchestration
│   └── .env.example        # Environment variable template
```

## 🏃 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/krishnahn/multiagent_LCA.git
cd multiagent_LCA/lca-analysis-system
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your AWS credentials and configuration:
```bash
cp .env.example .env
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn backend.main:app --reload
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

### 5. Docker Deployment (Optional)
```bash
docker-compose up --build
```

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.

---
**Developed with ❤️ for the LCA Community.**
