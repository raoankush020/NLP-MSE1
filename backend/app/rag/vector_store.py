import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings

class VectorStore:
    """Manages document chunk embeddings and similarity search."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = Path(persist_dir or settings.VECTOR_DB_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.persist_dir / "chunks_index.json"
        
        self.chunks: List[Dict[str, Any]] = []
        self._st_model = None
        self._use_st = True
        self.load()

    def _get_sentence_transformer(self):
        if not self._use_st:
            return None
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Suppress noisy logs and load small fast model
                self._st_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            except Exception as e:
                print(f"[VectorStore] SentenceTransformer not available or offline ({e}). Using TF-IDF vectorizer fallback.")
                self._use_st = False
                self._st_model = None
        return self._st_model

    def load(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception as e:
                print(f"[VectorStore] Error loading vector index: {e}")
                self.chunks = []
        else:
            self.chunks = []

    def save(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[VectorStore] Error saving vector index: {e}")

    def add_chunks(self, document_id: str, new_chunks: List[Dict[str, Any]]):
        # Remove existing chunks for this document if any
        self.delete_document(document_id)
        for ch in new_chunks:
            self.chunks.append(ch)
        self.save()

    def delete_document(self, document_id: str):
        self.chunks = [ch for ch in self.chunks if ch.get("document_id") != document_id]
        self.save()

    def search(
        self,
        query: str,
        top_k: int = 4,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []

        filtered_chunks = self.chunks
        if document_ids:
            filtered_chunks = [ch for ch in self.chunks if ch.get("document_id") in document_ids]

        if not filtered_chunks:
            return []

        query = query.strip()
        if not query:
            return []

        st_model = self._get_sentence_transformer()
        texts = [ch["content"] for ch in filtered_chunks]

        if st_model is not None:
            try:
                query_vec = st_model.encode([query])
                chunk_vecs = st_model.encode(texts)
                scores = cosine_similarity(query_vec, chunk_vecs)[0]
            except Exception as e:
                print(f"[VectorStore] Error during neural encoding: {e}. Falling back to TF-IDF.")
                scores = self._tfidf_scores(query, texts)
        else:
            scores = self._tfidf_scores(query, texts)

        # Pair scores with chunks
        ranked_results = []
        for i, score in enumerate(scores):
            similarity = float(score)
            # Clip between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            chunk_copy = dict(filtered_chunks[i])
            chunk_copy["similarity"] = round(similarity, 4)
            ranked_results.append(chunk_copy)

        # Sort descending by similarity
        ranked_results.sort(key=lambda x: x["similarity"], reverse=True)
        return ranked_results[:top_k]

    def _tfidf_scores(self, query: str, texts: List[str]) -> np.ndarray:
        corpus = [query] + texts
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vec = tfidf_matrix[0:1]
            corpus_vecs = tfidf_matrix[1:]
            sims = cosine_similarity(query_vec, corpus_vecs)[0]
            return sims
        except Exception:
            return np.zeros(len(texts))

# Global vector store singleton
vector_store = VectorStore()
