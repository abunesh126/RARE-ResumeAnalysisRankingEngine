"""Tests for YAML configuration loading."""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from resume_embedding.app.config import PipelineSettings


@pytest.fixture
def yaml_config_path() -> Path:
    """Create a temporary YAML config file."""
    config = {
        "model_name": "BAAI/bge-base-en-v1.5",
        "vector_dimension": 768,
        "default_batch_size": 128,
        "device": "cpu",
        "checkpoint_interval": 500,
        "norm_tolerance": 1e-6,
    }
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    yaml.dump(config, tmp)
    tmp.close()
    return Path(tmp.name)


@pytest.fixture
def partial_yaml_config_path() -> Path:
    """Create a YAML config with only some fields set."""
    config = {
        "default_batch_size": 512,
        "device": "cuda",
    }
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    yaml.dump(config, tmp)
    tmp.close()
    return Path(tmp.name)


class TestPipelineSettingsYAML:
    """Tests for YAML config loading and overrides."""

    def test_load_full_yaml(self, yaml_config_path: Path) -> None:
        """Should load all settings from a YAML file."""
        settings = PipelineSettings.from_yaml(yaml_config_path)

        assert settings.model_name == "BAAI/bge-base-en-v1.5"
        assert settings.vector_dimension == 768
        assert settings.default_batch_size == 128
        assert settings.device == "cpu"
        assert settings.checkpoint_interval == 500

    def test_partial_yaml_uses_defaults(self, partial_yaml_config_path: Path) -> None:
        """Unspecified fields should use built-in defaults."""
        settings = PipelineSettings.from_yaml(partial_yaml_config_path)

        assert settings.default_batch_size == 512
        assert settings.device == "cuda"
        # Defaults:
        assert settings.model_name == "BAAI/bge-small-en-v1.5"
        assert settings.vector_dimension == 384

    def test_cli_overrides_yaml(self, yaml_config_path: Path) -> None:
        """CLI overrides should take precedence over YAML values."""
        settings = PipelineSettings.from_yaml(
            yaml_config_path,
            default_batch_size=64,
            device="cuda",
        )

        assert settings.default_batch_size == 64
        assert settings.device == "cuda"
        # YAML values that weren't overridden:
        assert settings.model_name == "BAAI/bge-base-en-v1.5"

    def test_none_overrides_ignored(self, yaml_config_path: Path) -> None:
        """None-valued overrides should not replace YAML values."""
        settings = PipelineSettings.from_yaml(
            yaml_config_path,
            default_batch_size=None,
            device=None,
        )

        assert settings.default_batch_size == 128  # from YAML
        assert settings.device == "cpu"  # from YAML

    def test_nonexistent_yaml_raises(self) -> None:
        """Should raise FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            PipelineSettings.from_yaml(Path("/nonexistent/config.yaml"))

    def test_empty_yaml_uses_defaults(self) -> None:
        """Empty YAML file should produce default settings."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        tmp.write("")
        tmp.close()

        settings = PipelineSettings.from_yaml(Path(tmp.name))
        assert settings.model_name == "BAAI/bge-small-en-v1.5"
        assert settings.vector_dimension == 384


class TestDeviceResolution:
    """Tests for device auto-detection."""

    def test_explicit_cpu(self) -> None:
        """device='cpu' should resolve to 'cpu'."""
        settings = PipelineSettings(device="cpu")
        assert settings.resolve_device() == "cpu"

    def test_explicit_cuda(self) -> None:
        """device='cuda' should resolve to 'cuda'."""
        settings = PipelineSettings(device="cuda")
        assert settings.resolve_device() == "cuda"

    def test_auto_resolves_to_string(self) -> None:
        """device='auto' should resolve to either 'cuda' or 'cpu'."""
        settings = PipelineSettings(device="auto")
        result = settings.resolve_device()
        assert result in ("cuda", "cpu")

    def test_frozen_model(self) -> None:
        """Settings should be immutable."""
        settings = PipelineSettings()
        with pytest.raises(ValidationError):
            settings.model_name = "other-model"
