from __future__ import annotations

import logging
import threading

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.search.embedders.base import TextEmbedder
from app.services.search.exceptions import EmbedderUnavailable

logger = logging.getLogger(__name__)


def _resolve_device() -> str:
    if settings.SEMANTIC_DEVICE == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return settings.SEMANTIC_DEVICE


class BgeTextEmbedder(TextEmbedder):
    _instance: "BgeTextEmbedder | None" = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "BgeTextEmbedder":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        try:
            self._model = SentenceTransformer(
                settings.SEMANTIC_TEXT_MODEL,
                device=_resolve_device(),
                cache_folder=settings.SEMANTIC_HF_CACHE_DIR,
            )
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"BGE load failed: {e}") from e

    @property
    def dim(self) -> int:
        return settings.SEMANTIC_TEXT_DIM

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        try:
            vecs = self._model.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as e:  # noqa: BLE001
            raise EmbedderUnavailable(f"BGE encode failed: {e}") from e
        return vecs.astype(np.float32, copy=False)
