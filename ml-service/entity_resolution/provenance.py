"""
Entity Provenance and Deterministic ID Manager.
Maintains source lineage and assigns deterministic Canonical Work IDs (CW_000001).
"""

class ProvenanceManager:
    """
    Manages entity provenance and deterministic canonical work IDs.
    """

    def __init__(self, id_prefix: str = "CW_"):
        self.id_prefix = id_prefix
        self.counter = 1
        self.record_to_canonical = {} # (dataset, row_id) -> canonical_id
        self.official_to_canonical = {} # official_work_id -> canonical_id

    def get_or_create_canonical_id(self, official_work_id: str | None, 
                                   source_dataset: str, source_row_id: int | str) -> str:
        """
        Retrieves existing canonical ID if entity already matched, or mints a new deterministic one.
        """
        key = (source_dataset, str(source_row_id))
        if key in self.record_to_canonical:
            return self.record_to_canonical[key]

        if official_work_id and official_work_id in self.official_to_canonical:
            can_id = self.official_to_canonical[official_work_id]
            self.record_to_canonical[key] = can_id
            return can_id

        # Mint new canonical ID
        new_id = f"{self.id_prefix}{self.counter:06d}"
        self.counter += 1

        self.record_to_canonical[key] = new_id
        if official_work_id:
            self.official_to_canonical[official_work_id] = new_id

        return new_id

    def link_entities(self, canonical_id: str, official_work_id: str | None,
                      dataset: str, row_id: int | str):
        """
        Links another record to an existing canonical ID.
        """
        key = (dataset, str(row_id))
        self.record_to_canonical[key] = canonical_id
        if official_work_id and official_work_id not in self.official_to_canonical:
            self.official_to_canonical[official_work_id] = canonical_id

