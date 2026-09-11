from typing import List, Dict, Any


class HallucinationScorer:
    """
    Computes support and hallucination scores from per-claim evaluation results.

    Per-claim scores are now continuous floats in [0, 1] (from the improved
    ClaimVerifier), so the weighted average produces a meaningful distribution
    instead of always landing near 1.0.

    Classification tiers:
      ≥ 0.75  → NOT_HALLUCINATED    (well-grounded)
      ≥ 0.50  → LOW_HALLUCINATION   (mostly grounded, minor gaps)
      ≥ 0.25  → MEDIUM_HALLUCINATION
      <  0.25 → HIGH_HALLUCINATION
    """

    # Classification label weights when combining different verdict types
    CLASSIFICATION_WEIGHTS = {
        "SUPPORTED":          1.0,
        "PARTIALLY_SUPPORTED": 0.45,   # was 0.5 — slightly penalised
        "UNSUPPORTED":        0.0,
        "CONTRADICTED":      -0.1,     # negative pull on average
    }

    # Tier thresholds (applied to the normalised support score)
    TIER_NOT_HALLUCINATED  = 0.75
    TIER_LOW               = 0.50
    TIER_MEDIUM            = 0.25

    def calculate_scores(self, evaluated_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not evaluated_claims:
            return {
                "support_score": 0.0,
                "hallucination_score": 1.0,
                "classification": "HIGH_HALLUCINATION",
                "hallucinated": True,
                "claim_breakdown": {}
            }

        # ----------------------------------------------------------------
        # Use the raw continuous score emitted by the verifier (0–1 float)
        # plus a classification-level weight to produce the final average.
        # Contradicted claims can pull the average below their raw score.
        # ----------------------------------------------------------------
        weighted_scores = []
        breakdown = {"SUPPORTED": 0, "PARTIALLY_SUPPORTED": 0,
                     "UNSUPPORTED": 0, "CONTRADICTED": 0}

        for c in evaluated_claims:
            raw = float(c.get("score", 0.0))
            verdict = c.get("classification", "UNSUPPORTED")
            breakdown[verdict] = breakdown.get(verdict, 0) + 1

            # Blend: 70% continuous verifier score + 30% classification weight
            cls_weight = self.CLASSIFICATION_WEIGHTS.get(verdict, 0.0)
            blended = 0.70 * raw + 0.30 * max(0.0, cls_weight)
            weighted_scores.append(blended)

        support_score = round(sum(weighted_scores) / len(weighted_scores), 4)
        # Clamp to [0, 1]
        support_score = max(0.0, min(1.0, support_score))
        hallucination_score = round(1.0 - support_score, 4)

        # Tier classification
        if support_score >= self.TIER_NOT_HALLUCINATED:
            classification = "NOT_HALLUCINATED"
            hallucinated = False
        elif support_score >= self.TIER_LOW:
            classification = "LOW_HALLUCINATION"
            hallucinated = False
        elif support_score >= self.TIER_MEDIUM:
            classification = "MEDIUM_HALLUCINATION"
            hallucinated = True
        else:
            classification = "HIGH_HALLUCINATION"
            hallucinated = True

        return {
            "support_score": support_score,
            "hallucination_score": hallucination_score,
            "classification": classification,
            "hallucinated": hallucinated,
            "claim_breakdown": breakdown
        }


hallucination_scorer = HallucinationScorer()
