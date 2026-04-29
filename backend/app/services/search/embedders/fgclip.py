from __future__ import annotations

import logging
import threading

import numpy as np
import torch
from PIL.Image import Image
from transformers import AutoModelForCausalLM, AutoProcessor

from app.core.config import settings
from app.services.search.embedders.base import ImageEmbedder, TextEmbedder
from app.services.search.embedders.bge import _resolve_device
from app.services.search.exceptions import EmbedderUnavailable

logger = logging.getLogger(__name__)


def _l2_normalize(x: torch.Tensor) -> torch.Tensor:
    return x / x.norm(dim=-1, keepdim=True).clamp(min=1e-12)


class FgClipEmbedder(ImageEmbedder, TextEmbedder):
    """Single FG-CLIP 2 model exposing both image and text encoding."""

    _instance: "FgClipEmbedder | None" = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "FgClipEmbedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        self._device = _resolve_device()
        try:
            self._processor = AutoProcessor.from_pretrained(
                settings.SEMANTIC_FGCLIP_MODEL,
                trust_remote_code=True,
                cache_dir=settings.SEMANTIC_HF_CACHE_DIR,
            )
            # FG-CLIP 2 registers itself only under AutoModelForCausalLM
            # (see config.json `auto_map`), so we must use that loader even
            # though the model is a CLIP-style dual encoder, not a causal LM.
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.SEMANTIC_FGCLIP_MODEL,
                trust_remote_code=True,
                cache_dir=settings.SEMANTIC_HF_CACHE_DIR,
            ).to(self._device).eval()
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 load failed: {e}") from e

    @property
    def dim(self) -> int:
        return settings.SEMANTIC_FGCLIP_DIM

    @torch.inference_mode()
    def encode(self, items):  # type: ignore[override]
        # Dispatch for ABC: image list vs text list
        if not items:
            return np.zeros((0, self.dim), dtype=np.float32)
        if isinstance(items[0], str):
            return self._encode_text(items)
        return self._encode_image(items)

    @torch.inference_mode()
    def _encode_image(self, images: list[Image]) -> np.ndarray:
        try:
            inputs = self._processor(images=images, return_tensors="pt").to(self._device)
            feats = self._model.get_image_features(**inputs)
            feats = _l2_normalize(feats)
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 image encode failed: {e}") from e
        return feats.cpu().numpy().astype(np.float32, copy=False)

    @torch.inference_mode()
    def _encode_text(self, texts: list[str]) -> np.ndarray:
        try:
            inputs = self._processor(
                text=texts, return_tensors="pt", padding=True, truncation=True
            ).to(self._device)
            # walk_type="short" matches the query path (search bar input);
            # "long" is for description-length captions and is not used here.
            feats = self._model.get_text_features(**inputs, walk_type="short")
            feats = _l2_normalize(feats)
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"FG-CLIP 2 text encode failed: {e}") from e
        return feats.cpu().numpy().astype(np.float32, copy=False)
