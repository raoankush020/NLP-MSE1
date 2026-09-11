import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ClaimVerifier:
    """Verifies claims strictly against the retrieved context without external knowledge."""

    def __init__(self):
        pass

    def verify_claims(
        self,
        claims: List[str],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not claims:
            return []

        # Extract all candidate sentences from retrieved context
        context_sentences = []
        for ch in retrieved_chunks:
            text = ch.get("content", "") or ch.get("text", "")
            raw_sents = re.split(r'(?<=[.!?])\s+', text)
            for s in raw_sents:
                clean_s = s.strip()
                if len(clean_s) > 10:
                    context_sentences.append({
                        "sentence": clean_s,
                        "source": ch.get("filename", ch.get("source", "Context")),
                        "page": ch.get("page_number", ch.get("page", 1))
                    })

        results = []
        for claim in claims:
            eval_result = self._verify_single_claim(claim, context_sentences)
            results.append(eval_result)

        return results

    def _verify_single_claim(
        self,
        claim: str,
        context_sentences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not context_sentences:
            return {
                "claim": claim,
                "classification": "UNSUPPORTED",
                "score": 0.0,
                "evidence": "No supporting evidence found.",
                "conflicting_text": None
            }

        # 1. Check for explicit contradiction
        contradiction = self._check_contradiction(claim, context_sentences)
        if contradiction:
            return {
                "claim": claim,
                "classification": "CONTRADICTED",
                "score": 0.0,
                "evidence": None,
                "conflicting_text": contradiction
            }

        # 2. Compute similarity against all context sentences
        claim_words = self._extract_content_words(claim)
        if not claim_words:
            return {
                "claim": claim,
                "classification": "UNSUPPORTED",
                "score": 0.0,
                "evidence": "No supporting evidence found.",
                "conflicting_text": None
            }

        best_score = 0.0
        best_sentence = None

        # Build corpus for TF-IDF
        sent_texts = [item["sentence"] for item in context_sentences]
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            tfidf = vectorizer.fit_transform([claim] + sent_texts)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:])[0]
        except Exception:
            sims = np.zeros(len(sent_texts))

        for idx, item in enumerate(context_sentences):
            sim = float(sims[idx]) if idx < len(sims) else 0.0
            
            # Entity & token overlap
            c_words = self._extract_content_words(item["sentence"])
            intersection = claim_words.intersection(c_words)
            overlap_ratio = len(intersection) / max(1, len(claim_words))

            # Combined match score (TF-IDF cosine + token recall)
            combined_score = (0.5 * sim) + (0.5 * overlap_ratio)

            if combined_score > best_score:
                best_score = combined_score
                best_sentence = item["sentence"]

        # Classification thresholds
        if best_score >= 0.65:
            return {
                "claim": claim,
                "classification": "SUPPORTED",
                "score": 1.0,
                "evidence": best_sentence,
                "conflicting_text": None
            }
        elif best_score >= 0.35:
            return {
                "claim": claim,
                "classification": "PARTIALLY_SUPPORTED",
                "score": 0.5,
                "evidence": best_sentence or "Partial context overlap detected.",
                "conflicting_text": None
            }
        else:
            return {
                "claim": claim,
                "classification": "UNSUPPORTED",
                "score": 0.0,
                "evidence": "No supporting evidence found.",
                "conflicting_text": None
            }

    def _check_contradiction(self, claim: str, context_sentences: List[Dict[str, Any]]) -> Optional[str]:
        claim_lower = claim.lower()
        claim_years = re.findall(r'\b(19\d\d|20\d\d)\b', claim)
        claim_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', claim)
        claim_content_words = self._extract_content_words(claim)

        negations = {"not", "never", "no", "neither", "none", "unable", "cannot", "failed", "denied"}
        has_negation = any(w in negations for w in claim_lower.split())

        for item in context_sentences:
            s_text = item["sentence"]
            s_lower = s_text.lower()
            s_words = self._extract_content_words(s_text)

            overlap = claim_content_words.intersection(s_words)
            # If sentences share majority of context subject/verbs
            if len(overlap) >= 3 or (len(claim_content_words) <= 3 and len(overlap) >= 2):
                # 1. Check Year / Date conflict
                if claim_years:
                    s_years = re.findall(r'\b(19\d\d|20\d\d)\b', s_text)
                    if s_years and not any(y in s_years for y in claim_years):
                        return f"Context states different date/year: '{s_text}'"

                # 2. Polarity / Negation conflict
                s_has_negation = any(w in negations for w in s_lower.split())
                if has_negation != s_has_negation:
                    # Direct polarity clash on identical subject
                    return f"Context indicates opposing polarity: '{s_text}'"

        return None

    def _extract_content_words(self, text: str) -> set:
        stopwords = {
            "a", "an", "the", "in", "on", "at", "by", "for", "with", "about",
            "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "to", "from", "up", "down", "of", "and", "or", "is",
            "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "it", "its", "this", "that", "these", "those"
        }
        tokens = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        return set(t for t in tokens if t not in stopwords and len(t) > 1)

claim_verifier = ClaimVerifier()
