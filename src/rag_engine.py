from __future__ import annotations

from dataclasses import asdict
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .document_loader import DocumentChunk
from .config import TOP_K


class LocalRAGEngine:
    """A lightweight local retrieval engine using TF-IDF.

    This avoids paid embedding APIs and keeps the first version easy to run.
    The answer generation still uses Gemini free API.
    """

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
        self.matrix = None

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        self.chunks = chunks
        texts = [c.text for c in chunks]
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None

    def is_ready(self) -> bool:
        return bool(self.chunks) and self.matrix is not None

    def search(self, query: str, top_k: int = TOP_K) -> List[Tuple[DocumentChunk, float]]:
        if not self.is_ready():
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        best_indexes = scores.argsort()[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in best_indexes if scores[i] > 0]

    def stats(self) -> dict:
        files = sorted(set(c.filename for c in self.chunks))
        return {"files": files, "file_count": len(files), "chunk_count": len(self.chunks)}

    def export_chunks(self) -> list[dict]:
        return [asdict(c) for c in self.chunks]
