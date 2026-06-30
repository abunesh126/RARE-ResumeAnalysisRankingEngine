import os
import sys
from typing import List, Dict, Any, Union
from .schemas import CandidateInput, CandidateRanked

# Lazy import flag to support clean testing and development environments
try:
    import torch
    from FlagEmbedding import LayerWiseFlagLLMReranker
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

class LayerwiseCandidateReranker:
    """
    High-performance Layerwise LLM Reranker designed to optimize latency
    on consumer GPUs (like the Asus TUF A15) using early-exit layer processing.
    """
    def __init__(
        self, 
        model_name: str = 'BAAI/bge-reranker-v2-minicpm-layerwise', 
        use_fp16: bool = True,
        simulation_mode: bool = False
    ):
        """
        Initializes the reranker model on CUDA (if available) or CPU.
        
        Args:
            model_name: HuggingFace hub path to the layerwise reranker model.
            use_fp16: If True, uses half-precision (float16) to save VRAM and increase speed.
            simulation_mode: If True, runs mock ranking without loading PyTorch/FlagEmbedding.
        """
        self.simulation_mode = simulation_mode or not _HAS_DEPS
        
        if not _HAS_DEPS and not simulation_mode:
            print("[WARNING] torch or FlagEmbedding not found. Falling back to SIMULATION MODE.")
            self.simulation_mode = True

        if self.simulation_mode:
            self.device = "cpu"
            self.reranker = None
            print("[INFO] Initializing Reranker in SIMULATION MODE (no heavy model loaded).")
            return

        # Automatically detect NVIDIA GPU to utilize GPU acceleration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Initializing Reranker on device: {self.device}")
        
        try:
            # Initialize the model using FP16 (half-precision) to save VRAM
            self.reranker = LayerWiseFlagLLMReranker(
                model_name, 
                use_fp16=use_fp16,
                devices=[self.device] if self.device == "cuda" else None
            )
            print("[INFO] Model loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load model. Falling back to simulation mode. Details: {e}")
            self.simulation_mode = True
            self.device = "cpu"
            self.reranker = None

    def rank_candidates(
        self, 
        job_description: str, 
        retrieved_candidates: List[Union[Dict[str, Any], CandidateInput]], 
        cutoff_layer: int = 12,
        normalize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Takes a job description and a list of candidates retrieved by the team,
        calculates contextual scores using early-exit layers, and returns a sorted list of dictionaries.
        
        Args:
            job_description: Job description text query.
            retrieved_candidates: List of Candidate dictionaries or CandidateInput models.
            cutoff_layer: Early exit layer index (typically 8 to 40). Lower layer = faster.
            normalize: If True, maps scores to probability range [0, 1].
            
        Returns:
            Sorted list of candidate dictionaries including 'ai_match_score', sorted in descending order.
        """
        if not retrieved_candidates:
            return []

        # Validate incoming data using Pydantic schema
        validated_candidates: List[CandidateInput] = []
        for idx, item in enumerate(retrieved_candidates):
            try:
                if isinstance(item, CandidateInput):
                    validated_candidates.append(item)
                else:
                    validated_candidates.append(CandidateInput.model_validate(item))
            except Exception as e:
                raise ValueError(
                    f"Candidate validation failed at index {idx}. Data: {item}. Error: {e}"
                )

        if self.simulation_mode:
            # Run simulation scoring
            scores = self._compute_simulation_scores(job_description, validated_candidates)
        else:
            # Format input data into [Query, Document] pairs for Cross-Encoder
            pairs = []
            for candidate in validated_candidates:
                candidate_text = f"Skills: {candidate.skills}. Resume: {candidate.resume_text}"
                pairs.append([job_description, candidate_text])

            print(f"[INFO] Processing {len(pairs)} candidates with cutoff layer: {cutoff_layer}")
            try:
                # FlagEmbedding expects a list of cutoff layers, e.g., [cutoff_layer]
                scores = self.reranker.compute_score(
                    pairs, 
                    cutoff_layers=[cutoff_layer], 
                    normalize=normalize
                )
                
                # Defensive check: if scores is returned as a single float, wrap it in a list
                if isinstance(scores, (int, float)):
                    scores = [float(scores)]
                elif isinstance(scores, list) and len(scores) > 0 and isinstance(scores[0], list):
                    # FlagEmbedding might return nested lists if multiple layers were computed
                    # We extract the score for our target cutoff layer
                    scores = [float(s[0]) for s in scores]
                else:
                    scores = [float(s) for s in scores]
                    
            except Exception as e:
                print(f"[ERROR] Inference error: {e}. Falling back to simulation scores.")
                scores = self._compute_simulation_scores(job_description, validated_candidates)

        # Inject scores and prepare response candidates as dicts (preserving extra attributes)
        output_candidates = []
        for idx, candidate in enumerate(validated_candidates):
            candidate_dict = candidate.model_dump()
            candidate_dict['ai_match_score'] = float(scores[idx])
            output_candidates.append(candidate_dict)

        # Sort candidates in descending order based on their AI score
        ranked_candidates = sorted(
            output_candidates, 
            key=lambda x: x['ai_match_score'], 
            reverse=True
        )

        return ranked_candidates

    def _compute_simulation_scores(
        self, 
        job_description: str, 
        candidates: List[CandidateInput]
    ) -> List[float]:
        """
        Calculates simple keyword overlap scores for demonstration and test runs 
        without downloading heavy model parameters. Mapped synonyms support domain-specific matching.
        """
        # Stop words to filter out from job description matching
        stop_words = {
            "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", 
            "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto", 
            "out", "over", "to", "up", "with", "is", "was", "were", "be", "been", 
            "being", "have", "has", "had", "do", "does", "did", "looking", "expertise"
        }
        
        # Normalize and clean job description
        jd_text = job_description.lower().replace(",", " ").replace(".", " ")
        # Map synonyms to catch related terms in ATS context
        synonyms = {
            "golang": "go",
            "k8s": "kubernetes",
            "k8": "kubernetes",
            "docker": "container",
            "containers": "container"
        }
        
        # Tokenize and filter job description
        jd_words = []
        for word in jd_text.split():
            if word not in stop_words and len(word) >= 2:
                word_mapped = synonyms.get(word, word)
                jd_words.append(word_mapped)
        
        scores = []
        for candidate in candidates:
            # Normalize candidate skills and resume text
            skills_text = candidate.skills.lower().replace(",", " ").replace(".", " ")
            resume_text = candidate.resume_text.lower().replace(",", " ").replace(".", " ")
            
            # Map synonyms in candidate texts
            cand_words = []
            for word in (skills_text + " " + resume_text).split():
                cand_words.append(synonyms.get(word, word))
            cand_text = " ".join(cand_words)
            
            # Count word matches
            overlap_count = 0
            for word in jd_words:
                if word in cand_text:
                    overlap_count += 1
            
            base_score = float(overlap_count) / max(len(jd_words), 1)
            
            # Compute a specific skills bonus
            cand_skills_words = [synonyms.get(w, w) for w in skills_text.split()]
            skills_match = sum(1 for w in jd_words if w in cand_skills_words)
            
            # Final score mapped to [0, 1] range
            final_score = min(base_score + 0.15 * skills_match, 1.0)
            scores.append(final_score)
            
        return scores

