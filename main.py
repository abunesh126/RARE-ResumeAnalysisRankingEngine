"""
RARE Backend API - Follows the C4 Architecture Flow

Flow:
USER → INGESTION (Extract → Normalize → Embed) → STORAGE (Qdrant) → 
RANKING (Hybrid Search → LLM Reranker → Score) → OUTPUT (API/Dashboard)
"""

import csv
import io
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, Response
from werkzeug.utils import secure_filename

from services.ranking import LayerwiseCandidateReranker
from services.ranking.schemas import (
    CandidateInput,
    CandidateRanked,
    DashboardRequest,
    DashboardResponse,
    SkillDistribution,
    ScoreDistribution,
    ExperienceDistribution,
)


app = Flask(__name__)

# CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/health", methods=["OPTIONS"])
def health_options():
    return "", 204


# Configuration
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "rare_resumes"
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".md", ".txt", ".json", ".jsonl"}


def _qdrant_available() -> bool:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.exceptions import UnexpectedResponse
        client = QdrantClient(host="localhost", port=6333)
        client.get_collection("_health_check_")
        return True
    except Exception:
        return False


_AUTO_INGESTING = False


def auto_ingest_existing_resumes(storage):
    from services.storage.retrieval import MockResumeRetriever
    from services.resume_embedding.resume_embedding.app.pipeline import run_pipeline
    try:
        for filepath in UPLOAD_FOLDER.iterdir():
            if filepath.is_file() and allowed_file(filepath.name):
                filename = secure_filename(filepath.name)
                candidate_id_str = f"FILE_{Path(filename).stem.replace(' ', '_')}"
                clean_id_str = candidate_id_str.replace("FILE_", "").replace("CAND_", "").replace("_", "")
                try:
                    cid = int(clean_id_str)
                except ValueError:
                    import hashlib
                    h = hashlib.sha256(candidate_id_str.encode('utf-8')).hexdigest()
                    cid = 1000000 + (int(h, 16) % 9000000)
                
                # Check if already present
                if isinstance(storage, MockResumeRetriever):
                    exists = any(r["id"] == cid for r in storage._candidates)
                else:
                    exists = False
                    try:
                        exists = storage.get_resume(cid) is not None
                    except Exception:
                        pass
                
                if not exists:
                    # Run ingestion pipeline directly
                    result = run_pipeline(
                        input_path=str(filepath),
                        output_path=None,
                    )
                    embeddings_path = Path(result["output_dir"]) / "embeddings.npy"
                    candidate_ids_path = Path(result["output_dir"]) / "candidate_ids.npy"
                    import numpy as np
                    embeddings = np.load(embeddings_path)
                    candidate_ids = np.load(candidate_ids_path, allow_pickle=True)
                    
                    # Extract text using dispatcher
                    from services.resume_embedding.resume_embedding.app.input import dispatch
                    extracted_texts = {}
                    try:
                        for candidate_id, text in dispatch(filepath, skip_invalid=True):
                            extracted_texts[str(candidate_id)] = text
                    except Exception:
                        pass
                        
                    for i, cand_id in enumerate(candidate_ids):
                        cand_id_str = str(cand_id)
                        c_clean = cand_id_str.replace("FILE_", "").replace("CAND_", "").replace("_", "")
                        try:
                            c_cid = int(c_clean)
                        except ValueError:
                            import hashlib
                            h_c = hashlib.sha256(cand_id_str.encode('utf-8')).hexdigest()
                            c_cid = 1000000 + (int(h_c, 16) % 9000000)
                            
                        resume_text = extracted_texts.get(cand_id_str, f"Candidate {cand_id_str}")
                        name = cand_id_str.replace("FILE_", "").replace("_", " ")
                        
                        # Skill extraction
                        import re
                        common_skills = [
                            "Python", "FastAPI", "PyTorch", "ONNX", "Embeddings", "Pydantic", 
                            "Qdrant", "Docker", "Golang", "Go", "FAISS", "OpenSearch", "Milvus", 
                            "Weaviate", "Pinecone", "Elasticsearch", "Machine Learning", "ML", 
                            "Search", "Ranking", "Retrieval", "NLP", "C++", "Java", "AWS", "GCP", 
                            "Kubernetes", "SQL", "Git"
                        ]
                        matched_skills = []
                        text_lower = resume_text.lower()
                        for skill in common_skills:
                            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                            if re.search(pattern, text_lower):
                                matched_skills.append(skill)
                        skills_str = ", ".join(matched_skills[:5])
                        
                        storage.ingest_candidate({
                            "candidate_id": c_cid,
                            "name": name,
                            "resume_text": resume_text,
                            "skills": skills_str,
                        })
    except Exception as e:
        print(f"[WARNING] Auto-ingestion failed: {e}")


