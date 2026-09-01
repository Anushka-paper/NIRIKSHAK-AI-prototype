from collections import defaultdict
from typing import List, Dict

class CandidateGenerator:
    """
    Blocking and Indexing Engine for Candidate Generation.
    Prevents O(N^2) full pairwise comparisons by blocking candidates
    using first token, N-gram prefix, house, or state keys.
    """

    @staticmethod
    def build_block_key(normalized_name: str, state_id: int = None, house: str = None) -> str:
        """Generates a composite blocking key."""
        tokens = normalized_name.split()
        first_token = tokens[0] if tokens else "empty"
        
        prefix = first_token[:3] if len(first_token) >= 3 else first_token
        
        state_part = str(state_id) if state_id else "ALL"
        house_part = str(house)[:2].upper() if house else "ALL"
        
        return f"{prefix}_{state_part}_{house_part}"

    @classmethod
    def generate_candidate_blocks(cls, entity_list: List[Dict]) -> Dict[str, List[Dict]]:
        """Group entity list into candidate blocks by blocking key."""
        blocks = defaultdict(list)
        for entity in entity_list:
            key = cls.build_block_key(
                entity.get("normalized_name", ""),
                entity.get("state_id"),
                entity.get("house")
            )
            blocks[key].append(entity)
        return blocks

