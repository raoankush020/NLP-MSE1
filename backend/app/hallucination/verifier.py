import re
import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ClaimVerifier:
    """
    Verifies claims against retrieved context using multi-signal analysis:
      - TF-IDF cosine similarity (lexical)
      - Token-level precision & recall (Jaccard-like F1)
      - Entity / number / date exactness penalty
      - Negation / polarity flip detection
      - Specificity weighting (longer, more specific claims are harder to satisfy)
    Returns a continuous score in [0, 1] instead of coarse 0/0.5/1.0 buckets.
    """

    # ---- thresholds -------------------------------------------------------
    SUPPORTED_THRESHOLD      = 0.55   # > this → SUPPORTED
    PARTIAL_THRESHOLD        = 0.28   # > this → PARTIALLY_SUPPORTED
    # anything below PARTIAL_THRESHOLD → UNSUPPORTED

    def verify_claims(
        self,
        claims: List[str],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not claims:
            return []

        context_sentences = self._extract_context_sentences(retrieved_chunks)
        full_context = " ".join([item["sentence"] for item in context_sentences])

        results = []
        for claim in claims:
            eval_result = self._verify_single_claim(claim, context_sentences, full_context)
            results.append(eval_result)

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_context_sentences(self, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict]:
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
        return context_sentences

    def _verify_single_claim(
        self,
        claim: str,
        context_sentences: List[Dict[str, Any]],
        full_context: str
    ) -> Dict[str, Any]:
        if not context_sentences:
            return self._make_result(claim, "UNSUPPORTED", 0.0, "No context available.", None)

        # 1. Hard contradiction check first
        contradiction = self._check_contradiction(claim, context_sentences)
        if contradiction:
            return self._make_result(claim, "CONTRADICTED", 0.0, None, contradiction)

        claim_words = self._extract_content_words(claim)
        if not claim_words:
            return self._make_result(claim, "UNSUPPORTED", 0.0, "Claim has no content words.", None)

        sent_texts = [item["sentence"] for item in context_sentences]

        # 2. TF-IDF similarity (claim vs each sentence)
        tfidf_sims = self._tfidf_similarities(claim, sent_texts)

        # 3. Find best sentence by multi-signal score
        best_score = 0.0
        best_sentence = None
        best_details = {}

        for idx, item in enumerate(context_sentences):
            sent = item["sentence"]
            sent_words = self._extract_content_words(sent)

            tfidf_sim = float(tfidf_sims[idx]) if idx < len(tfidf_sims) else 0.0

            # Token recall: fraction of claim words found in sentence
            overlap = claim_words.intersection(sent_words)
            token_recall = len(overlap) / max(1, len(claim_words))

            # Token precision: fraction of sentence words that appear in claim
            token_precision = len(overlap) / max(1, len(sent_words))

            # F1 of token overlap
            if token_recall + token_precision > 0:
                token_f1 = 2 * token_recall * token_precision / (token_recall + token_precision)
            else:
                token_f1 = 0.0

            # Entity / number exactness: penalise if claim mentions specific
            # numbers/years that are absent or different in the sentence
            entity_score = self._entity_match_score(claim, sent)

            # Combined score (weighted)
            combined = (
                0.35 * tfidf_sim +
                0.30 * token_f1 +
                0.20 * token_recall +
                0.15 * entity_score
            )

            # Specificity penalty: very specific claims (many unique content words)
            # that only partially overlap should be harder to classify as SUPPORTED
            specificity_factor = self._specificity_factor(claim_words, overlap)
            adjusted = combined * specificity_factor

            if adjusted > best_score:
                best_score = adjusted
                best_sentence = sent
                best_details = {
                    "tfidf": round(tfidf_sim, 3),
                    "token_f1": round(token_f1, 3),
                    "entity": round(entity_score, 3),
                    "specificity_factor": round(specificity_factor, 3),
                }

        # 4. Also check claim vs full context (aggregate) – prevents false
        #    negatives when claim info is spread across multiple sentences
        agg_score = self._aggregate_context_score(claim, claim_words, sent_texts, tfidf_sims)
        # Take the max of sentence-level and aggregate
        final_score = round(max(best_score, agg_score * 0.85), 4)  # slight discount for aggregate

        # 5. Classify
        if final_score >= self.SUPPORTED_THRESHOLD:
            classification = "SUPPORTED"
        elif final_score >= self.PARTIAL_THRESHOLD:
            classification = "PARTIALLY_SUPPORTED"
        else:
            classification = "UNSUPPORTED"
            best_sentence = None

        return self._make_result(
            claim, classification, final_score,
            best_sentence if classification != "UNSUPPORTED" else "No supporting evidence found.",
            None
        )

    def _tfidf_similarities(self, claim: str, sent_texts: List[str]) -> np.ndarray:
        if not sent_texts:
            return np.array([])
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                min_df=1,
                sublinear_tf=True  # log-scale TF, reduces dominance of common terms
            )
            corpus = [claim] + sent_texts
            tfidf = vectorizer.fit_transform(corpus)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:])[0]
            return sims
        except Exception:
            return np.zeros(len(sent_texts))

    def _aggregate_context_score(
        self,
        claim: str,
        claim_words: set,
        sent_texts: List[str],
        tfidf_sims: np.ndarray
    ) -> float:
        """Score claim against the *union* of top-N sentences."""
        if not sent_texts:
            return 0.0

        # Pick top-3 sentences by tfidf similarity
        top_indices = np.argsort(tfidf_sims)[::-1][:3]
        top_sents = " ".join(sent_texts[i] for i in top_indices if i < len(sent_texts))
        top_words = self._extract_content_words(top_sents)

        overlap = claim_words.intersection(top_words)
        recall = len(overlap) / max(1, len(claim_words))

        # average tfidf of top sentences
        avg_tfidf = float(np.mean([tfidf_sims[i] for i in top_indices if i < len(tfidf_sims)]))

        return (0.5 * recall + 0.5 * avg_tfidf)

    def _entity_match_score(self, claim: str, sentence: str) -> float:
        """
        Returns a score 0–1 based on how well numbers/years/capitalised entities
        in the claim appear in the sentence.
        Penalises heavily when specific entities in the claim are absent.
        """
        # Extract years, numbers, and capitalised tokens (proper nouns)
        claim_entities = set(re.findall(r'\b\d+(?:[.,]\d+)?\b', claim))
        claim_entities |= set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', claim))

        if not claim_entities:
            return 1.0  # no entities to check → neutral

        sent_text_lower = sentence.lower()
        matches = sum(
            1 for e in claim_entities
            if e.lower() in sent_text_lower
        )
        return matches / len(claim_entities)

    def _specificity_factor(self, claim_words: set, overlap: set) -> float:
        """
        Penalises vague matches on highly specific claims.
        If a claim has many content words but very few overlap,
        the factor reduces the score further.
        """
        n = len(claim_words)
        if n == 0:
            return 1.0
        overlap_ratio = len(overlap) / n

        # Smooth factor: for a claim with 10+ words, demand higher overlap
        if n >= 10:
            # Scale: full match → 1.0; 50% match → ~0.7; 25% → ~0.5
            return max(0.3, overlap_ratio ** 0.5)
        elif n >= 5:
            return max(0.4, overlap_ratio ** 0.4)
        else:
            # Short claims — be more lenient
            return max(0.6, overlap_ratio ** 0.3)

    # ------------------------------------------------------------------
    # Contradiction detection
    # ------------------------------------------------------------------

    def _check_contradiction(
        self,
        claim: str,
        context_sentences: List[Dict[str, Any]]
    ) -> Optional[str]:
        claim_lower = claim.lower()
        claim_years   = set(re.findall(r'\b(19\d\d|20\d\d)\b', claim))
        claim_numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', claim)
        claim_content = self._extract_content_words(claim)

        negations = {"not", "never", "no", "neither", "none", "unable",
                     "cannot", "can't", "failed", "denied", "without",
                     "doesn't", "don't", "didn't", "isn't", "aren't",
                     "wasn't", "weren't"}
        claim_has_neg = any(w in negations for w in claim_lower.split())

        for item in context_sentences:
            s_text  = item["sentence"]
            s_lower = s_text.lower()
            s_words = self._extract_content_words(s_text)

            overlap = claim_content.intersection(s_words)
            # Require meaningful topical overlap before flagging contradiction
            sufficient_overlap = (
                len(overlap) >= 3 or
                (len(claim_content) <= 4 and len(overlap) >= 2)
            )
            if not sufficient_overlap:
                continue

            # 1. Year / date conflict
            if claim_years:
                s_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', s_text))
                if s_years and claim_years.isdisjoint(s_years):
                    return f"Context states different year/date: '{s_text}'"

            # 2. Numeric value conflict (only flag when numbers are significant)
            if claim_numbers:
                s_numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', s_text)
                if s_numbers:
                    # Check if any claim number is significantly different
                    for cn in claim_numbers:
                        try:
                            cn_val = float(cn.replace(',', ''))
                        except ValueError:
                            continue
                        for sn in s_numbers:
                            try:
                                sn_val = float(sn.replace(',', ''))
                                # Flag if same order of magnitude but different value
                                if cn_val != sn_val and cn_val > 0 and sn_val > 0:
                                    if 0.1 < (cn_val / sn_val) < 10:  # same ballpark, different value
                                        return f"Context states a different value ({sn}) vs claim ({cn}): '{s_text}'"
                            except ValueError:
                                continue

            # 3. Negation polarity flip
            s_has_neg = any(w in negations for w in s_lower.split())
            if claim_has_neg != s_has_neg:
                return f"Context indicates opposing polarity: '{s_text}'"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _extract_content_words(self, text: str) -> set:
        stopwords = {
            "a", "an", "the", "in", "on", "at", "by", "for", "with", "about",
            "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "to", "from", "up", "down", "of", "and", "or", "is",
            "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "it", "its", "this", "that", "these", "those", "also",
            "which", "who", "whom", "when", "where", "why", "how", "if", "then",
            "than", "so", "as", "but", "yet", "both", "either", "each", "all",
            "any", "some", "such", "can", "will", "would", "could", "should",
            "may", "might", "must", "shall", "very", "just", "more", "most",
            "other", "same", "their", "they", "them", "we", "our", "you", "your",
            "he", "she", "his", "her", "my", "i", "me", "us"
        }
        tokens = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        return {t for t in tokens if t not in stopwords and len(t) > 1}

    def _make_result(
        self,
        claim: str,
        classification: str,
        score: float,
        evidence: Optional[str],
        conflicting_text: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "claim": claim,
            "classification": classification,
            "score": score,
            "evidence": evidence,
            "conflicting_text": conflicting_text
        }


claim_verifier = ClaimVerifier()
