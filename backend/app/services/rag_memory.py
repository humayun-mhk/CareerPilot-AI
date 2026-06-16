import hashlib
from typing import Any

import numpy as np

from ..core.config import CHROMA_PATH


class FallbackEmbeddingFunction:
    def __init__(self) -> None:
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            self.model = None

    def __call__(self, input: list[str]) -> list[list[float]]:
        if self.model is not None:
            try:
                vectors = self.model.encode(input, normalize_embeddings=True)
                return vectors.tolist()
            except Exception:
                pass
        return [self._hash_embedding(text) for text in input]

    @staticmethod
    def _hash_embedding(text: str, dimensions: int = 384) -> list[float]:
        vector = np.zeros(dimensions, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % dimensions
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


class RagMemory:
    def __init__(self) -> None:
        self.available = False
        self.client = None
        self.embedding_function = FallbackEmbeddingFunction()
        self.approved_collection = None
        self.evidence_collection = None
        self.github_collection = None

    def init(self) -> None:
        try:
            import chromadb

            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self.approved_collection = self.client.get_or_create_collection(
                name="approved_content",
                embedding_function=self.embedding_function,
            )
            self.evidence_collection = self.client.get_or_create_collection(
                name="evidence_reports",
                embedding_function=self.embedding_function,
            )
            self.github_collection = self.client.get_or_create_collection(
                name="github_readme_evidence",
                embedding_function=self.embedding_function,
            )
            self.available = True
        except Exception:
            self.available = False

    def add_approved_content(
        self,
        application_id: int,
        resume_bullets: list[str],
        cover_letter: str,
        metadata: dict[str, Any],
    ) -> None:
        if not self.available or self.approved_collection is None:
            return
        documents = []
        ids = []
        metadatas = []
        for index, bullet in enumerate(resume_bullets):
            documents.append(bullet)
            ids.append(f"application-{application_id}-bullet-{index}")
            metadatas.append({**metadata, "application_id": application_id, "content_type": "resume_bullet"})
        if cover_letter:
            documents.append(cover_letter)
            ids.append(f"application-{application_id}-cover-letter")
            metadatas.append({**metadata, "application_id": application_id, "content_type": "cover_letter"})
        if documents:
            self.approved_collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def add_evidence_report(self, application_id: int, evidence_report: dict[str, Any]) -> None:
        if not self.available or self.evidence_collection is None:
            return
        documents = []
        ids = []
        metadatas = []
        for skill, details in evidence_report.items():
            evidence = details.get("evidence", [])
            documents.append(f"{skill}: {'; '.join(evidence)}")
            ids.append(f"application-{application_id}-evidence-{skill}")
            metadatas.append(
                {
                    "application_id": application_id,
                    "skill": skill,
                    "confidence": float(details.get("confidence", 0) or 0),
                    "status": details.get("status", "missing"),
                }
            )
        if documents:
            self.evidence_collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def add_github_readme_chunks(self, user_id: int, report: dict[str, Any]) -> None:
        if not self.available or self.github_collection is None:
            return
        documents = []
        ids = []
        metadatas = []
        for project in report.get("projects", []):
            repo_name = project.get("repo_name", "")
            readme_text = project.get("readme_text", "") or project.get("readme_summary", "")
            if not repo_name or not readme_text:
                continue
            chunks = [readme_text[index : index + 1200] for index in range(0, len(readme_text), 1200)]
            for chunk_index, chunk in enumerate(chunks[:4]):
                documents.append(chunk)
                ids.append(f"github-{user_id}-{repo_name}-{chunk_index}")
                metadatas.append(
                    {
                        "user_id": user_id,
                        "repo_name": repo_name,
                        "repo_url": project.get("repo_url", ""),
                        "project_type": project.get("project_type", ""),
                        "confidence": float(project.get("evidence_confidence", 0) or 0),
                    }
                )
        if documents:
            self.github_collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def retrieve_context(self, query: str, limit: int = 5) -> str:
        if not self.available or self.approved_collection is None or not query.strip():
            return ""
        try:
            results = self.approved_collection.query(query_texts=[query], n_results=limit)
            documents = results.get("documents", [[]])[0]
            return "\n".join(documents)
        except Exception:
            return ""

    def retrieve_github_context(self, query: str, limit: int = 5) -> str:
        if not self.available or self.github_collection is None or not query.strip():
            return ""
        try:
            results = self.github_collection.query(query_texts=[query], n_results=limit)
            documents = results.get("documents", [[]])[0]
            return "\n".join(documents)
        except Exception:
            return ""


rag_memory = RagMemory()
