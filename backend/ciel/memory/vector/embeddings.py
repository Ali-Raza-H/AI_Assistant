from __future__ import annotations

import hashlib
import math
import re


class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Embedding provider is a stage-2 extension point")


class HashEmbeddingProvider(EmbeddingProvider):
    """Small deterministic embedding fallback for local semantic retrieval."""

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
