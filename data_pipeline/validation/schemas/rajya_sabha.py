RAJYA_SABHA_SCHEMAS = {
    "allocated_limit": {
        "required": ["source_house", "source_file", "source_row_number", "state", "elected/nominated"],
        "mp_field": "honble_members_of_parliament",
        "has_constituency": False
    },
    "calamity_consent": {
        "required": ["source_house", "source_file", "source_row_number", "calamity_type", "calamity_name", "date_of_consent"],
        "has_constituency": False
    },
    "works_recommended": {
        "required": ["source_house", "source_file", "source_row_number", "work", "elected/nominated", "recommended_date"],
        "has_constituency": False
    },
    "works_sanctioned": {
        "required": ["source_house", "source_file", "source_row_number", "work", "elected/nominated", "sanction_date"],
        "has_constituency": False
    },
    "works_completed": {
        "required": ["source_house", "source_file", "source_row_number", "work", "elected/nominated", "completion_date"],
        "has_constituency": False
    },
    "expenditure": {
        "required": ["source_house", "source_file", "source_row_number", "work", "work_id", "elected/nominated", "expenditure_date"],
        "has_constituency": False
    }
}
