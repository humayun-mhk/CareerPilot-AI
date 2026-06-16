import json
import os
import re
from typing import Iterable

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


COMMON_SKILLS = [
    "Python",
    "FastAPI",
    "Flask",
    "Django",
    "Streamlit",
    "SQL",
    "PostgreSQL",
    "SQLite",
    "MongoDB",
    "Docker",
    "Git",
    "GitHub",
    "AWS",
    "Azure",
    "GCP",
    "OpenAI",
    "Gemini",
    "Groq",
    "LangChain",
    "LangGraph",
    "LlamaIndex",
    "RAG",
    "Vector Database",
    "ChromaDB",
    "Pinecone",
    "FAISS",
    "NLP",
    "Machine Learning",
    "Deep Learning",
    "PyTorch",
    "TensorFlow",
    "Scikit-learn",
    "Pandas",
    "NumPy",
    "REST API",
    "React",
    "JavaScript",
    "TypeScript",
    "Agentic AI",
    "LLM Evaluation",
    "Prompt Engineering",
    "Embeddings",
]


SKILL_ALIASES = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sqlite": "SQLite",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "github": "GitHub",
    "git hub": "GitHub",
    "amazon web services": "AWS",
    "aws": "AWS",
    "azure": "Azure",
    "google cloud": "GCP",
    "gcp": "GCP",
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "langchain": "LangChain",
    "lang graph": "LangGraph",
    "langgraph": "LangGraph",
    "llamaindex": "LlamaIndex",
    "llama index": "LlamaIndex",
    "retrieval augmented generation": "RAG",
    "rag": "RAG",
    "vector db": "Vector Database",
    "vector database": "Vector Database",
    "chromadb": "ChromaDB",
    "chroma": "ChromaDB",
    "pinecone": "Pinecone",
    "faiss": "FAISS",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "rest api": "REST API",
    "restful api": "REST API",
    "react": "React",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "agentic ai": "Agentic AI",
    "llm evaluation": "LLM Evaluation",
    "prompt engineering": "Prompt Engineering",
    "embeddings": "Embeddings",
}


def _dedupe_preserve_order(skills: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for skill in skills:
        cleaned = str(skill).strip()
        if not cleaned:
            continue

        canonical = _canonicalize_skill(cleaned)
        key = canonical.lower()
        if key not in seen:
            seen.add(key)
            result.append(canonical)

    return result


def _canonicalize_skill(skill: str) -> str:
    normalized = re.sub(r"\s+", " ", skill.strip()).lower()
    return SKILL_ALIASES.get(normalized, skill.strip())


def _extract_json_list(content: str) -> list[str]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if isinstance(parsed, dict):
        parsed = parsed.get("skills", [])

    if not isinstance(parsed, list):
        return []

    return _dedupe_preserve_order(str(item) for item in parsed)


def _extract_skills_with_llm(text: str, text_type: str) -> list[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    allowed_skills = ", ".join(COMMON_SKILLS)
    prompt = f"""
Extract the relevant technical and AI skills from this {text_type}.

Return only a JSON array of skill names. Prefer canonical names from this list:
{allowed_skills}

Include clearly stated equivalent skills even if wording differs.

{text_type.title()}:
\"\"\"
{text[:12000]}
\"\"\"
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "You extract concise technical skill names and return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "[]"
    skills = _extract_json_list(content)
    if not skills:
        raise RuntimeError("LLM returned no parseable skills.")
    return skills


def fallback_skill_extraction(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []

    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-z0-9+#.-])" + re.escape(skill.lower()) + r"(?![a-z0-9+#.-])"
        if re.search(pattern, lowered):
            found.append(skill)

    for alias, canonical in SKILL_ALIASES.items():
        pattern = r"(?<![a-z0-9+#.-])" + re.escape(alias) + r"(?![a-z0-9+#.-])"
        if re.search(pattern, lowered):
            found.append(canonical)

    return _dedupe_preserve_order(found)


def _extract_skills(text: str, text_type: str) -> list[str]:
    if not text or not text.strip():
        return []

    try:
        return _extract_skills_with_llm(text, text_type)
    except Exception:
        return fallback_skill_extraction(text)


def extract_job_skills(job_description: str) -> list[str]:
    return _extract_skills(job_description, "job description")


def extract_resume_skills(resume_text: str) -> list[str]:
    return _extract_skills(resume_text, "resume")
