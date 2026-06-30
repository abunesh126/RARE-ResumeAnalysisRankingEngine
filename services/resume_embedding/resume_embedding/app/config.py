"""Pipeline configuration with YAML loading and device auto-detection.

Supports three configuration sources (later sources override earlier):
1. Built-in defaults
2. YAML config file (--config flag)
3. CLI argument overrides
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PipelineSettings(BaseModel):
    """Immutable configuration for the embedding pipeline."""

    model_name: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace model identifier for embedding generation.",
    )
    vector_dimension: int = Field(
        default=384,
        ge=1,
        description="Expected dimensionality of output embeddings.",
    )
    default_batch_size: int = Field(
        default=256,
        ge=1,
        le=4096,
        description="Number of texts to embed per inference batch.",
    )
    device: str = Field(
        default="auto",
        description="Compute device: 'auto', 'cuda', or 'cpu'.",
    )
    checkpoint_interval: int = Field(
        default=1000,
        ge=1,
        description="Save a checkpoint every N records processed.",
    )
    norm_tolerance: float = Field(
        default=1e-5,
        gt=0,
        description="Tolerance for L2 norm validation.",
    )

    model_config = {"frozen": True}

    def resolve_device(self) -> str:
        """Resolve the actual compute device.

        When device is 'auto', checks for CUDA availability via torch.
        Falls back to 'cpu' if torch is not installed or CUDA is unavailable.

        Returns:
            'cuda' or 'cpu'.
        """
        if self.device in ("cuda", "cpu"):
            return self.device

        # Auto-detect: try torch first, then onnxruntime.
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("Auto-detected CUDA via PyTorch: %s", torch.cuda.get_device_name(0))
                return "cuda"
        except ImportError:
            pass

        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in providers:
                logger.info("Auto-detected CUDA via ONNX Runtime CUDAExecutionProvider.")
                return "cuda"
        except ImportError:
            pass

        logger.info("No CUDA detected. Falling back to CPU.")
        return "cpu"

    @classmethod
    def from_yaml(cls, config_path: Path, **overrides: Any) -> "PipelineSettings":
        """Load settings from a YAML file with optional overrides.

        Args:
            config_path: Path to a YAML configuration file.
            **overrides: Keyword arguments that override YAML values.
                Values of None are ignored (treated as "not specified").

        Returns:
            A new PipelineSettings instance.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, encoding="utf-8") as fh:
            yaml_data = yaml.safe_load(fh) or {}

        # Apply non-None overrides on top of YAML values.
        for key, value in overrides.items():
            if value is not None:
                yaml_data[key] = value

        return cls(**yaml_data)


# Path to the bundled default config.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"

# Module-level default instance for convenience.
if _DEFAULT_CONFIG_PATH.exists():
    DEFAULT_SETTINGS = PipelineSettings.from_yaml(_DEFAULT_CONFIG_PATH)
else:
    DEFAULT_SETTINGS = PipelineSettings()
