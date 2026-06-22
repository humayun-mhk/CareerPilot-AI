# CareerPilot AI

Live Demo: https://careerpilot-ai-frontend-h9kh.onrender.com/

Backend API: https://careerpilot-ai-api.onrender.com/api

CareerPilot AI is a full-stack AI career assistant that analyzes a resume, LinkedIn profile, GitHub evidence, portfolio context, and job description. It helps users understand job fit, improve career documents, verify claims with evidence, and track applications.

## Pitch

CareerPilot AI helps candidates understand how well they match a job, improve their resume honestly, prepare a better LinkedIn profile, and track each application from analysis to follow-up.

## Problem Statement

Job seekers often rewrite resumes and cover letters manually without knowing which claims are supported by evidence. This creates weak applications, missing keywords, and sometimes exaggerated claims. CareerPilot AI turns resume, LinkedIn, job, GitHub, and portfolio evidence into structured recommendations with human approval before saving.

## Features

- Resume PDF upload
- LinkedIn PDF upload or pasted LinkedIn text
- Job title, company, link, and description input
- LangGraph multi-agent workflow
- GitHub evidence scanner
- Evidence-aware skill verification
- Skill gap and match scoring
- Tailored resume bullets
- Resume versioning and exports
- Cover letter generation
- Portfolio project recommendations
- Human approval before saving
- Application tracker
- ChromaDB memory for approved content and evidence
- Evaluation report
- Agent tracing
- Analytics and evidence graph
- Fallback logic when `OPENAI_API_KEY` is missing

## Architecture

- Frontend: React JS with Vite
- Backend: FastAPI
- Workflow: LangGraph multi-agent orchestration
- Production database: Neon PostgreSQL through `DATABASE_URL`
- Local database fallback: SQLite only when `DATABASE_URL` is not set
- Vector memory: ChromaDB at `database/chroma`
- PDF parsing: PyMuPDF and pdfplumber
- LLM: OpenAI through LangChain when configured, fallback logic otherwise
- Embeddings: hash fallback by default, optional SentenceTransformers
- Deployment: Render

## Agents

The backend uses LangGraph to pass one shared state through multiple agents. Each agent adds a focused result to the state and sends it to the next step.

Workflow:

```text
Document Parser
-> Resume Analyzer
-> LinkedIn Optimizer
-> GitHub Evidence Scanner
-> Job Research
-> Skill Gap
-> Evidence Verification
-> Resume Tailoring
-> Project Recommender
-> Cover Letter
-> Evaluation
-> Human Approval
-> Application Tracker
```

| Agent | Responsibility |
|---|---|
| Document Parser | Reads uploaded resume and LinkedIn files, cleans text, and prepares workflow input. |
| Resume Analyzer Agent | Extracts resume skills, projects, experience, education, weak points, and resume strength. |
| LinkedIn Optimizer Agent | Suggests LinkedIn headline, About section, skill order, and profile improvements. |
| GitHub Evidence Agent | Scans GitHub evidence and identifies projects, skills, README details, and proof signals. |
| Job Research Agent | Extracts job skills, tools, responsibilities, seniority, job category, and ATS keywords. |
| Skill Gap Agent | Compares job requirements against candidate evidence and calculates gaps. |
| Evidence Verification Agent | Checks whether resume and skill claims are supported by resume, LinkedIn, GitHub, or portfolio evidence. |
| Resume Tailoring Agent | Creates honest, ATS-friendly resume bullets using supported evidence only. |
| Project Recommender Agent | Recommends portfolio projects for missing or weak skills. |
| Cover Letter Agent | Generates a job-specific cover letter using verified strengths. |
| Evaluation Agent | Reviews generated outputs for quality, evidence use, and improvement score. |
| Human Approval Agent | Holds sensitive content for user review before saving or export. |
| Application Tracker Agent | Saves approved application data, match score, status, and follow-up information. |

## Database

Production uses Neon PostgreSQL. The backend reads the production database connection from `DATABASE_URL`.

SQLite is only a local development fallback when `DATABASE_URL` is not set. In production, `ENVIRONMENT=production` requires a PostgreSQL/Neon URL.

Main tables:

- `applications`
- `agent_runs`
- `evidence_reports`
- `analysis_runs`
- `github_evidence_scans`
- `github_repository_evidence`
- `resume_versions`
- `resume_exports`
- `evaluation_reports`
- `agent_traces`
- `approval_items`

Alembic is included for database migrations.

## RAG Memory

