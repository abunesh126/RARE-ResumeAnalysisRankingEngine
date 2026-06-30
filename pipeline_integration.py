"""End-to-end pipeline: Resume → Vector → Qdrant → Similarity Search → BAAI Rerank."""

import time
from services.ranking import LayerwiseCandidateReranker
from services.storage.retrieval import ResumeRetriever


def transform_qdrant_results(results: list[dict]) -> list[dict]:
    """Transform Qdrant search results to CandidateInput format for reranker."""
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


def explain_ranking(job_description: str, candidate: dict) -> list[str]:
    """Generate skill match explanations for why a candidate ranked where they did."""
    jd_lower = job_description.lower()
    skills_text = candidate.get("skills", "")
    resume_text = candidate.get("resume_text", "").lower()
    
    synonyms = {
        "golang": "go", "k8s": "kubernetes", "k8": "kubernetes",
        "docker": "container", "containers": "container",
    }
    
    jd_words = jd_lower.replace(",", " ").replace(".", " ").split()
    jd_words = [synonyms.get(w, w) for w in jd_words if len(w) >= 2 and w not in {"a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto", "out", "over", "to", "up", "with", "is", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "looking", "expertise"}]
    
    matches = []
    for word in jd_words:
        if word in skills_text.lower():
            matches.append(f"{word.title()} (skill)")
        elif word in resume_text:
            matches.append(f"{word.title()} (in resume)")
    
    seen = set()
    unique_matches = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique_matches.append(m)
    
    return unique_matches[:5]


def run_e2e_pipeline(
    job_description: str,
    top_k: int = 10,
    cutoff_layer: int = 12,
    mock_mode: bool = True,
    simulation_mode: bool = True,
):
    """Run the complete pipeline from Qdrant retrieval to BAAI reranking."""
    retriever = ResumeRetriever(mock_mode=mock_mode)
    
    print(f"\n[INPUT] Job Description: '{job_description}'")
    
    print(f"\n[STEP 1] Similarity search (top_k={top_k})...")
    retrieved = retriever.search(job_description, top_k=top_k)
    print(f"[INFO] Retrieved {len(retrieved)} candidates from {'Qdrant' if not mock_mode else 'Mock DB'}")
    
    print(f"\n[STEP 2] Reranking with BAAI layerwise model (cutoff_layer={cutoff_layer})...")
    candidates = transform_qdrant_results(retrieved)
    
    reranker = LayerwiseCandidateReranker(simulation_mode=simulation_mode)
    ranked = reranker.rank_candidates(
        job_description=job_description,
        retrieved_candidates=candidates,
        cutoff_layer=cutoff_layer,
    )
    
    return ranked


def main():
    print("=" * 70)
    print("              ATS END-TO-END PIPELINE DEMONSTRATION")
    print("=" * 70)
    
    job_desc = "Looking for a Go Backend Developer with Kubernetes expertise."
    
    start_time = time.perf_counter()
    ranked_candidates = run_e2e_pipeline(
        job_description=job_desc,
        top_k=5,
        cutoff_layer=12,
        mock_mode=True,
    )
    elapsed = time.perf_counter() - start_time
    
    print("\n" + "=" * 70)
    print("                   FINAL RANKED SHORTLIST")
    print("=" * 70)
    
    for rank, candidate in enumerate(ranked_candidates, start=1):
        skills = candidate.get("skills", [])
        skills_str = ", ".join(skills) if isinstance(skills, list) else skills
        
        print(f"\nRank {rank}: {candidate.get('name', 'Unknown')} (ID: {candidate.get('id')})")
        print(f"  AI Match Score : {candidate['ai_match_score']:.4f}")
        print(f"  Vector Score   : {candidate.get('vector_score', 0):.4f}")
        print(f"  Core Skills    : {skills_str}")
        summary = candidate.get('resume_text', '')
        print(f"  Summary        : {summary[:70] if len(summary) > 70 else summary}...")
        
        explanations = explain_ranking(job_desc, candidate)
        if explanations:
            print(f"  🔍 Match Reasons : {', '.join(explanations)}")
    
    print(f"\n[INFO] Pipeline completed in {elapsed:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()