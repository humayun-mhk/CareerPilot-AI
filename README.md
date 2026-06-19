# CareerPilot AI

Live Demo: https://careerpilot-ai-frontend-h9kh.onrender.com/

CareerPilot AI is a full-stack multi-agent career assistant that analyzes a resume, LinkedIn profile, and job description, then produces evidence-aware career assets for a target role.

## Pitch

CareerPilot AI helps candidates understand how well they match a job, improve their resume honestly, prepare a better LinkedIn profile, and track each application from analysis to follow-up.

## Problem Statement

Job seekers often rewrite resumes and cover letters manually without knowing which claims are supported by evidence. This creates weak applications, missing keywords, and sometimes exaggerated claims. CareerPilot AI turns resume, LinkedIn, job, GitHub, and portfolio evidence into structured recommendations with human approval before saving.

## Features

- Resume PDF upload
- LinkedIn PDF upload or pasted LinkedIn text
- Job title, company, link, and description input
- LangGraph multi-agent workflow
- Evidence-aware skill verification
- Skill gap and match scoring
- Tailored resume bullets
- Cover letter generation
- Portfolio project recommendations
- Human approval before saving
- SQLite application tracker
- ChromaDB memory for approved content and evidence
- Analytics and evidence graph APIs
- Fallback logic when `OPENAI_API_KEY` is missing

## Architecture

- Frontend: React JS with Vite
- Backend: FastAPI
- Workflow: LangGraph using the existing Step 2 agents in `src/agents`
- Database: SQLite at `database/careerpilot.db`
- Vector memory: ChromaDB at `database/chroma`
- PDF parsing: PyMuPDF
- LLM: OpenAI through LangChain when configured, fallback logic otherwise
- Deployment: Render

## Agents

1. Document Parser
2. Resume Analyzer Agent
3. LinkedIn Optimizer Agent
4. Job Research Agent
5. Evidence Verification Agent
6. Skill Gap Agent
7. Resume Tailoring Agent
8. Project Recommender Agent
9. Cover Letter Agent
10. Human Approval
11. Application Tracker

## Database Schema

`applications`

- `id`
- `company_name`
- `job_title`
- `job_link`
- `job_description`
- `match_score`
- `status`
- `follow_up_date`
- `approved_resume_bullets`
- `approved_cover_letter`
- `created_at`
- `updated_at`

`agent_runs`

- `id`
- `application_id`
- `step_name`
- `input_json`
- `output_json`
- `created_at`

`evidence_reports`

- `id`
- `application_id`
- `skill_name`
- `evidence_json`
- `confidence`
- `status`
- `created_at`

`analysis_runs`

- `id`
- `input_json`
- `output_json`
- `approval_status`
- `application_id`
- `created_at`
- `updated_at`

## RAG Memory

ChromaDB stores approved resume bullets, cover letters, and evidence reports. Future analyses retrieve relevant approved content by job title and job description and inject that context into the LangGraph state as `rag_context`.

Embedding behavior:

- First tries SentenceTransformers with `all-MiniLM-L6-v2`
- Falls back to deterministic hash embeddings if SentenceTransformers is unavailable
- Does not require an OpenAI API key for embeddings

## API Endpoints

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/analysis/{analysis_id}`
- `POST /api/approvals/{analysis_id}`
- `GET /api/applications`
- `PATCH /api/applications/{application_id}/status`
- `GET /api/analytics`
- `GET /api/evidence-graph`
- `GET /api/memory/search`

## Frontend Pages

- `/analyze` - upload files and run analysis
- `/approval/:analysisId` - review, edit, approve, or reject generated content
- `/tracker` - view applications and update status
- `/analytics` - view application metrics
- `/evidence` - view evidence graph data

## Setup

```powershell
cd f:\Agentic_AI\Resume\careerpilot-ai
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Optional `.env`:

```env
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_PATH=database/careerpilot.db
CHROMA_PATH=database/chroma
```

## Run Commands

Backend:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Deployment

CareerPilot AI is deployed on Render.

For Render deployments, the backend entrypoint is:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Set the Render environment variables from `.env.example`, including `OPENAI_API_KEY` if LLM-powered generation is needed. The app still supports fallback mode when `OPENAI_API_KEY` is not configured.

## Future Improvements

- User authentication
- Real LinkedIn OAuth import
- Rich visual graph rendering
- Background jobs for long analyses
- More advanced RAG memory filters
- Export to PDF and DOCX
- Render monitoring, CI/CD, and production observability
