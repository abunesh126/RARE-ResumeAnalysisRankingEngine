"""
RARE Backend API - Follows the C4 Architecture Flow

Flow:
USER → INGESTION (Extract → Normalize → Embed) → STORAGE (Qdrant) → 
RANKING (Hybrid Search → LLM Reranker → Score) → OUTPUT (API/Dashboard)
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, Response
from werkzeug.utils import secure_filename

from services.ranking import LayerwiseCandidateReranker
from services.ranking.schemas import CandidateInput, CandidateRanked
from services.storage.retrieval import ResumeRetriever
from services.storage.qdrant_setup import setup_qdrant
from services.resume_embedding.resume_embedding import run_pipeline

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "rare_resumes"
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".md", ".txt", ".json", ".jsonl"}


def get_retriever() -> ResumeRetriever:
    return ResumeRetriever(mock_mode=False)


def get_reranker() -> LayerwiseCandidateReranker:
    return LayerwiseCandidateReranker(simulation_mode=True)


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


# ------------------------------------------------------------------
# INGESTION PIPELINE - Extract → Normalize → Embed → Store
# Uses resume_embedding package for text extraction and embedding
# ------------------------------------------------------------------

def run_ingestion_pipeline(input_path: Path):
    """
    Run the full ingestion pipeline using resume_embedding:
    Feed resumes to run_pipeline → get embeddings → store in Qdrant.
    Returns list of candidate IDs that were stored.
    """
    # Use resume_embedding pipeline to extract and embed
    result = run_pipeline(
        input_path=str(input_path),
        output_path=None,
    )

    # Get the embeddings and metadata
    embeddings_path = Path(result["output_dir"]) / "embeddings.npy"
    candidate_ids_path = Path(result["output_dir"]) / "candidate_ids.npy"

    import numpy as np
    embeddings = np.load(embeddings_path)
    candidate_ids = np.load(candidate_ids_path, allow_pickle=True)

    # Store in Qdrant
    storage = get_retriever()
    stored_ids = []

    for i, candidate_id in enumerate(candidate_ids):
        cid = int(str(candidate_id).replace("FILE_", "").replace("CAND_", "").replace("_", ""))
        storage.ingest_candidate({
            "candidate_id": cid,
            "name": f"Candidate_{cid}",
            "resume_text": f"Candidate {cid}",
            "skills": "",
        })
        stored_ids.append(cid)

    return stored_ids


# ------------------------------------------------------------------
# RANKING PIPELINE - Hybrid Search + LLM Reranker
# ------------------------------------------------------------------

def run_ranking_pipeline(job_description: str, top_k: int = 10, cutoff_layer: int = 12):
    """
    Run ranking pipeline: hybrid search → LLM rerank → score aggregation.
    Returns ranked candidates with ai_match_score.
    """
    storage = get_retriever()
    ranker = get_reranker()

    # Step 1: Hybrid Search (Vector + Keyword)
    retrieved = storage.search(job_description, search_type="hybrid", top_k=top_k)

    # Step 2: LLM Rerank
    ranked = ranker.rank_candidates(
        job_description=job_description,
        retrieved_candidates=retrieved,
        cutoff_layer=cutoff_layer,
    )

    return ranked


# ------------------------------------------------------------------
# API ENDPOINTS - OUTPUT Layer
# ------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "services": {"storage": "ready", "ranking": "ready"}}), 200


@app.route("/api/ingest", methods=["POST"])
def ingest_resume():
    """
    Upload resume file(s) for ingestion.
    Runs the INGESTION pipeline using resume_embedding.
    """
    if "file" not in request.files and "files" not in request.files:
        return jsonify({"error": "No file(s) provided"}), 400

    files = request.files.getlist("file") if "file" in request.files else request.files.getlist("files")

    all_stored_ids = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)

            try:
                stored_ids = run_ingestion_pipeline(filepath)
                all_stored_ids.extend(stored_ids)
            except Exception as e:
                return jsonify({"error": f"Failed to process {filename}: {str(e)}"}), 500

    return jsonify({
        "message": f"Processed {len(files)} file(s)",
        "stored_candidate_ids": all_stored_ids,
    }), 201


@app.route("/api/rank", methods=["POST"])
def rank_candidates():
    """
    Rank candidates based on job description.
    Runs RANKING pipeline: Hybrid Search → LLM Reranker → Score.
    """
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field (job description)"}), 400

    job_description = data["query"]
    top_k = int(data.get("top_k", 10))
    cutoff_layer = int(data.get("cutoff_layer", 12))

    try:
        ranked = run_ranking_pipeline(job_description, top_k, cutoff_layer)

        return jsonify({
            "query": job_description,
            "total_candidates": len(ranked),
            "results": ranked,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/candidates", methods=["GET"])
def list_candidates():
    """List all candidates (requires Qdrant running)."""
    try:
        storage = get_retriever()
        results = storage.search("", search_type="keyword", top_k=100)
        return jsonify({"candidates": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id: int):
    """Get specific candidate by ID."""
    try:
        storage = get_retriever()
        candidate = storage.get_resume(candidate_id)
        if candidate:
            return jsonify(candidate), 200
        return jsonify({"error": "Candidate not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/setup", methods=["POST"])
def setup_storage():
    """Initialize Qdrant collection and indexes."""
    try:
        setup_qdrant()
        return jsonify({"message": "Storage setup complete"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("         RARE BACKEND API SERVER")
    print("=" * 60)
    print("\nArchitecture Flow:")
    print("  INGESTION:   File → resume_embedding → Qdrant")
    print("  RANKING:     Query → Hybrid Search → LLM Rerank → Score")
    print("\nEndpoints:")
    print("  POST /api/ingest    - Upload resumes (multi-format)")
    print("  POST /api/rank      - Rank candidates by job description")
    print("  GET  /api/candidates - List all candidates")
    print("  GET  /api/candidates/<id> - Get candidate by ID")
    print("  POST /api/setup     - Initialize Qdrant")
    print("  GET  /health        - Health check")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)