"""Benchmark script for the end-to-end pipeline."""

import time
import statistics
from pipeline_integration import run_e2e_pipeline, transform_qdrant_results, explain_ranking
from services.storage.retrieval import ResumeRetriever


def benchmark_pipeline(
    job_descriptions: list[str],
    iterations: int = 5,
    top_k: int = 5,
    cutoff_layer: int = 12,
):
    """Run benchmark across multiple job descriptions."""
    
    results = {}
    
    for jd in job_descriptions:
        times = []
        
        for i in range(iterations):
            start = time.perf_counter()
            ranked = run_e2e_pipeline(
                job_description=jd,
                top_k=top_k,
                cutoff_layer=cutoff_layer,
                mock_mode=True,
                simulation_mode=True,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        results[jd] = {
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "ranked": ranked[:3] if 'ranked' in dir() else [],
        }
    
    return results


def main():
    print("=" * 70)
    print("              PIPELINE BENCHMARK")
    print("=" * 70)
    
    job_descriptions = [
        "Looking for a Go Backend Developer with Kubernetes expertise.",
        "Need a Python Data Scientist with TensorFlow and ML experience.",
        "Seeking Full Stack Developer with React and Node.js skills.",
        "Hiring DevOps Engineer with Kubernetes and AWS experience.",
    ]
    
    print(f"\n[INFO] Running {len(job_descriptions)} queries x 5 iterations each...\n")
    
    results = benchmark_pipeline(job_descriptions, iterations=5, top_k=5, cutoff_layer=12)
    
    print("\n" + "=" * 70)
    print("                   BENCHMARK RESULTS")
    print("=" * 70)
    
    all_times = []
    for jd, data in results.items():
        print(f"\nQuery: '{jd[:50]}...'")
        print(f"  Avg Time: {data['avg_time']*1000:.2f}ms")
        print(f"  Min/Max:  {data['min_time']*1000:.2f}ms / {data['max_time']*1000:.2f}ms")
        all_times.append(data['avg_time'])
    
    print(f"\n" + "-" * 70)
    print(f"Overall Average Pipeline Time: {statistics.mean(all_times)*1000:.2f}ms")
    
    # Detailed output for one query
    print("\n" + "=" * 70)
    print("                   SAMPLE OUTPUT (Go Developer)")
    print("=" * 70)
    
    ranked = run_e2e_pipeline(
        job_description="Looking for a Go Backend Developer with Kubernetes expertise.",
        top_k=5,
        cutoff_layer=12,
        mock_mode=True,
        simulation_mode=True,
    )
    
    for rank, candidate in enumerate(ranked, start=1):
        skills = candidate.get("skills", "")
        summary = candidate.get('resume_text', '')
        
        print(f"\nRank {rank}: {candidate.get('name', 'Unknown')} (ID: {candidate.get('id')})")
        print(f"  AI Match Score : {candidate['ai_match_score']:.4f}")
        print(f"  Core Skills    : {skills}")
        print(f"  Summary        : {summary[:100]}{'...' if len(summary) > 100 else ''}")
        
        explanations = explain_ranking("Looking for a Go Backend Developer with Kubernetes expertise.", candidate)
        if explanations:
            print(f"  🔍 Match Reasons : {', '.join(explanations)}")


if __name__ == "__main__":
    main()