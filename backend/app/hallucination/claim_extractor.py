import re
from typing import List


class ClaimExtractor:
    """
    Decomposes a generated answer into individual atomic, verifiable claims.

    Key design goals:
    - Each claim should be one fact that can stand alone.
    - Avoid extracting generic/filler phrases that have no factual content
      (e.g. "The context does not mention X" or "Based on the above...").
    - Short, non-informative sentences are filtered out.
    """

    # Minimum character length for a claim to be considered
    MIN_CLAIM_LEN = 15

    # Phrases that indicate meta-commentary rather than factual claims
    FILLER_PATTERNS = [
        r'^based on (the|this|that)',
        r'^according to (the|this)',
        r'^as (mentioned|stated|noted|described)',
        r'^the (context|document|text|passage) (does not|doesn\'t|mentions|states)',
        r'^(in summary|to summarize|in conclusion|overall|therefore)',
        r'^(please note|note that|it (is|should be) noted)',
        r'^i (could not|cannot|don\'t|do not)',
        r'^(yes|no|sure|certainly|absolutely)[,.]?\s*$',
    ]
    _filler_re = [re.compile(p, re.IGNORECASE) for p in FILLER_PATTERNS]

    def extract_claims(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        # 1. Clean markdown, citations, source annotations
        cleaned = re.sub(r'\[(?:Source|Page|\d+)[^\]]*\]', '', text)
        cleaned = re.sub(r'[*_`#>]', '', cleaned)
        cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()

        # 2. Split into sentences (handle abbreviations naively)
        raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', cleaned)
        sentences = [s.strip() for s in raw_sentences
                     if s.strip() and len(s.strip()) >= self.MIN_CLAIM_LEN]

        # 3. Filter out filler / meta-commentary sentences
        sentences = [s for s in sentences if not self._is_filler(s)]

        # 4. Atomise each sentence
        claims: List[str] = []
        for sent in sentences:
            atomic = self._decompose_sentence(sent)
            claims.extend(atomic)

        # Fallback: if nothing survived, use raw sentences
        if not claims and sentences:
            claims = sentences

        # 5. Deduplicate while preserving order
        unique_claims: List[str] = []
        seen: set = set()
        for c in claims:
            c_clean = c.strip().rstrip('.')
            if c_clean and c_clean.lower() not in seen and len(c_clean) >= self.MIN_CLAIM_LEN:
                unique_claims.append(c_clean + ".")
                seen.add(c_clean.lower())

        return unique_claims

    # ------------------------------------------------------------------
    # Sentence decomposition
    # ------------------------------------------------------------------

    def _decompose_sentence(self, sentence: str) -> List[str]:
        """Break a compound sentence into simpler atomic claims."""

        # Pattern: "X was created/founded/invented by Y in YEAR"
        m = re.match(
            r'^(.*?)\s+was\s+(created|founded|invented|written|developed|built)\s+by\s+(.*?)\s+in\s+(\d{4}|\w+\s+\d{4})(.*)?$',
            sentence, re.IGNORECASE
        )
        if m:
            subj   = m.group(1).strip()
            verb   = m.group(2).strip()
            agent  = m.group(3).strip()
            year   = m.group(4).strip()
            tail   = (m.group(5) or "").strip()
            parts  = [
                f"{subj} was {verb} by {agent}.",
                f"{subj} was {verb} in {year}." + (f" {tail}" if tail else ""),
            ]
            return [p for p in parts if len(p) >= self.MIN_CLAIM_LEN]

        # Pattern: coordinating conjunctions separating independent clauses
        # Only split on ", and " or "; " where what follows starts with a
        # pronoun or uppercase (likely an independent clause).
        clauses = re.split(r',\s+and\s+(?=[A-Z\w])|;\s*', sentence)
        if len(clauses) > 1:
            results = []
            for cl in clauses:
                cl_clean = cl.strip()
                if len(cl_clean) >= self.MIN_CLAIM_LEN:
                    results.append(cl_clean.rstrip('.') + ".")
            if len(results) > 1:
                return results

        # Single claim — return as-is
        return [sentence.rstrip('.') + "."]

    # ------------------------------------------------------------------
    # Filler / meta-commentary detection
    # ------------------------------------------------------------------

    def _is_filler(self, sentence: str) -> bool:
        for pattern in self._filler_re:
            if pattern.search(sentence):
                return True
        return False


claim_extractor = ClaimExtractor()
