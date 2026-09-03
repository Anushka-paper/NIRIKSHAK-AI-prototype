"""
Candidate Blocking and Pair Generator.
Indexes datasets by exact Work ID and blocks records by State + Constituency / MP to avoid O(N^2).
"""

from collections import defaultdict
import pandas as pd
from .column_mapper import ColumnMapper
from .normalizer import normalize_text, normalize_mp_name, normalize_constituency, normalize_work_id

class CandidateGenerator:
    """
    Generates candidate record pairs between two datasets using blocking techniques.
    """

    def __init__(self):
        self.column_mapper = ColumnMapper()

    def generate_candidate_blocks(self, df_a: pd.DataFrame, df_b: pd.DataFrame, 
                                   map_a: dict, map_b: dict) -> list[tuple[int, int, str]]:
        """
        Generates pairs of (row_idx_a, row_idx_b, match_strategy).
        Strategies:
          1. 'work_id_exact': Records with identical non-empty official work IDs.
          2. 'blocked_fuzzy': Records belonging to the same state/constituency/mp block.
        """
        candidate_pairs = set()

        col_wid_a = map_a.get("work_id")
        col_wid_b = map_b.get("work_id")

        # 1. Exact Work ID Indexing if available in both datasets
        if col_wid_a and col_wid_b:
            wid_index_b = defaultdict(list)
            for idx_b, wid_val in df_b[col_wid_b].items():
                norm_wid = normalize_work_id(wid_val)
                if norm_wid and norm_wid not in {"NAN", "NONE", "NULL", ""}:
                    wid_index_b[norm_wid].append(idx_b)

            for idx_a, wid_val in df_a[col_wid_a].items():
                norm_wid = normalize_work_id(wid_val)
                if norm_wid and norm_wid in wid_index_b:
                    for idx_b in wid_index_b[norm_wid]:
                        candidate_pairs.add((idx_a, idx_b, "work_id_exact"))

        # 2. Key-Based Blocking (State + Constituency or State + MP)
        # We block records that haven't been resolved by exact work ID
        col_state_a = map_a.get("state")
        col_const_a = map_a.get("constituency")
        col_mp_a = map_a.get("mp_name")

        col_state_b = map_b.get("state")
        col_const_b = map_b.get("constituency")
        col_mp_b = map_b.get("mp_name")

        # Determine best available blocking key
        if col_state_a and col_const_a and col_state_b and col_const_b:
            block_index_b = defaultdict(list)
            for idx_b, row in df_b.iterrows():
                st = normalize_text(row[col_state_b])
                co = normalize_constituency(row[col_const_b])
                if st and co:
                    block_index_b[(st, co)].append(idx_b)

            for idx_a, row in df_a.iterrows():
                st = normalize_text(row[col_state_a])
                co = normalize_constituency(row[col_const_a])
                if (st, co) in block_index_b:
                    # Cap max candidates per block to prevent blowout on huge districts
                    b_matches = block_index_b[(st, co)][:150]
                    for idx_b in b_matches:
                        if (idx_a, idx_b, "work_id_exact") not in candidate_pairs:
                            candidate_pairs.add((idx_a, idx_b, "blocked_fuzzy"))

        elif col_state_a and col_mp_a and col_state_b and col_mp_b:
            block_index_b = defaultdict(list)
            for idx_b, row in df_b.iterrows():
                st = normalize_text(row[col_state_b])
                mp = normalize_mp_name(row[col_mp_b])
                if st and mp:
                    block_index_b[(st, mp)].append(idx_b)

            for idx_a, row in df_a.iterrows():
                st = normalize_text(row[col_state_a])
                mp = normalize_mp_name(row[col_mp_a])
                if (st, mp) in block_index_b:
                    b_matches = block_index_b[(st, mp)][:150]
                    for idx_b in b_matches:
                        if (idx_a, idx_b, "work_id_exact") not in candidate_pairs:
                            candidate_pairs.add((idx_a, idx_b, "blocked_fuzzy"))

        return list(candidate_pairs)