CareerPilot AI uses ChromaDB for vector memory.

Stored memory includes:

- Approved resume bullets
- Approved cover letters
- Evidence reports
- GitHub README evidence chunks

The app can retrieve relevant memory and add it to the LangGraph state for future analysis.

Embedding behavior:

- `EMBEDDING_PROVIDER=hash` is the default production-safe fallback
- SentenceTransformers can be used when configured
- OpenAI embeddings are not required for fallback mode

## API Endpoints

Important backend endpoints:

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/analysis/{analysis_id}`
- `POST /api/approvals/{analysis_id}`
- `GET /api/applications`
- `PATCH /api/applications/{application_id}/status`
- `GET /api/analytics`
- `GET /api/evidence-graph`
- `GET /api/memory/search`
- `POST /api/github/scan`
- `GET /api/resume-versions/{user_id}`
- `GET /api/resume-versions/detail/{version_id}`
- `POST /api/resume-versions/compare`
- `POST /api/resume-versions/export`
- `GET /api/evaluations/{user_id}`
- `GET /api/evaluations/detail/{evaluation_id}`
- `GET /api/traces/{user_id}`
- `GET /api/traces/run/{graph_run_id}`
- `GET /api/approvals/pending/{user_id}`
- `GET /api/approvals/history/{user_id}`
- `POST /api/approvals/approve`
- `POST /api/approvals/reject`
- `POST /api/approvals/regenerate`
- `GET /api/deployment/status`

## Frontend Pages

- `/dashboard` - main starting point
- `/upload` - upload resume and LinkedIn files
- `/analyze` - submit job details and run the workflow
- `/match-report` - view match score and skill gaps
- `/resume-suggestions` - view tailored resume bullets
- `/linkedin-optimizer` - view LinkedIn recommendations
- `/github-scanner` - scan GitHub evidence
- `/project-recommendations` - view suggested portfolio projects
- `/cover-letter` - view generated cover letter
- `/resume-versioning` - track resume versions, approvals, exports, and comparisons
- `/approval/:analysisId` - review one generated analysis
- `/approval-center` - approve, reject, or request regeneration
- `/tracker` - track job applications and statuses
- `/analytics` - view metrics
- `/evidence` - view evidence graph data
- `/evaluation-report` - view evaluation results
- `/agent-tracing` - inspect workflow traces
- `/deployment-status` - view backend, frontend, database, and vector-memory status

## Application Tracker vs Resume Versioning

Application Tracker and Resume Versioning are related, but they are not the same feature.

Application Tracker manages job applications. It tracks company, role, job link, match score, status, and follow-up information.

Resume Versioning manages generated resumes. It tracks which resume version was created for which job, score changes, approval status, exports, and version comparisons.

In simple words:

- Use Application Tracker to manage jobs.
- Use Resume Versioning to manage tailored resumes.

## Environment Variables

Backend environment:

```env
PROJECT_NAME=CareerPilot AI API
ENVIRONMENT=production
DATABASE_URL=postgresql://your_neon_connection_url
JWT_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
EMBEDDING_PROVIDER=hash
CHROMA_PATH=database/chroma
CORS_ORIGINS=https://careerpilot-ai-frontend-h9kh.onrender.com,http://localhost:5173
```

Frontend environment:

```env
VITE_API_BASE_URL=https://careerpilot-ai-api.onrender.com/api
```

`OPENAI_API_KEY` is optional. If it is missing, the project uses fallback logic for skill extraction, scoring, and generated placeholder content.

## Local Setup

```powershell
cd f:\Agentic_AI\Resume\careerpilot-ai
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Run backend from the project root:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

Or run backend from inside the `backend` folder:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Install and run frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Local backend health check:

```text
http://localhost:8000/api/health
```

## Deployment

CareerPilot AI is deployed on Render. Render reads `render.yaml`.

Backend Render service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Backend details:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Health check path: `/api/health`
- Production database: Neon PostgreSQL through `DATABASE_URL`

Frontend Render service:

```bash
npm ci && npm run build
```

Frontend details:

- Root directory: `frontend`
- Publish directory: `dist`
- API URL: `VITE_API_BASE_URL=https://careerpilot-ai-api.onrender.com/api`

## Future Improvements

- User authentication
- Real LinkedIn OAuth import
- Rich visual graph rendering
- Background jobs for long analyses
- More advanced RAG memory filters
- Export to PDF and DOCX
- Render monitoring, CI/CD, and production observability
