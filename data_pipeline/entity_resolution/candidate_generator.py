def get_mp_candidates(norm_name, house, state, master_mps):
    candidates = []
    for mp in master_mps:
        if house and mp.get("source_house") == house:
            candidates.append(mp)
        elif state and mp.get("canonical_state") == state:
            candidates.append(mp)
    return candidates if candidates else master_mps

def get_vendor_candidates(norm_vendor, state, master_vendors):
    if not master_vendors:
        return []
    prefix = norm_vendor[:2] if len(norm_vendor) >= 2 else norm_vendor
    filtered = [v for v in master_vendors if v.get("norm_name", "").startswith(prefix) or v.get("canonical_state") == state]
    return filtered if filtered else master_vendors
