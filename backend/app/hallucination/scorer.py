from typing import List, Dict, Any

class HallucinationScorer:
    """Computes support and hallucination scores and maps to standard classification tiers."""

    SCORE_WEIGHTS = {
        "SUPPORTED": 1.0,
        "PARTIALLY_SUPPORTED": 0.5,
        "UNSUPPORTED": 0.0,
        "CONTRADICTED": 0.0,
    }

    def calculate_scores(self, evaluated_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not evaluated_claims:
            return {
                "support_score": 0.0,
                "hallucination_score": 1.0,
                "classification": "HIGH_HALLUCINATION",
                "hallucinated": True
            }

        total_score = sum(c.get("score", 0.0) for c in evaluated_claims)
        num_claims = len(evaluated_claims)

        support_score = round(total_score / num_claims, 4)
        hallucination_score = round(1.0 - support_score, 4)

        # Classification based on support score tiers:
        # 0.00 - 0.39 -> HIGH HALLUCINATION
        # 0.40 - 0.69 -> MEDIUM HALLUCINATION
        # 0.70 - 0.89 -> LOW HALLUCINATION
        # 0.90 - 1.00 -> NOT HALLUCINATED
        if support_score >= 0.90:
            classification = "NOT_HALLUCINATED"
            hallucinated = False
        elif support_score >= 0.70:
            classification = "LOW_HALLUCINATION"
            hallucinated = False
        elif support_score >= 0.40:
            classification = "MEDIUM_HALLUCINATION"
            hallucinated = True
        else:
            classification = "HIGH_HALLUCINATION"
            hallucinated = True

        return {
            "support_score": support_score,
            "hallucination_score": hallucination_score,
            "classification": classification,
            "hallucinated": hallucinated
        }

hallucination_scorer = HallucinationScorer()
