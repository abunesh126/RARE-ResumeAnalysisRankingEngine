"""Tests for metadata_writer module."""

import json
from pathlib import Path

from resume_embedding.app.io import write_metadata


class TestWriteMetadata:
    """Tests for the write_metadata function."""

    def test_writes_metadata_file(self, tmp_output_dir: Path) -> None:
        """Should create a metadata.json file."""
        path = write_metadata(
            tmp_output_dir,
            model="BAAI/bge-small-en-v1.5",
            dimension=384,
            normalized=True,
            records_processed=100000,
        )
        assert path.exists()
        assert path.name == "metadata.json"

    def test_metadata_content(self, tmp_output_dir: Path) -> None:
        """Metadata content should match input parameters."""
        write_metadata(
            tmp_output_dir,
            model="BAAI/bge-small-en-v1.5",
            dimension=384,
            normalized=True,
            records_processed=100000,
            device="cuda",
            input_file="/path/to/data.jsonl",
        )
        with open(tmp_output_dir / "metadata.json") as fh:
            data = json.load(fh)

        assert data["model"] == "BAAI/bge-small-en-v1.5"
        assert data["dimension"] == 384
        assert data["normalized"] is True
        assert data["records_processed"] == 100000
        assert data["device"] == "cuda"
        assert data["input_file"] == "/path/to/data.jsonl"
        assert "timestamp" in data

    def test_creates_directory(self, tmp_output_dir: Path) -> None:
        """Should create the output directory if missing."""
        nested = tmp_output_dir / "a" / "b"
        write_metadata(
            nested,
            model="test",
            dimension=384,
            normalized=True,
            records_processed=10,
        )
        assert (nested / "metadata.json").exists()

    def test_metadata_keys(self, tmp_output_dir: Path) -> None:
        """Metadata should have the expected keys."""
        write_metadata(
            tmp_output_dir,
            model="test",
            dimension=384,
            normalized=True,
            records_processed=50,
        )
        with open(tmp_output_dir / "metadata.json") as fh:
            data = json.load(fh)
        expected_keys = {"model", "dimension", "normalized", "records_processed",
                         "device", "input_file", "timestamp"}
        assert set(data.keys()) == expected_keys
