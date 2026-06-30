"""Resume retrieval and ranking logic using vector embeddings."""

import re
from typing import Optional

from services.storage.config import (
    EMBEDDING_MODEL_NAME,
    KEYWORD_WEIGHT,
    OVERFETCH_FACTOR,
    QDRANT_COLLECTION_NAME,
    QDRANT_HOST,
    QDRANT_PORT,
    VECTOR_WEIGHT,
)

try:
    from fastembed import TextEmbedding
    from qdrant_client import QdrantClient
    from qdrant_client.models import FieldCondition, Filter, MatchText, MatchValue, PointStruct

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False


class MockResumeRetriever:
    """Mock retriever for testing without Qdrant running."""

    def __init__(self):
        from services.storage.sample_resumes import SAMPLE_RESUMES

        self._candidates = SAMPLE_RESUMES

    def search(self, query: str, top_k: int = 5) -> list:
        """Return mock candidates based on query keywords."""
        query_lower = query.lower()
        scored = []

        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "when",
            "at",
            "by",
            "for",
            "from",
            "in",
            "into",
            "of",
            "off",
            "on",
            "onto",
            "out",
            "over",
            "to",
            "up",
            "with",
            "is",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "looking",
            "expertise",
        }

        synonyms = {"golang": "go", "k8s": "kubernetes", "docker": "container"}
        jd_words = [
            synonyms.get(w, w)
            for w in query_lower.replace(",", " ").split()
            if w not in stop_words and len(w) >= 2
        ]

        for idx, resume in enumerate(self._candidates):
            score = 0.5  # base
            text = (resume.get("content", "") + " " + " ".join(resume.get("skills", []))).lower()
            for word in jd_words:
                if word in text:
                    score += 0.1
            scored.append(
                {
                    "candidate_id": resume["id"],
                    "name": resume["name"],
                    "resume_text": resume["content"],
                    "skills": resume.get("skills", []),
                    "experience": resume.get("experience"),
                    "score": min(score, 1.0),
                }
            )

        return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

    def get_resume(self, resume_id: int) -> Optional[dict]:
        for r in self._candidates:
            if r["id"] == resume_id:
                return {
                    "candidate_id": r["id"],
                    "name": r["name"],
                    "resume_text": r["content"],
                    "skills": r.get("skills", []),
                    "experience": r.get("experience"),
                }
        return None

    def ingest_candidate(self, candidate: dict) -> dict:
        raise RuntimeError("Mock mode does not support ingestion")


