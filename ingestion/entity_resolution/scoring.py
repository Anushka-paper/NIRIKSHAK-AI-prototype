from ingestion.entity_resolution.similarity import SimilarityEngine

class ContextualScorer:
    """
    Weighted Contextual Match Scorer.
    Combines string similarity with contextual metadata (constituency, state, house, registration_no).
    """

    DEFAULT_WEIGHTS = {
        "name_similarity": 0.50,
        "registration_match": 0.25,
        "constituency_match": 0.15,
        "state_match": 0.05,
        "house_match": 0.05
    }

    @classmethod
    def calculate_match_score(cls, 
                              norm_name1: str, 
                              norm_name2: str,
                              context1: dict = None, 
                              context2: dict = None,
                              weights: dict = None) -> tuple[float, dict]:
        """
        Calculates composite match score between two entities given names and contextual attributes.
        Returns composite score float and features breakdown dict.
        """
        w = weights or cls.DEFAULT_WEIGHTS
        ctx1 = context1 or {}
        ctx2 = context2 or {}

        # 1. Name Similarity
        name_sim = SimilarityEngine.composite_string_similarity(norm_name1, norm_name2)

        # 2. Registration Match (Strongest signal if present)
        reg1 = ctx1.get("registration_number")
        reg2 = ctx2.get("registration_number")
        reg_match = 1.0 if (reg1 and reg2 and reg1 == reg2) else (0.0 if (reg1 and reg2) else 0.5)

        # 3. Constituency Match
        const1 = ctx1.get("constituency_id")
        const2 = ctx2.get("constituency_id")
        const_match = 1.0 if (const1 and const2 and const1 == const2) else (0.0 if (const1 and const2) else 0.5)

        # 4. State Match
        st1 = ctx1.get("state_id")
        st2 = ctx2.get("state_id")
        st_match = 1.0 if (st1 and st2 and st1 == st2) else (0.0 if (st1 and st2) else 0.5)

        # 5. House Match
        h1 = ctx1.get("house")
        h2 = ctx2.get("house")
        h_match = 1.0 if (h1 and h2 and h1 == h2) else (0.0 if (h1 and h2) else 0.5)

        features = {
            "name_similarity": name_sim,
            "registration_match": reg_match,
            "constituency_match": const_match,
            "state_match": st_match,
            "house_match": h_match
        }

        # Override: If registration number matches exactly, set high score directly!
        if reg1 and reg2 and reg1 == reg2:
            return 1.0, features

        # Composite score sum
        composite_score = (
            w["name_similarity"] * name_sim +
            w["registration_match"] * reg_match +
            w["constituency_match"] * const_match +
            w["state_match"] * st_match +
            w["house_match"] * h_match
        )

        return round(composite_score, 4), features

