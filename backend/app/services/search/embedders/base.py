from abc import ABC, abstractmethod

import numpy as np
from PIL.Image import Image


class TextEmbedder(ABC):
    """Encodes text strings into L2-normalized float32 vectors."""

    @property
    @abstractmethod
    def dim(self) -> int: ...

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return shape (len(texts), dim), L2-normalized, float32."""


class ImageEmbedder(ABC):
    """Encodes PIL images into L2-normalized float32 vectors."""

    @property
    @abstractmethod
    def dim(self) -> int: ...

    @abstractmethod
    def encode(self, images: list[Image]) -> np.ndarray:
        """Return shape (len(images), dim), L2-normalized, float32."""