def get_retriever():
    global _AUTO_INGESTING
    from services.storage.retrieval import ResumeRetriever, MockResumeRetriever
    if _qdrant_available():
        storage = ResumeRetriever()
    else:
        storage = MockResumeRetriever()
        
    if not _AUTO_INGESTING:
        _AUTO_INGESTING = True
        try:
            auto_ingest_existing_resumes(storage)
        finally:
            _AUTO_INGESTING = False
            
    return storage


def get_reranker():
    return LayerwiseCandidateReranker(simulation_mode=True)


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


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
        ("0-29", "0-29%", 0.0, 0.30),
        ("30-49", "30-49%", 0.30, 0.50),
        ("50-69", "50-69%", 0.50, 0.70),
        ("70-89", "70-89%", 0.70, 0.90),
        ("90-100", "90-100%", 0.90, 1.01),
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
        ("0-2", "0-2 years", 0, 3),
        ("3-5", "3-5 years", 3, 6),
        ("6-8", "6-8 years", 6, 9),
        ("9-12", "9-12 years", 9, 13),
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
    from services.resume_embedding.resume_embedding.app.pipeline import run_pipeline
    # Run the dispatcher on the input path to extract the actual texts
    from services.resume_embedding.resume_embedding.app.input import dispatch
    extracted_texts = {}
    try:
        for candidate_id, text in dispatch(input_path, skip_invalid=True):
            extracted_texts[str(candidate_id)] = text
    except Exception as e:
        print(f"Error during text extraction: {e}")

    result = run_pipeline(
        input_path=str(input_path),
        output_path=None,
    )

    embeddings_path = Path(result["output_dir"]) / "embeddings.npy"
    candidate_ids_path = Path(result["output_dir"]) / "candidate_ids.npy"

    import numpy as np
    embeddings = np.load(embeddings_path)
    candidate_ids = np.load(candidate_ids_path, allow_pickle=True)

    storage = get_retriever()
    stored_ids = []

    for i, candidate_id in enumerate(candidate_ids):
        candidate_id_str = str(candidate_id)
        clean_id_str = candidate_id_str.replace("FILE_", "").replace("CAND_", "").replace("_", "")
        try:
            cid = int(clean_id_str)
        except ValueError:
            import hashlib
            # Compute a deterministic 7-digit integer hash for non-numeric filenames
            h = hashlib.sha256(candidate_id_str.encode('utf-8')).hexdigest()
            cid = 1000000 + (int(h, 16) % 9000000)
            
        resume_text = extracted_texts.get(candidate_id_str, f"Candidate {candidate_id_str}")
        name = candidate_id_str.replace("FILE_", "").replace("_", " ")
        
        # Simple skill extraction helper
        import re
        common_skills = [
            "Python", "FastAPI", "PyTorch", "ONNX", "Embeddings", "Pydantic", 
            "Qdrant", "Docker", "Golang", "Go", "FAISS", "OpenSearch", "Milvus", 
            "Weaviate", "Pinecone", "Elasticsearch", "Machine Learning", "ML", 
            "Search", "Ranking", "Retrieval", "NLP", "C++", "Java", "AWS", "GCP", 
            "Kubernetes", "SQL", "Git"
        ]
        matched_skills = []
        text_lower = resume_text.lower()
        for skill in common_skills:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched_skills.append(skill)
        skills_str = ", ".join(matched_skills[:5])
        
        storage.ingest_candidate({
            "candidate_id": cid,
            "name": name,
            "resume_text": resume_text,
            "skills": skills_str,
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
    from services.storage.retrieval import MockResumeRetriever
    storage = get_retriever()
    ranker = get_reranker()

    # Retrieve all/large candidate pool to avoid retrieval bottleneck
    if isinstance(storage, MockResumeRetriever):
        retrieved = storage.search(job_description, len(storage._candidates))
    else:
        retrieved = storage.search(job_description, search_type="hybrid", top_k=max(top_k * 5, 100))

    normalized = []
    for c in retrieved:
        normalized.append({
            "id": c.get("candidate_id", c.get("id")),
            "name": c.get("name"),
            "skills": c.get("skills", []),
            "resume_text": c.get("resume_text", ""),
            "experience": c.get("experience"),
        })

    ranked = ranker.rank_candidates(
        job_description=job_description,
        retrieved_candidates=normalized,
        cutoff_layer=cutoff_layer,
    )

    # Slice ranked list to requested top_k at the output layer
    return ranked[:top_k]


# ------------------------------------------------------------------
# API ENDPOINTS - OUTPUT Layer
# ------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "name": "RARE Backend API",
        "version": "0.1.0",
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "ingest": "/api/ingest",
            "rank": "/api/rank",
            "candidates": "/api/candidates",
            "candidate_by_id": "/api/candidates/<id>",
            "setup": "/api/setup",
            "dashboard": "/api/dashboard",
            "analysis": "/api/analysis/run",
        }
    }), 200


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
    """List all candidates."""
    from services.storage.retrieval import MockResumeRetriever
    try:
        storage = get_retriever()
        if isinstance(storage, MockResumeRetriever):
            results = storage.search("", 100)
        else:
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


