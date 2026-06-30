"""Flask application for resume retrieval API."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import Counter
from flask import Flask, jsonify, request

from services.ranking import LayerwiseCandidateReranker
from services.ranking.schemas import DashboardResponse, DashboardRequest, ScoreDistribution, SkillDistribution, ExperienceDistribution
from services.storage.qdrant_setup import setup_qdrant
from services.storage.retrieval import ResumeRetriever


app = Flask(__name__)
retriever = None
reranker = None


@app.before_request
def initialize():
    """Initialize retriever and reranker on first request."""
    global retriever, reranker
    if retriever is None:
        try:
            retriever = ResumeRetriever(mock_mode=True)
        except Exception as e:
            print(f"Error initializing retriever: {e}")
            print("Make sure Qdrant is running and setup_qdrant() has been executed.")
    if reranker is None:
        try:
            reranker = LayerwiseCandidateReranker(simulation_mode=True)
        except Exception as e:
            print(f"Error initializing reranker: {e}")


def compute_skill_distribution(candidates, top_n=15):
    skill_counts = Counter()
    for c in candidates:
        skills_raw = c.get("skills", [])
        if isinstance(skills_raw, str):
            skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]
        for skill in skills_raw:
            skill_counts[skill.title()] += 1
    return [SkillDistribution(skill=s, count=c) for s, c in skill_counts.most_common(top_n)]


def compute_score_distribution(candidates):
    bins = [
        ("0-29", "0–29%", 0.0, 0.30),
        ("30-49", "30–49%", 0.30, 0.50),
        ("50-69", "50–69%", 0.50, 0.70),
        ("70-89", "70–89%", 0.70, 0.90),
        ("90-100", "90–100%", 0.90, 1.01),
    ]
    counts = {b[0]: 0 for b in bins}
    for c in candidates:
        score = float(c.get("ai_match_score", c.get("score", 0)))
        score = max(0.0, min(1.0, score))
        pct = score * 100
        for key, _, lo, hi in bins:
            if lo <= pct < hi:
                counts[key] += 1
                break
        else:
            counts["90-100"] += 1
    total = len(candidates) or 1
    return [
        ScoreDistribution(
            range=key,
            label=label,
            count=counts[key],
            percentage=round((counts[key] / total) * 100, 1),
        )
        for key, label, _, _ in bins
    ]


def compute_experience_distribution(candidates):
    bins = [
        ("0-2", "0–2 years", 0, 3),
        ("3-5", "3–5 years", 3, 6),
        ("6-8", "6–8 years", 6, 9),
        ("9-12", "9–12 years", 9, 13),
        ("13+", "13+ years", 13, 999),
    ]
    counts = {b[0]: 0 for b in bins}
    for c in candidates:
        exp = c.get("experience")
        if exp is None:
            continue
        try:
            exp = float(exp)
        except (TypeError, ValueError):
            continue
        for key, _, lo, hi in bins:
            if lo <= exp < hi:
                counts[key] += 1
                break
        else:
            counts["13+"] += 1
    return [
        ExperienceDistribution(range=key, label=label, count=counts[key])
        for key, label, _, _ in bins
    ]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/dashboard", methods=["POST"])
def dashboard():
    global reranker, retriever
    try:
        data = request.get_json() or {}
        req = DashboardRequest.model_validate(data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    if retriever is None:
        return jsonify({"error": "Retriever not initialized. Is Qdrant running?"}), 503

    query = req.query or ""
    top_k = req.top_k or 20

    try:
        if query:
            raw_candidates = retriever.search(query, min(top_k, 50))
            job_desc = query
        else:
            raw_candidates = retriever.search("candidates", min(top_k, 50))
            job_desc = "General candidate search"

        if not raw_candidates:
            raw_candidates = retriever.search("software developer engineer", min(top_k, 50))
            job_desc = "software developer engineer"

        if not raw_candidates:
            return jsonify({"error": "No candidates found. Run /setup first."}), 404

        ranked = []
        if reranker and not reranker.simulation_mode:
            ranked = reranker.rank_candidates(
                job_description=job_desc,
                retrieved_candidates=raw_candidates,
                cutoff_layer=12,
            )
        else:
            ranked = list(raw_candidates)

        return jsonify(DashboardResponse(
            query=query or "All Candidates",
            total_candidates=len(ranked),
            skill_distribution=compute_skill_distribution(ranked),
            score_distribution=compute_score_distribution(ranked),
            experience_distribution=compute_experience_distribution(ranked),
        ).model_dump()), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard", methods=["GET"])
def dashboard_get():
    global reranker, retriever
    query = request.args.get("query", "")
    top_k = int(request.args.get("top_k", 20))

    if retriever is None:
        return jsonify({"error": "Retriever not initialized"}), 503

    try:
        if query:
            raw_candidates = retriever.search(query, min(top_k, 50))
        else:
            raw_candidates = retriever.search("candidates", min(top_k, 50))

        if not raw_candidates:
            raw_candidates = retriever.search("software developer engineer", min(top_k, 50))

        if not raw_candidates:
            return jsonify({"error": "No candidates found. Run /setup first."}), 404

        ranked = list(raw_candidates)
        return jsonify(DashboardResponse(
            query=query or "All Candidates",
            total_candidates=len(ranked),
            skill_distribution=compute_skill_distribution(ranked),
            score_distribution=compute_score_distribution(ranked),
            experience_distribution=compute_experience_distribution(ranked),
        ).model_dump()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field"}), 400

    query = data.get("query")
    top_k = int(data.get("top_k", 5))

    try:
        results = retriever.search(query, top_k)
        return jsonify({"results": results, "query": query}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ingest", methods=["POST"])
def ingest_candidate():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing request body"}), 400

    try:
        stored = retriever.ingest_candidate(data)
        return jsonify({"message": "Candidate ingested", "candidate": stored}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/resume/<int:resume_id>", methods=["GET"])
def get_resume(resume_id):
    try:
        resume = retriever.get_resume(resume_id)
        if resume:
            return jsonify(resume), 200
        return jsonify({"error": "Resume not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/setup", methods=["POST"])
def setup():
    try:
        setup_qdrant()
        return jsonify({"message": "Qdrant setup complete"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
