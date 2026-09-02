LOK_SABHA_SCHEMAS = {
    "allocated_limit": {
        "required": ["source_house", "source_file", "source_row_number", "state"],
        "mp_field": "honble_members_of_parliaments",
        "has_constituency": True
    },
    "calamity_consent": {
        "required": ["source_house", "source_file", "source_row_number", "calamity_type", "calamity_name", "date_of_consent"],
        "has_constituency": False
    },
    "works_recommended": {
        "required": ["source_house", "source_file", "source_row_number", "work", "recommended_date"],
        "has_constituency": True
    },
    "works_sanctioned": {
        "required": ["source_house", "source_file", "source_row_number", "work", "sanction_date"],
        "has_constituency": True
    },
    "works_completed": {
        "required": ["source_house", "source_file", "source_row_number", "work", "completion_date"],
        "has_constituency": True
    },
    "expenditure": {
        "required": ["source_house", "source_file", "source_row_number", "work", "work_id", "expenditure_date"],
        "has_constituency": True
    }
}