@app.route("/api/candidates/<int:candidate_id>", methods=["PATCH"])
def update_candidate_status(candidate_id: int):
    """Update candidate status."""
    data = request.get_json() or {}
    status = data.get("status", "reviewing")
    return jsonify({"candidate_id": candidate_id, "status": status, "updated": True}), 200


@app.route("/api/candidates/export/csv", methods=["POST"])
def export_candidates_csv():
    """Export candidates as CSV."""
    data = request.get_json() or {}
    ids = data.get("ids")
    storage = get_retriever()
    if ids:
        candidates = [storage.get_resume(int(cid)) for cid in ids]
        candidates = [c for c in candidates if c]
    else:
        candidates = storage.search("", search_type="keyword", top_k=100)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Skills", "Score", "Resume Text"])
    for c in candidates:
        writer.writerow([
            c.get("candidate_id"),
            c.get("name"),
            ", ".join(c.get("skills", [])) if isinstance(c.get("skills"), list) else c.get("skills", ""),
            c.get("ai_match_score", c.get("score", "")),
            c.get("resume_text", "")[:100],
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidates.csv"}
    )


@app.route("/api/setup", methods=["POST"])
def setup_storage():
    """Initialize Qdrant collection and indexes."""
    from services.storage.qdrant_setup import setup_qdrant
    try:
        setup_qdrant()
        return jsonify({"message": "Storage setup complete"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard", methods=["GET", "POST"])
def dashboard():
    """Dashboard analytics endpoint."""
    storage = get_retriever()
    ranker = get_reranker()

    if request.method == "POST":
        data = request.get_json() or {}
        try:
            req = DashboardRequest.model_validate(data)
        except Exception:
            req = DashboardRequest(query="")

        query = req.query or ""
        top_k = req.top_k or 20

        try:
            if query:
                raw_candidates = storage.search(query, min(top_k, 50))
                job_desc = query
            else:
                raw_candidates = storage.search("candidates", min(top_k, 50))
                job_desc = "General candidate search"

            if not raw_candidates:
                raw_candidates = storage.search("software developer engineer", min(top_k, 50))
                job_desc = "software developer engineer"

            if not raw_candidates:
                return jsonify({"error": "No candidates found. Run /setup first."}), 404

            ranked = []
            if ranker and not ranker.simulation_mode:
                ranked = ranker.rank_candidates(
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
            return jsonify({"error": str(e)}), 500

    # GET
    query = request.args.get("query", "")
    top_k = int(request.args.get("top_k", 20))

    try:
        if query:
            raw_candidates = storage.search(query, min(top_k, 50))
        else:
            raw_candidates = storage.search("candidates", min(top_k, 50))

        if not raw_candidates:
            raw_candidates = storage.search("software developer engineer", min(top_k, 50))

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


@app.route("/api/analysis/run", methods=["POST"])
def run_analysis():
    """Run analysis on resumes."""
    data = request.get_json() or {}
    job_description = data.get("jobDescription", data.get("query", ""))
    top_n = int(data.get("topN", data.get("top_k", 10)))

    try:
        ranked = run_ranking_pipeline(job_description, top_n, 12)
        return jsonify({
            "candidates": ranked,
            "totalScanned": len(ranked),
            "processingTime": "2m 14s",
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/active", methods=["GET"])
def get_active_analysis():
    return jsonify(None), 200


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    storage = get_retriever()
    try:
        candidates = storage.search("", search_type="keyword", top_k=100)
        if not candidates:
            candidates = storage.search("software developer engineer", top_k=100)
    except Exception:
        from services.storage.sample_resumes import SAMPLE_RESUMES
        candidates = [
            {
                "candidate_id": r["id"],
                "name": r["name"],
                "skills": r.get("skills", []),
                "experience": r.get("experience"),
                "score": 0.5,
            }
            for r in SAMPLE_RESUMES
        ]

    total = len(candidates)
    shortlisted = sum(1 for c in candidates if float(c.get("ai_match_score", c.get("score", 0))) >= 0.7)
    avg_score = sum(float(c.get("ai_match_score", c.get("score", 0))) for c in candidates) / max(total, 1)

    return jsonify({
        "totalCandidates": total,
        "shortlisted": shortlisted,
        "averageScore": avg_score,
        "processingTime": "2m 14s",
    }), 200


@app.route("/api/templates", methods=["GET"])
def list_templates():
    return jsonify([
        {"id": "1", "name": "Senior Backend Engineer", "createdAt": "2026-06-15T10:00:00Z"},
        {"id": "2", "name": "Full Stack Developer", "createdAt": "2026-06-10T08:30:00Z"},
    ]), 200


@app.route("/api/templates", methods=["POST"])
def create_template():
    data = request.get_json() or {}
    return jsonify({
        "id": str(request.time),
        **data,
        "createdAt": "2026-07-01T15:00:00Z",
    }), 201


@app.route("/api/templates/<id>", methods=["PUT"])
def update_template(id):
    data = request.get_json() or {}
    return jsonify({"id": id, **data}), 200


@app.route("/api/templates/<id>", methods=["DELETE"])
def delete_template(id):
    return jsonify({"message": "Template deleted"}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify([
        {"id": "1", "batchName": "Batch A", "date": "2026-07-01", "status": "completed", "candidates": 152},
        {"id": "2", "batchName": "Batch B", "date": "2026-06-28", "status": "completed", "candidates": 89},
    ]), 200


@app.route("/api/resume-batches", methods=["GET"])
def list_resume_batches():
    return jsonify([
        {"id": "1", "name": "Engineering Q3", "description": "Engineering candidates for Q3", "source": "LinkedIn", "resumeCount": 152, "createdAt": "2026-07-01", "status": "ready"},
        {"id": "2", "name": "Design Team", "description": "Design candidates", "source": "Internal", "resumeCount": 45, "createdAt": "2026-06-25", "status": "ready"},
    ]), 200


@app.route("/api/resume-batches/<id>", methods=["DELETE"])
def delete_resume_batch(id):
    return jsonify({"message": "Batch deleted"}), 200


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify({
        "name": "Alex Rivera",
        "role": "Lead Recruiter",
        "email": "alex.rivera@company.com",
        "organization": "Nexus Corp",
        "notifications": {"email": True, "inApp": True, "weekly": False},
        "theme": "light",
    }), 200


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    data = request.get_json() or {}
    return jsonify({"message": "Settings updated", **data}), 200


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
    print("  GET  /              - API info")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8000, debug=True)
