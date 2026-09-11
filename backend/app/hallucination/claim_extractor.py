import re
from typing import List

class ClaimExtractor:
    """Decomposes generated answers into individual, verifiable atomic factual claims."""

    def extract_claims(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        # 1. Clean markdown formatting, citations like [1], [Source: ...], etc.
        cleaned = re.sub(r'\[(?:Source|Page|\d+)[^\]]*\]', '', text)
        cleaned = re.sub(r'[*_`#]', '', cleaned)
        cleaned = cleaned.strip()

        # 2. Split into sentences
        raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', cleaned)
        sentences = [s.strip() for s in raw_sentences if s.strip() and len(s.strip()) > 5]

        claims: List[str] = []
        for sent in sentences:
            atomic = self._decompose_sentence(sent)
            claims.extend(atomic)

        # Fallback if no atomic claims generated
        if not claims and sentences:
            claims = sentences

        # Deduplicate while preserving order
        unique_claims = []
        seen = set()
        for c in claims:
            c_clean = c.strip().rstrip('.')
            if c_clean and c_clean.lower() not in seen and len(c_clean) > 5:
                unique_claims.append(c_clean + ".")
                seen.add(c_clean.lower())

        return unique_claims

    def _decompose_sentence(self, sentence: str) -> List[str]:
        # Handle sentences with compound prepositions like "created by X in Y"
        # Example: "Python was created by Guido van Rossum in 1991."
        date_by_match = re.match(r'^(.*?)\s+was created by\s+(.*?)\s+in\s+(\d{4}|\w+\s+\d{4})(.*)$', sentence, re.IGNORECASE)
        if date_by_match:
            subj = date_by_match.group(1).strip()
            creator = date_by_match.group(2).strip()
            year = date_by_match.group(3).strip()
            tail = date_by_match.group(4).strip()
            return [
                f"{subj} was created by {creator}.",
                f"{subj} was created in {year}." + (f" {tail}" if tail else "")
            ]

        # Handle coordinating conjunctions ("and", "as well as") separating independent clauses
        clauses = re.split(r',\s*and\s+|\s+and\s+(?=[A-Z])|;\s*', sentence)
        if len(clauses) > 1:
            results = []
            for cl in clauses:
                cl_clean = cl.strip()
                if len(cl_clean) > 10:
                    results.append(cl_clean.rstrip('.') + ".")
            if results:
                return results

        # Single clause/claim
        return [sentence.rstrip('.') + "."]

claim_extractor = ClaimExtractor()
