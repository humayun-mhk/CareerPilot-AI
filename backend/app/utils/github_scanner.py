import base64
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

import requests


GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "CareerPilotAI/4.0"}

SKILL_KEYWORDS: dict[str, list[str]] = {
    "Python": ["python", "fastapi", "flask", "pandas", "numpy", "scikit", "sklearn"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "React": ["react", "vite", "jsx", "frontend"],
    "Flutter": ["flutter", "dart"],
    "Firebase": ["firebase", "firestore", "firebase auth", "firebase storage"],
    "RAG": ["rag", "retrieval augmented", "retrieval-augmented", "vector database"],
    "LangChain": ["langchain"],
    "LangGraph": ["langgraph"],
    "LLM": ["llm", "openai", "gemini", "groq", "bedrock", "large language model"],
    "AI Agents": ["agent", "agents", "multi-agent", "agentic"],
    "ChromaDB": ["chromadb", "chroma"],
    "FAISS": ["faiss"],
    "Pinecone": ["pinecone"],
    "Docker": ["docker", "container"],
    "AWS": ["aws", "sagemaker", "ec2", "ecr", "bedrock", "cloudfront"],
    "SQL": ["sql", "sqlite", "postgres", "mysql"],
    "Computer Vision": ["opencv", "yolo", "facenet", "mtcnn", "vision", "image"],
    "NLP": ["nlp", "bert", "t5", "lstm", "text classification", "summarization"],
    "MLOps": ["mlops", "pipeline", "deployment", "monitoring", "ci/cd", "github actions"],
    "Automation": ["automation", "n8n", "workflow", "zapier"],
}

PROJECT_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("RAG Application", ["rag", "retrieval", "vector", "pinecone", "chromadb", "faiss"]),
    ("Agentic AI System", ["agent", "langgraph", "crew", "multi-agent"]),
    ("Computer Vision System", ["opencv", "yolo", "vision", "face", "image"]),
    ("Full-Stack Mobile Application", ["flutter", "firebase", "mobile", "android", "ios"]),
    ("MLOps Pipeline", ["sagemaker", "mlops", "pipeline", "deployment", "docker"]),
    ("NLP Application", ["nlp", "bert", "t5", "lstm", "summarization"]),
    ("Automation Workflow", ["n8n", "automation", "workflow"]),
    ("Full-Stack Web Application", ["react", "fastapi", "flask", "frontend", "backend"]),
]


def normalize_github_username(github_input: str) -> str:
    value = (github_input or "").strip()
    if not value:
        return ""
    if value.startswith("@"):
        return value[1:]
    if "github.com" in value:
        parsed = urlparse(value if value.startswith(("http://", "https://")) else f"https://{value}")
        parts = [part for part in parsed.path.split("/") if part]
        return parts[0] if parts else ""
    return value.rstrip("/")


def _request_json(url: str) -> Any:
    response = requests.get(url, headers=HEADERS, timeout=12)
    response.raise_for_status()
    return response.json()


def fetch_user_repositories(username: str) -> list[dict[str, Any]]:
    if not username:
        return []
    repos = _request_json(f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated")
    if not isinstance(repos, list):
        return []
    return [
        repo
        for repo in repos
        if not repo.get("fork") and not repo.get("archived")
    ]


def fetch_repo_readme(owner: str, repo_name: str) -> str:
    try:
        payload = _request_json(f"{GITHUB_API}/repos/{owner}/{repo_name}/readme")
        encoded = payload.get("content", "")
        if not encoded:
            return ""
        return base64.b64decode(encoded, validate=False).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def detect_repo_skills(repo_name: str, readme_text: str) -> list[str]:
    text = f"{repo_name}\n{readme_text}".lower()
    skills = []
    for skill, keywords in SKILL_KEYWORDS.items():
        if any(re.search(rf"(?<![a-z0-9+#.-]){re.escape(keyword)}(?![a-z0-9+#.-])", text) for keyword in keywords):
            skills.append(skill)
    return skills


def detect_project_type(repo_name: str, readme_text: str, detected_skills: list[str]) -> str:
    text = f"{repo_name}\n{readme_text}\n{' '.join(detected_skills)}".lower()
    for project_type, keywords in PROJECT_TYPE_RULES:
        if any(keyword in text for keyword in keywords):
            return project_type
    return "AI / Software Project" if detected_skills else "Software Project"


def summarize_readme(repo_name: str, readme_text: str, detected_skills: list[str]) -> str:
    clean = " ".join((readme_text or "").replace("#", " ").split())
    if clean:
        return clean[:260] + ("..." if len(clean) > 260 else "")
    skills = ", ".join(detected_skills[:5]) or "software engineering"
    return f"{repo_name} appears to demonstrate {skills} based on repository metadata."


def calculate_repo_evidence_confidence(detected_skills: list[str], readme_text: str) -> float:
    if not detected_skills:
        return 0.1
    confidence = 0.28 + min(len(detected_skills), 8) * 0.07
    lower = (readme_text or "").lower()
    if len(readme_text) > 500:
        confidence += 0.12
    if any(word in lower for word in ["installation", "usage", "architecture", "features", "api", "deployment"]):
        confidence += 0.12
    if any(word in lower for word in ["docker", "deploy", "production", "tests", "github actions"]):
        confidence += 0.08
    return round(max(0.1, min(confidence, 0.95)), 2)


def scan_github_evidence(github_input: str) -> dict[str, Any]:
    username = normalize_github_username(github_input)
    if not username:
        return {
            "username": "",
            "repositories_scanned": 0,
            "projects": [],
            "skill_evidence_summary": {},
            "errors": ["GitHub username or profile URL is required."],
        }

    errors: list[str] = []
    try:
        repositories = fetch_user_repositories(username)
    except Exception as exc:
        return {
            "username": username,
            "repositories_scanned": 0,
            "projects": [],
            "skill_evidence_summary": {},
            "errors": [f"Unable to fetch repositories: {exc}"],
        }

    projects: list[dict[str, Any]] = []
    skill_repos: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for repo in repositories:
        repo_name = repo.get("name", "")
        readme = fetch_repo_readme(username, repo_name)
        detected_skills = detect_repo_skills(repo_name, readme)
        confidence = calculate_repo_evidence_confidence(detected_skills, readme)
        project_type = detect_project_type(repo_name, readme, detected_skills)
        project = {
            "repo_name": repo_name,
            "repo_url": repo.get("html_url", f"https://github.com/{username}/{repo_name}"),
            "detected_skills": detected_skills,
            "project_type": project_type,
            "readme_summary": summarize_readme(repo_name, readme, detected_skills),
            "readme_text": readme[:5000],
            "evidence_confidence": confidence,
            "stars": int(repo.get("stargazers_count", 0) or 0),
            "language": repo.get("language") or "",
            "updated_at": repo.get("updated_at") or "",
        }
        projects.append(project)
        for skill in detected_skills:
            skill_repos[skill].append((repo_name, confidence))

    skill_evidence_summary = {}
    for skill, repo_scores in skill_repos.items():
        confidence = sum(score for _, score in repo_scores) / max(len(repo_scores), 1)
        confidence = min(0.97, confidence + min(len(repo_scores), 4) * 0.03)
        skill_evidence_summary[skill] = {
            "repos": [repo for repo, _ in repo_scores],
            "confidence": round(confidence, 2),
        }

    return {
        "username": username,
        "repositories_scanned": len(projects),
        "projects": projects,
        "skill_evidence_summary": dict(sorted(skill_evidence_summary.items())),
        "errors": errors,
    }
