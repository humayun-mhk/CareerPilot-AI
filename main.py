import json

from src.graph.workflow import run_careerpilot_workflow


def main() -> None:
    initial_state = {
        "resume_text": """
AI/ML Engineer with Python, FastAPI, LangChain, RAG, OpenAI, SQL, Pandas, and Streamlit experience.
Projects include a Medical Chatbot RAG system for document question answering and an AI resume analyzer.
Education: BS Computer Science.
""",
        "linkedin_text": """
AI/ML Engineer focused on Generative AI, RAG, Python, FastAPI, and LangChain.
Featured projects: Medical Chatbot RAG and CareerPilot AI.
""",
        "job_title": "Generative AI Engineer",
        "company_name": "Example AI",
        "job_link": "https://example.com/jobs/generative-ai-engineer",
        "job_description": """
We need a Generative AI Engineer to build RAG applications, LLM workflows, FastAPI services,
LangGraph agents, Docker deployments, and LLM evaluation pipelines.
""",
        "github_url": "",
        "portfolio_url": "",
        "approval_status": "approved",
        "auto_approve": True,
        "errors": [],
    }

    final_state = run_careerpilot_workflow(initial_state)
    print(json.dumps(final_state, indent=2, default=str))


if __name__ == "__main__":
    main()
