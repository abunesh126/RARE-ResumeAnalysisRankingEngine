import unittest
from unittest.mock import MagicMock, patch

from qdrant_client.http.exceptions import UnexpectedResponse

from services.storage.config import KEYWORD_WEIGHT, VECTOR_WEIGHT
from services.storage.qdrant_setup import setup_qdrant
from services.storage.retrieval import ResumeRetriever


class StorageTests(unittest.TestCase):
    """Core storage and retrieval tests."""

    @patch("services.storage.qdrant_setup.QdrantClient")
    @patch("services.storage.qdrant_setup.TextEmbedding")
    @patch("services.storage.qdrant_setup.UnexpectedResponse", new=Exception)
    def test_setup_qdrant_creates_collection(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("missing")
        mock_client_class.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        ]
        mock_embedding_class.return_value = mock_embedding

        setup_qdrant(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        mock_client.create_collection.assert_called_once()

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_search_returns_ranked_results(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.side_effect = [
            [MagicMock(tolist=lambda: [1.0, 0.0])],
            [MagicMock(tolist=lambda: [1.0, 0.0])],
            [MagicMock(tolist=lambda: [1.0, 0.0])],
            [MagicMock(tolist=lambda: [0.0, 1.0])],
        ]
        mock_embedding_class.return_value = embedding

        alice = MagicMock()
        alice.id = 1
        alice.score = 0.95
        alice.payload = {
            "candidate_id": 1,
            "name": "Alice",
            "resume_text": "Python developer",
            "skills": ["Python"],
            "experience": 3,
        }

        bob = MagicMock()
        bob.id = 2
        bob.score = 0.72
        bob.payload = {
            "candidate_id": 2,
            "name": "Bob",
            "resume_text": "React developer",
            "skills": ["React"],
            "experience": 4,
        }

        mock_client.query_points.return_value.points = [alice, bob]

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        results = retriever.search(
            "Python developer",
            top_k=2,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["candidate_id"], 1)
        self.assertGreaterEqual(
            results[0]["score"],
            results[1]["score"],
        )

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_ingest_candidate_stores_payload(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        payload = retriever.ingest_candidate(
            {
                "candidate_id": 99,
                "name": "Sarah",
                "resume_text": "Backend Engineer",
                "skills": ["Python", "AWS"],
                "experience": 6,
            }
        )

        mock_client.upsert.assert_called_once()

        self.assertEqual(payload["candidate_id"], 99)
        self.assertEqual(payload["name"], "Sarah")

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_get_resume_returns_payload(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        ]
        mock_embedding_class.return_value = embedding

        point = MagicMock()
        point.id = 7
        point.payload = {
            "candidate_id": 7,
            "name": "John",
            "resume_text": "Python AWS Docker",
            "skills": ["Python", "AWS"],
            "experience": 5,
        }

        mock_client.retrieve.return_value = [point]

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        resume = retriever.get_resume(7)
        self.assertIsNotNone(resume)
        assert resume is not None

        self.assertEqual(resume["candidate_id"], 7)
        self.assertEqual(resume["name"], "John")

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_ingest_missing_resume_text(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_embedding_class.return_value = MagicMock()

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        with self.assertRaises(ValueError):
            retriever.ingest_candidate(
                {
                    "candidate_id": 1,
                    "name": "Alice",
                }
            )

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_ingest_missing_candidate_id(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        with self.assertRaises(ValueError):
            retriever.ingest_candidate(
                {
                    "resume_text": "Python Developer",
                    "skills": ["Python"],
                }
            )

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_ingest_without_optional_fields(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever(
            collection_name="resumes-test",
            host="localhost",
            port=6333,
        )

        payload = retriever.ingest_candidate(
            {
                "candidate_id": 15,
                "resume_text": "Python Developer",
            }
        )

        self.assertEqual(payload["candidate_id"], 15)
        self.assertEqual(payload["skills"], [])
        self.assertIsNone(payload["experience"])


class HybridSearchTests(unittest.TestCase):
    """Tests for Hybrid Search functionality."""

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_extract_keywords(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        retriever = ResumeRetriever()

        keywords = retriever.extract_keywords(
            "Senior Python Developer with AWS and Docker"
        )

        self.assertIn("python", keywords)
        self.assertIn("developer", keywords)
        self.assertIn("aws", keywords)
        self.assertIn("docker", keywords)

        self.assertNotIn("with", keywords)
        self.assertNotIn("and", keywords)

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_vector_search(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.5, 0.7])
        ]
        mock_embedding_class.return_value = embedding

        point = MagicMock()
        point.id = 1
        point.score = 0.91
        point.payload = {
            "candidate_id": 1,
            "name": "Alice",
            "resume_text": "Python AWS Engineer",
            "skills": ["Python", "AWS"],
            "experience": 5,
        }

        mock_client.query_points.return_value.points = [point]

        retriever = ResumeRetriever()

        results = retriever.vector_search(
            "Python",
            top_k=5,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["candidate_id"], 1)
        self.assertEqual(results[0]["vector_score"], 0.91)

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_keyword_search(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        point = MagicMock()
        point.id = 1
        point.payload = {
            "candidate_id": 1,
            "name": "Alice",
            "resume_text": "Python AWS Developer",
            "skills": ["Python", "AWS"],
            "experience": 5,
        }

        mock_client.scroll.return_value = ([point], None)

        retriever = ResumeRetriever()

        results = retriever.keyword_search(
            "Python AWS",
            top_k=5,
        )

        self.assertEqual(len(results), 1)
        self.assertGreater(results[0]["keyword_score"], 0)

    def test_merge_results(self):

        vector_results = [
            {
                "candidate_id": 1,
                "name": "Alice",
                "vector_score": 0.9,
            },
            {
                "candidate_id": 2,
                "name": "Bob",
                "vector_score": 0.7,
            },
        ]

        keyword_results = [
            {
                "candidate_id": 2,
                "name": "Bob",
                "keyword_score": 3,
            },
            {
                "candidate_id": 3,
                "name": "Charlie",
                "keyword_score": 5,
            },
        ]

        merged = ResumeRetriever.merge_results(
            vector_results,
            keyword_results,
        )

        self.assertEqual(len(merged), 3)

        ids = [candidate["candidate_id"] for candidate in merged]

        self.assertIn(1, ids)
        self.assertIn(2, ids)
        self.assertIn(3, ids)

    def test_normalize_scores(self):

        candidates = [
            {
                "candidate_id": 1,
                "vector_score": 0.2,
                "keyword_score": 2,
            },
            {
                "candidate_id": 2,
                "vector_score": 0.6,
                "keyword_score": 5,
            },
            {
                "candidate_id": 3,
                "vector_score": 1.0,
                "keyword_score": 8,
            },
        ]

        normalized = ResumeRetriever.normalize_scores(candidates)

        for candidate in normalized:

            self.assertGreaterEqual(
                candidate["vector_score"],
                0.0,
            )

            self.assertLessEqual(
                candidate["vector_score"],
                1.0,
            )

            self.assertGreaterEqual(
                candidate["keyword_score"],
                0.0,
            )

            self.assertLessEqual(
                candidate["keyword_score"],
                1.0,
            )

    def test_normalize_scores_identical(self):

        candidates = [
            {
                "candidate_id": 1,
                "vector_score": 0.8,
                "keyword_score": 0,
            },
            {
                "candidate_id": 2,
                "vector_score": 0.8,
                "keyword_score": 0,
            },
        ]

        normalized = ResumeRetriever.normalize_scores(candidates)

        for candidate in normalized:

            self.assertEqual(
                candidate["vector_score"],
                0.0,
            )

            self.assertEqual(
                candidate["keyword_score"],
                0.0,
            )

    def test_calculate_final_score(self):

        candidates = [
            {
                "candidate_id": 1,
                "vector_score": 1.0,
                "keyword_score": 0.5,
            },
            {
                "candidate_id": 2,
                "vector_score": 0.5,
                "keyword_score": 1.0,
            },
        ]

        ranked = ResumeRetriever.calculate_final_score(
            candidates,
            VECTOR_WEIGHT,
            KEYWORD_WEIGHT,
        )

        self.assertEqual(len(ranked), 2)

        self.assertGreaterEqual(
            ranked[0]["score"],
            ranked[1]["score"],
        )

    @patch.object(ResumeRetriever, "vector_search")
    @patch.object(ResumeRetriever, "keyword_search")
    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_search_hybrid(
        self,
        mock_embedding_class,
        mock_client_class,
        mock_keyword,
        mock_vector,
    ):

        mock_vector.return_value = [
            {
                "candidate_id": 1,
                "name": "Alice",
                "vector_score": 0.95,
            }
        ]

        mock_keyword.return_value = [
            {
                "candidate_id": 1,
                "name": "Alice",
                "keyword_score": 4,
            }
        ]

        retriever = ResumeRetriever()

        results = retriever.search_hybrid(
            "Python Developer",
            top_k=5,
        )

        self.assertEqual(len(results), 1)

        self.assertEqual(
            results[0]["candidate_id"],
            1,
        )

        self.assertIn("score", results[0])


class EdgeCaseTests(unittest.TestCase):
    """Edge-case and regression tests."""

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_empty_query_returns_empty_keyword_results(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        retriever = ResumeRetriever()

        results = retriever.keyword_search("", top_k=5)

        self.assertEqual(results, [])

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_empty_database(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client.query_points.return_value.points = []
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever()

        results = retriever.search(
            "Python",
            top_k=5,
        )

        self.assertEqual(results, [])

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_duplicate_candidate_ingestion(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever()

        candidate = {
            "candidate_id": 10,
            "name": "Alice",
            "resume_text": "Python Developer",
            "skills": ["Python"],
            "experience": 3,
        }

        retriever.ingest_candidate(candidate)
        retriever.ingest_candidate(candidate)

        self.assertEqual(mock_client.upsert.call_count, 2)

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_large_resume_ingestion(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1] * 384)
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever()

        large_resume = "Python AWS Docker Kubernetes " * 5000

        payload = retriever.ingest_candidate(
            {
                "candidate_id": 100,
                "name": "Large Resume",
                "resume_text": large_resume,
            }
        )

        self.assertEqual(payload["candidate_id"], 100)

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_missing_skills_field(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever()

        payload = retriever.ingest_candidate(
            {
                "candidate_id": 50,
                "resume_text": "Python Developer",
            }
        )

        self.assertEqual(payload["skills"], [])

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_missing_experience_field(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        embedding = MagicMock()
        embedding.embed.return_value = [
            MagicMock(tolist=lambda: [0.1, 0.2])
        ]
        mock_embedding_class.return_value = embedding

        retriever = ResumeRetriever()

        payload = retriever.ingest_candidate(
            {
                "candidate_id": 60,
                "resume_text": "Machine Learning Engineer",
            }
        )

        self.assertIsNone(payload["experience"])

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_search_type_keyword(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        retriever = ResumeRetriever()

        with patch.object(
            retriever,
            "keyword_search",
            return_value=[],
        ):

            results = retriever.search(
                "Python",
                search_type="keyword",
            )

            self.assertEqual(results, [])

    @patch("services.storage.retrieval.QdrantClient")
    @patch("services.storage.retrieval.TextEmbedding")
    def test_search_type_hybrid(
        self,
        mock_embedding_class,
        mock_client_class,
    ):
        retriever = ResumeRetriever()

        with patch.object(
            retriever,
            "search_hybrid",
            return_value=[],
        ):

            results = retriever.search(
                "Python",
                search_type="hybrid",
            )

            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()