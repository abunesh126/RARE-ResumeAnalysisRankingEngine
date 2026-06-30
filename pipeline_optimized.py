"""Optimized pipeline with caching, parallel processing, and warmup."""

import asyncio
import concurrent.futures
import statistics
import time
from functools import lru_cache
from typing import Any, List, Optional

from services.ranking import LayerwiseCandidateReranker


class _MockRetriever:
    """Self-contained mock retriever that doesn't depend on external packages."""
    def __init__(self):
        self._candidates = _SAMPLE_RESUMES

    def search(self, query: str, top_k: int = 5) -> list:
        query_lower = query.lower()
        stop_words = {"a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
                      "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto",
                      "out", "over", "to", "up", "with", "is", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did", "looking", "expertise"}
        synonyms = {"golang": "go", "k8s": "kubernetes", "docker": "container"}
        jd_words = [synonyms.get(w, w) for w in query_lower.replace(",", " ").split()
                    if w not in stop_words and len(w) >= 2]
        scored = []
        for resume in self._candidates:
            score = 0.5
            text = (resume.get("content", "") + " " + " ".join(resume.get("skills", []))).lower()
            for word in jd_words:
                if word in text:
                    score += 0.1
            scored.append({
                "candidate_id": resume["id"],
                "name": resume["name"],
                "resume_text": resume["content"],
                "skills": resume.get("skills", []),
                "experience": resume.get("experience"),
                "score": min(score, 1.0),
            })
        return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

_SAMPLE_RESUMES = [
    {"id": 1, "name": "Alice", "skills": ["Go", "Docker", "Kubernetes", "Microservices"],
     "content": "Built cloud backend systems with Go and Kubernetes. Automated Docker build containers.",
     "experience": [{"role": "Backend Engineer", "years": 3}]},
    {"id": 2, "name": "Bob", "skills": ["React", "CSS", "HTML", "TypeScript"],
     "content": "Frontend designer portfolio containing clean pixel-perfect components using Tailwind, React and HTML.",
     "experience": [{"role": "Frontend Developer", "years": 2}]},
    {"id": 3, "name": "Charlie", "skills": ["Python", "Django", "AWS", "Kubernetes"],
     "content": "Backend engineer with experience in Django, PostgreSQL and Docker. Managed some AWS EKS services.",
     "experience": [{"role": "Backend Engineer", "years": 4}]},
    {"id": 4, "name": "Diana", "skills": ["TensorFlow", "Python", "ML", "Data Science"],
     "content": "Data scientist building ML models with TensorFlow and PyTorch. Experience in NLP and computer vision.",
     "experience": [{"role": "Data Scientist", "years": 3}]},
    {"id": 5, "name": "Eve", "skills": ["Node.js", "React", "Express", "MongoDB"],
     "content": "Full stack developer with Node.js backend and React frontend experience. Built several MERN applications.",
     "experience": [{"role": "Full Stack Developer", "years": 5}]},
]


def transform_qdrant_results(results: list[dict]) -> list[dict]:
    """Transform Qdrant search results to CandidateInput format."""
    candidates = []
    for r in results:
        skills = r.get("skills", [])
        skills_str = ", ".join(skills) if isinstance(skills, list) else skills
        candidates.append({
            "id": r.get("candidate_id", r.get("id")),
            "name": r.get("name"),
            "skills": skills_str,
            "resume_text": r.get("resume_text", ""),
            "vector_score": r.get("score", 0.0),
        })
    return candidates


@lru_cache(maxsize=32)
def _cached_jd_words(job_description: str) -> tuple:
    stop_words = {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto",
        "out", "over", "to", "up", "with", "is", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "looking", "expertise",
    }
    synonyms = {
        "golang": "go", "k8s": "kubernetes", "k8": "kubernetes",
        "docker": "container", "containers": "container",
    }
    jd_lower = job_description.lower().replace(",", " ").replace(".", " ")
    words = []
    for w in jd_lower.split():
        wm = synonyms.get(w, w)
        if len(wm) >= 2 and wm not in stop_words:
            words.append(wm)
    return tuple(words)


def explain_ranking(job_description: str, candidate: dict) -> list[str]:
    """Generate skill match explanations (with cached JD word parsing)."""
    jd_words = _cached_jd_words(job_description)
    skills_text = candidate.get("skills", "").lower()
    resume_text = candidate.get("resume_text", "").lower()

    synonyms = {
        "golang": "go", "k8s": "kubernetes", "k8": "kubernetes",
        "docker": "container", "containers": "container",
    }

    seen = set()
    matches = []
    for word in jd_words:
        mapped_skill = synonyms.get(word, word)
        if mapped_skill in skills_text and mapped_skill not in seen:
            seen.add(mapped_skill)
            matches.append(f"{word.title()} (skill)")
        elif word in resume_text and word not in seen:
            seen.add(word)
            matches.append(f"{word.title()} (in resume)")
        if len(matches) >= 5:
            break
    return matches


def explain_candidates_parallel(
    job_description: str,
    candidates: list[dict],
    max_workers: Optional[int] = None,
) -> list[list[str]]:
    """Compute explain_ranking for all candidates in parallel."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(
            lambda c: explain_ranking(job_description, c),
            candidates,
        ))


class OptimizedPipeline:
    """Latency-optimized pipeline with caching, warmup, and parallel explain."""

    def __init__(
        self,
        reranker: Optional[LayerwiseCandidateReranker] = None,
        retriever=None,
        mock_mode: bool = True,
        simulation_mode: bool = True,
        batch_size: int = 0,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
    ):
        self.reranker = reranker or LayerwiseCandidateReranker(
            simulation_mode=simulation_mode,
            batch_size=batch_size,
            load_in_8bit=load_in_8bit,
            load_in_4bit=load_in_4bit,
        )
        if retriever is not None:
            self.retriever = retriever
        elif mock_mode:
            self.retriever = _MockRetriever()
        else:
            try:
                from services.storage.retrieval import ResumeRetriever
                self.retriever = ResumeRetriever(mock_mode=False)
            except ImportError:
                print("[WARNING] Qdrant storage unavailable; falling back to mock retriever.")
                self.retriever = _MockRetriever()

    def warmup(self, job_description: str = "", top_k: int = 1):
        """Warm up the cache and model by running a single mini-batch."""
        if not job_description:
            job_description = "warmup query"
        dummy = [{
            "id": 0,
            "name": "warmup",
            "skills": "warmup",
            "resume_text": "warmup candidate for model initialization.",
        }]
        _ = self.reranker.rank_candidates(job_description, dummy, cutoff_layer=8)
        print("[INFO] Pipeline warmed up.")

    def run(
        self,
        job_description: str,
        top_k: int = 10,
        cutoff_layer: int = 12,
        explain: bool = False,
        parallel_explain: bool = True,
    ) -> dict:
        """Run the full pipeline with optional parallel explain.

        Returns dict with 'ranked' (list) and optionally 'explanations' (list of lists).
        """
        start = time.perf_counter()

        retrieved = self.retriever.search(job_description, top_k=top_k)
        candidates = transform_qdrant_results(retrieved)

        ranked = self.reranker.rank_candidates(
            job_description=job_description,
            retrieved_candidates=candidates,
            cutoff_layer=cutoff_layer,
        )

        elapsed = time.perf_counter() - start

        result = {
            "ranked": ranked,
            "elapsed": elapsed,
            "count": len(ranked),
        }

        if explain:
            if parallel_explain and len(ranked) > 1:
                result["explanations"] = explain_candidates_parallel(job_description, ranked)
            else:
                result["explanations"] = [explain_ranking(job_description, c) for c in ranked]

        return result

    def clear_cache(self):
        self.reranker.clear_cache()

    @staticmethod
    def tune(
        n_candidates: int = 100,
        candidate_generator=None,
        simulation_mode: bool = True,
    ) -> dict:
        """Auto-tune batch_size and cutoff_layer for best latency.

        Runs a sweep and returns the configuration with lowest avg latency.
        """
        if candidate_generator is None:
            from services.ranking.schemas import CandidateInput

            def _gen():
                import random
                random.seed(42)
                for i in range(n_candidates):
                    skills = random.sample(
                        ["Go", "Python", "Kubernetes", "Docker", "React", "AWS",
                         "TensorFlow", "ML", "Node.js", "PostgreSQL", "Java", "C++"],
                        k=random.randint(2, 5),
                    )
                    yield {
                        "id": i,
                        "name": f"Cand_{i}",
                        "skills": ", ".join(skills),
                        "resume_text": " ".join([f"exp_{j}" for j in range(random.randint(20, 80))]),
                    }
            candidate_generator = _gen

        jd = "Generic software engineer role requiring Go, Kubernetes, and AWS."

        candidates = list(candidate_generator())

        results = []

        batch_sizes = [0, 8, 16, 32, 64] if not simulation_mode else [0]
        cutoff_layers = [8, 12, 20, 32] if not simulation_mode else [12]

        for bs in batch_sizes:
            for cl in cutoff_layers:
                r = LayerwiseCandidateReranker(simulation_mode=simulation_mode, batch_size=bs)
                times = []
                for _ in range(10):
                    r.clear_cache()
                    start = time.perf_counter()
                    r.rank_candidates(jd, candidates, cutoff_layer=cl)
                    times.append(time.perf_counter() - start)
                avg = statistics.mean(times) * 1000
                results.append({"batch_size": bs, "cutoff_layer": cl, "avg_ms": avg})
                print(f"  batch={bs:>2}  cutoff={cl:>2}  -> {avg:.3f}ms")

        best = min(results, key=lambda x: x["avg_ms"])
        print(f"\n  [BEST] batch_size={best['batch_size']}, cutoff_layer={best['cutoff_layer']} ({best['avg_ms']:.3f}ms)")
        return best


class AsyncOptimizedPipeline:
    """Async pipeline — runs retrieval and reranking off the event loop.

    Supports concurrent execution of multiple job descriptions.
    """

    def __init__(self, *args, **kwargs):
        self._sync = OptimizedPipeline(*args, **kwargs)

    @property
    def reranker(self):
        return self._sync.reranker

    async def warmup(self, job_description: str = ""):
        await asyncio.to_thread(self._sync.warmup, job_description)

    async def run(
        self,
        job_description: str,
        top_k: int = 10,
        cutoff_layer: int = 12,
        explain: bool = False,
    ) -> dict:
        """Run pipeline asynchronously (non-blocking to event loop)."""
        return await asyncio.to_thread(
            self._sync.run,
            job_description=job_description,
            top_k=top_k,
            cutoff_layer=cutoff_layer,
            explain=explain,
            parallel_explain=True,
        )

    async def run_many(
        self,
        queries: list[tuple[str, int, int]],
        max_concurrency: int = 4,
    ) -> list[dict]:
        """Run multiple JD queries concurrently.

        Each item in queries is (job_description, top_k, cutoff_layer).
        """
        sem = asyncio.Semaphore(max_concurrency)

        async def _run_one(jd: str, top_k: int, cl: int):
            async with sem:
                return await self.run(jd, top_k=top_k, cutoff_layer=cl)

        tasks = [_run_one(jd, tk, cl) for jd, tk, cl in queries]
        return await asyncio.gather(*tasks)

    def clear_cache(self):
        self._sync.clear_cache()
