import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock torch and FlagEmbedding dynamically to test both execution paths
# without requiring heavy installations or downloading huge neural model weights.
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = True

mock_reranker_class = MagicMock()
mock_reranker_instance = MagicMock()
mock_reranker_class.return_value = mock_reranker_instance
mock_reranker_instance.compute_score.return_value = [0.95, 0.20, 0.75]

# Inject the mocks into sys.modules before importing ranking components
with patch.dict(sys.modules, {
    'torch': mock_torch,
    'FlagEmbedding': MagicMock(LayerWiseFlagLLMReranker=mock_reranker_class)
}):
    # Force _HAS_DEPS to True for the sake of importing neural path code
    import services.ranking.layerwise_engine
    services.ranking.layerwise_engine._HAS_DEPS = True
    
    from services.ranking.layerwise_engine import LayerwiseCandidateReranker
    from services.ranking.schemas import CandidateInput, CandidateRanked

def test_candidate_schemas_valid_parsing():
    """
    Test that valid candidate dicts are correctly parsed by Pydantic CandidateInput,
    and extra keys passed from upstream are preserved.
    """
    candidate_data = {
        "id": 101,
        "name": "Jane Doe",
        "skills": "Python, Spark",
        "resume_text": "Data engineer with 3 years experience.",
        "extra_upstream_field": "some-db-id"
    }
    
    cand = CandidateInput.model_validate(candidate_data)
    assert cand.id == 101
    assert cand.name == "Jane Doe"
    # Verify extra fields are allowed and accessible via dict dumps
    assert cand.model_dump()["extra_upstream_field"] == "some-db-id"

def test_candidate_schemas_invalid_parsing():
    """
    Test that invalid schema inputs (missing fields) raise ValueError or ValidationError.
    """
    invalid_data = {
        "id": 102,
        # missing name, skills, resume_text
    }
    with pytest.raises(Exception):
         CandidateInput.model_validate(invalid_data)

def test_empty_candidates_returns_immediately():
    """
    Test that an empty candidate list returns immediately without invoking models.
    """
    reranker = LayerwiseCandidateReranker(simulation_mode=True)
    res = reranker.rank_candidates("Job desc", [])
    assert res == []

def test_rank_candidates_sorting_order():
    """
    Test that rank_candidates output is sorted in descending order of score.
    """
    reranker = LayerwiseCandidateReranker(simulation_mode=True)
    candidates = [
        {"id": 1, "name": "Python dev", "skills": "Python", "resume_text": "Writes python backend code."},
        {"id": 2, "name": "Frontend", "skills": "CSS, HTML", "resume_text": "Design websites using HTML."},
    ]
    # For a Python description, python candidate should score higher
    ranked = reranker.rank_candidates("Looking for Python", candidates)
    
    assert len(ranked) == 2
    # First candidate should have higher score than second candidate
    assert ranked[0]["ai_match_score"] >= ranked[1]["ai_match_score"]

def test_neural_path_inference_and_cutoff_propagation():
    """
    Test that the neural path initializes the LayerWiseFlagLLMReranker, 
    propagates early exit cutoff layers correctly, and maps scores correctly.
    """
    # Reset mocks
    mock_reranker_class.reset_mock()
    mock_reranker_instance.compute_score.reset_mock()
    
    # Mock return values
    mock_reranker_instance.compute_score.return_value = [0.85, 0.45]
    
    # Initialize with simulation_mode=False (force neural path test)
    reranker = LayerwiseCandidateReranker(simulation_mode=False)
    
    # Verify class initialized the FlagEmbedding model on cuda (mocked as available)
    assert reranker.simulation_mode is False
    assert reranker.device == "cuda"
    mock_reranker_class.assert_called_once_with(
        'BAAI/bge-reranker-v2-minicpm-layerwise', 
        use_fp16=True, 
        devices=["cuda"]
    )
    
    candidates = [
        {"id": 101, "name": "Alice", "skills": "Python", "resume_text": "Experienced Dev"},
        {"id": 102, "name": "Bob", "skills": "React", "resume_text": "Frontend Dev"},
    ]
    
    res = reranker.rank_candidates("Looking for Dev", candidates, cutoff_layer=15)
    
    # Verify compute_score called with exact pairs and cutoff list format
    mock_reranker_instance.compute_score.assert_called_once_with(
        [
            ["Looking for Dev", "Skills: Python. Resume: Experienced Dev"],
            ["Looking for Dev", "Skills: React. Resume: Frontend Dev"]
        ],
        cutoff_layers=[15],
        normalize=True
    )
    
    # Verify match scores injected correctly
    assert res[0]["ai_match_score"] == 0.85
    assert res[1]["ai_match_score"] == 0.45

def test_neural_inference_fallback_on_exception():
    """
    Test that if compute_score fails during neural inference, the engine fallbacks 
    gracefully to simulation keyword scoring instead of crashing the pipeline.
    """
    mock_reranker_instance.compute_score.side_effect = RuntimeException("CUDA Out Of Memory")
    
    reranker = LayerwiseCandidateReranker(simulation_mode=False)
    candidates = [
        {"id": 1, "name": "Alice", "skills": "Go", "resume_text": "Go Dev"},
    ]
    
    # Should not raise exception
    res = reranker.rank_candidates("Go", candidates)
    assert len(res) == 1
    assert "ai_match_score" in res[0]
    assert isinstance(res[0]["ai_match_score"], float)

class RuntimeException(Exception):
    pass
