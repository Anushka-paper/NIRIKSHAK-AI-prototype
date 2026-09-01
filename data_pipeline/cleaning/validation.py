def validate_record_schema(record, source_house, dataset_type):
    if record.get('source_house') != source_house:
        return False, "Source house tag mismatch"
        
    if dataset_type == 'allocated_limit':
        if not record.get('honble_members_of_parliaments') and not record.get('honble_members_of_parliament'):
            return False, "Missing MP name"
    return True, "Valid"