class ResumeRetriever:
    """Handles resume retrieval, ingestion, and candidate ranking."""

    def __init__(
        self,
        collection_name=QDRANT_COLLECTION_NAME,
        host=QDRANT_HOST,
        port=QDRANT_PORT,
    ):
        self.client = QdrantClient(host=host, port=port)
        self.model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
        self.collection_name = collection_name

    def rank_candidates(
        self,
        job_description: str,
        retrieved_candidates: list,
        cutoff_layer: int = 12,
        normalize: bool = True,
    ) -> list:
        """Rank retrieved candidates against a job description."""
        if not job_description:
            raise ValueError("job_description is required")

        if not retrieved_candidates:
            return []

        query_embedding = list(self.model.embed([job_description]))[0].tolist()
        ranked_results = []

        for candidate in retrieved_candidates:
            candidate_text = candidate.get("resume_text") or candidate.get("content") or ""
            if not candidate_text:
                continue

            candidate_embedding = list(self.model.embed([candidate_text]))[0].tolist()
            score = sum(a * b for a, b in zip(query_embedding, candidate_embedding))

            ranked_results.append(
                {
                    "candidate_id": candidate.get("candidate_id") or candidate.get("id"),
                    "name": candidate.get("name"),
                    "resume_text": candidate_text,
                    "skills": candidate.get("skills", []),
                    "experience": candidate.get("experience"),
                    "score": score,
                }
            )

        ranked_results.sort(key=lambda item: item["score"], reverse=True)
        ranked_results = ranked_results[:cutoff_layer]

        if normalize and ranked_results:
            scores = [item["score"] for item in ranked_results]
            min_score = min(scores)
            max_score = max(scores)

            if max_score != min_score:
                for item in ranked_results:
                    item["score"] = (item["score"] - min_score) / (max_score - min_score)
            else:
                for item in ranked_results:
                    item["score"] = 1.0

        return ranked_results

    def search(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "vector",
        vector_weight: float = VECTOR_WEIGHT,
        keyword_weight: float = KEYWORD_WEIGHT,
    ) -> list:
        """Search resumes using the specified search type.

        Parameters
        ----------
        query : str
            The job description or query text.
        top_k : int
            Number of results to return.
        search_type : {"vector", "keyword", "hybrid"}
            Which retrieval strategy to use.
        vector_weight : float
            Weight for vector similarity score (hybrid only).
        keyword_weight : float
            Weight for keyword relevance score (hybrid only).
        """
        if search_type == "hybrid":
            return self.search_hybrid(query, top_k, vector_weight, keyword_weight)
        if search_type == "keyword":
            kw_results = self.keyword_search(query, top_k * OVERFETCH_FACTOR)
            for r in kw_results:
                r["score"] = r["keyword_score"]
            # Normalise keyword-only results for consistency.
            if kw_results:
                scores = [r["score"] for r in kw_results]
                lo, hi = min(scores), max(scores)
                for r in kw_results:
                    if hi != lo:
                        r["score"] = (r["score"] - lo) / (hi - lo)
                    else:
                        r["score"] = 0.0
            return kw_results[:top_k]

        # Default: vector search (existing behaviour).
        query_embedding = list(self.model.embed([query]))[0].tolist()
        results = self.client.query_points(
            collection_name=self.collection_name, query=query_embedding, limit=top_k
        ).points

        retrieved_candidates = []
        for result in results:
            payload = result.payload or {}
            retrieved_candidates.append(
                {
                    "candidate_id": payload.get("candidate_id", result.id),
                    "name": payload.get("name"),
                    "resume_text": payload.get("resume_text"),
                    "skills": payload.get("skills", []),
                    "experience": payload.get("experience"),
                }
            )
        return self.rank_candidates(
            job_description=query,
            retrieved_candidates=retrieved_candidates,
            cutoff_layer=top_k,
            normalize=True,
        )

    def get_resume(self, resume_id: int) -> Optional[dict]:
        """Get a specific resume by ID."""
        points = self.client.retrieve(collection_name=self.collection_name, ids=[resume_id])

        if points:
            point = points[0]
            payload = point.payload or {}
            return {
                "candidate_id": payload.get("candidate_id", point.id),
                "name": payload.get("name"),
                "resume_text": payload.get("resume_text"),
                "skills": payload.get("skills", []),
                "experience": payload.get("experience"),
            }

        return None

    def ingest_candidate(self, candidate: dict) -> dict:
        """Embed and store a single candidate profile in Qdrant."""
        candidate_text = candidate.get("resume_text") or candidate.get("content") or ""
        if not candidate_text:
            raise ValueError("candidate must include resume_text or content")

        candidate_id = candidate.get("candidate_id") or candidate.get("id")
        if candidate_id is None:
            raise ValueError("candidate must include candidate_id or id")

        embedding = list(self.model.embed([candidate_text]))[0].tolist()
        payload = {
            "candidate_id": candidate_id,
            "name": candidate.get("name"),
            "resume_text": candidate_text,
            "skills": candidate.get("skills", []),
            "experience": candidate.get("experience"),
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=candidate_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return payload

    # ------------------------------------------------------------------
    # Hybrid Search: keyword extraction, vector search, keyword search,
    # result merging, score normalisation, and weighted ranking.
    # ------------------------------------------------------------------

    @staticmethod
    def extract_keywords(text: str) -> list[str]:
        """Extract lowercase keywords from a query string."""
        if not text:
            return []
        tokens = re.findall(r"[a-zA-Z+#.]+", text.lower())
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "about",
            "and",
            "but",
            "or",
            "if",
            "while",
            "that",
            "this",
            "it",
            "its",
            "what",
            "which",
            "who",
            "whom",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "you",
            "your",
            "yours",
            "he",
            "him",
            "his",
            "she",
            "her",
            "hers",
            "they",
            "them",
            "their",
            "theirs",
        }
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def vector_search(self, query: str, top_k: int) -> list:
        """Pure vector (semantic) search returning scored candidates."""
        query_embedding = list(self.model.embed([query]))[0].tolist()
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
        ).points

        candidates = []
        for result in results:
            payload = result.payload or {}
            candidates.append(
                {
                    "candidate_id": payload.get("candidate_id", result.id),
                    "name": payload.get("name"),
                    "resume_text": payload.get("resume_text", ""),
                    "skills": payload.get("skills", []),
                    "experience": payload.get("experience"),
                    "vector_score": result.score,
                }
            )
        return candidates

    def keyword_search(self, query: str, top_k: int) -> list:
        """Keyword search over resume text and metadata using Qdrant filter."""
        keywords = self.extract_keywords(query)
        if not keywords:
            return []

        should_conditions = []
        for kw in keywords:
            should_conditions.append(
                FieldCondition(
                    key="resume_text",
                    match=MatchText(text=kw),
                )
            )
            should_conditions.append(
                FieldCondition(
                    key="skills",
                    match=MatchValue(value=kw),
                )
            )

        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=top_k,
            filter=Filter(should=should_conditions),
            with_payload=True,
        )

        candidates = []
        for point in points:
            payload = point.payload or {}
            resume_text = (payload.get("resume_text") or "").lower()
            skills = [s.lower() for s in (payload.get("skills") or [])]
            score = 0.0
            for kw in keywords:
                if kw in resume_text:
                    score += 1.0
                if any(kw in skill for skill in skills):
                    score += 2.0

            if score > 0:
                candidates.append(
                    {
                        "candidate_id": payload.get("candidate_id", point.id),
                        "name": payload.get("name"),
                        "resume_text": payload.get("resume_text", ""),
                        "skills": payload.get("skills", []),
                        "experience": payload.get("experience"),
                        "keyword_score": score,
                    }
                )

        candidates.sort(key=lambda x: x["keyword_score"], reverse=True)
        return candidates[:top_k]

    @staticmethod
    def merge_results(vector_results: list, keyword_results: list) -> list:
        """Merge vector and keyword result sets, deduplicating by candidate_id."""
        merged = {}
        for r in vector_results:
            cid = r["candidate_id"]
            merged[cid] = {
                "candidate_id": cid,
                "name": r.get("name"),
                "resume_text": r.get("resume_text", ""),
                "skills": r.get("skills", []),
                "experience": r.get("experience"),
                "vector_score": r.get("vector_score", 0.0),
                "keyword_score": 0.0,
            }

        for r in keyword_results:
            cid = r["candidate_id"]
            if cid in merged:
                merged[cid]["keyword_score"] = r.get("keyword_score", 0.0)
            else:
                merged[cid] = {
                    "candidate_id": cid,
                    "name": r.get("name"),
                    "resume_text": r.get("resume_text", ""),
                    "skills": r.get("skills", []),
                    "experience": r.get("experience"),
                    "vector_score": 0.0,
                    "keyword_score": r.get("keyword_score", 0.0),
                }

        return list(merged.values())

    @staticmethod
    def normalize_scores(
        candidates: list,
        vector_key: str = "vector_score",
        keyword_key: str = "keyword_score",
    ) -> list:
        """Min-max normalize vector and keyword scores independently.

        When all values in an arm are identical the arm provides no
        discriminative signal, so the normalised value is set to 0.0.
        """
        if not candidates:
            return candidates

        vec_scores = [c.get(vector_key, 0.0) for c in candidates]
        kw_scores = [c.get(keyword_key, 0.0) for c in candidates]

        v_min, v_max = min(vec_scores), max(vec_scores)
        k_min, k_max = min(kw_scores), max(kw_scores)

        for c in candidates:
            if v_max != v_min:
                c[vector_key] = (c.get(vector_key, 0.0) - v_min) / (v_max - v_min)
            else:
                c[vector_key] = 0.0

            if k_max != k_min:
                c[keyword_key] = (c.get(keyword_key, 0.0) - k_min) / (k_max - k_min)
            else:
                c[keyword_key] = 0.0

        return candidates

    @staticmethod
    def calculate_final_score(
        candidates: list,
        vector_weight: float = VECTOR_WEIGHT,
        keyword_weight: float = KEYWORD_WEIGHT,
    ) -> list:
        """Apply weighted scoring and sort by final score descending."""
        for c in candidates:
            c["score"] = (
                vector_weight * c.get("vector_score", 0.0)
                + keyword_weight * c.get("keyword_score", 0.0)
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = VECTOR_WEIGHT,
        keyword_weight: float = KEYWORD_WEIGHT,
    ) -> list:
        """Run hybrid search (vector + keyword), merge, normalise, rank."""
        overfetch_k = top_k * OVERFETCH_FACTOR

        vector_results = self.vector_search(query, overfetch_k)
        keyword_results = self.keyword_search(query, overfetch_k)

        merged = self.merge_results(vector_results, keyword_results)
        merged = self.normalize_scores(merged)
        merged = self.calculate_final_score(merged, vector_weight, keyword_weight)

        return merged[:top_k]