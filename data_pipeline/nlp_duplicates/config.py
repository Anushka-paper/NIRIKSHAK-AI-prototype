"""
Configuration for Section 9 Work/NLP Duplicate Detection Architecture (§9).
"""

# Default Config Priors (§9)
SIMILARITY_PRIOR = 0.80
AMOUNT_TOLERANCE_PCT = 0.15  # +/- 15% tolerance band
DATE_PROXIMITY_DAYS = 180    # 180 days date proximity window
MIN_LABELS_FOR_CALIBRATION = 20

# Config-Driven Abbreviation Dictionary for Indian Government Terminology (§9)
ABBREVIATIONS_DICT = {
    r"\bcc road\b": "cement concrete road",
    r"\bbt road\b": "black top road",
    r"\bpwd\b": "public works department",
    r"\bgp\b": "gram panchayat",
    r"\bps\b": "panchayat samiti",
    r"\bzp\b": "zilla parishad",
    r"\bro plant\b": "reverse osmosis plant",
    r"\bac\b": "assembly constituency",
    r"\bpc\b": "parliamentary constituency",
    r"\bphc\b": "primary health centre",
    r"\bchc\b": "community health centre",
    r"\bsub centre\b": "health sub centre",
    r"\bcomm hall\b": "community hall",
    r"\bdrg water\b": "drinking water",
    r"\bw/s\b": "water supply",
    r"\bboring\b": "borewell water supply"
}

# Boilerplate terms to strip during cleaning
BOILERPLATE_TERMS = [
    "construction of", "proposed construction of", "development of", "installation of",
    "supply and installation of", "execution of work", "under mplads scheme",
    "under mplads", "mplads work", "sanction for", "recommendation for"
]

