"""
Parliament-Specific Column Mapping Layer for NIRIKSHAK AI
"""

COLUMN_MAPPINGS = {
    "lok_sabha": {
        r'(?i)^sr\.?\s*no\.?$': 'sr_no',
        r'(?i)^state$': 'state',
        r'(?i)^(hon\'ble\s+members?\s+of\s+parliaments?|mp\s*name|parliamentarian|mp)$': 'mp_name',
        r'(?i)^constituency$': 'constituency',
        r'(?i)^district$': 'district',
        r'(?i)^(allocated\s+amount.*|allocation.*)$': 'allocated_amount',
        r'(?i)^(recommended\s+amount.*|recommendation\s+amount.*)$': 'recommended_amount',
        r'(?i)^(sanction\s+amount.*|sanctioned\s+amount.*)$': 'sanction_amount',
        r'(?i)^(amount\s+disbursed.*|fund\s+disbursed\s+amount.*|expenditure\s+amount.*|expenditure.*)$': 'expenditure_amount',
        r'(?i)^(work\s*id|project\s*id|work_id)$': 'work_id',
        r'(?i)^(ida|implementing\s+agency|agency)$': 'ida_agency',
        r'(?i)^(work\s+category|category)$': 'work_category',
        r'(?i)^(work\s+description|description|project\s+details|work)$': 'work_description',
        r'(?i)^(recommended\s+date|recommendation\s+date)$': 'recommended_date',
        r'(?i)^(sanction\s+date|sanctioned\s+date)$': 'sanction_date',
        r'(?i)^(completion\s+date|completed\s+date)$': 'completion_date',
        r'(?i)^(expenditure\s+date|payment\s+date)$': 'expenditure_date',
        r'(?i)^(work\s+status|status|payment\s+status)$': 'work_status',
        r'(?i)^(vendor\s+name|vendor)$': 'vendor_name'
    },
    "rajya_sabha": {
        r'(?i)^sr\.?\s*no\.?$': 'sr_no',
        r'(?i)^state$': 'state',
        r'(?i)^(hon\'ble\s+members?\s+of\s+parliaments?|mp\s*name|parliamentarian|mp|member)$': 'mp_name',
        r'(?i)^(constituency|nodal\s+district|district)$': 'constituency',
        r'(?i)^(allocated\s+amount.*|allocation.*)$': 'allocated_amount',
        r'(?i)^(recommended\s+amount.*|recommendation\s+amount.*)$': 'recommended_amount',
        r'(?i)^(sanction\s+amount.*|sanctioned\s+amount.*)$': 'sanction_amount',
        r'(?i)^(amount\s+disbursed.*|fund\s+disbursed\s+amount.*|expenditure\s+amount.*|expenditure.*)$': 'expenditure_amount',
        r'(?i)^(work\s*id|project\s*id|work_id)$': 'work_id',
        r'(?i)^(ida|implementing\s+agency|agency)$': 'ida_agency',
        r'(?i)^(work\s+category|category)$': 'work_category',
        r'(?i)^(work\s+description|description|project\s+details|work)$': 'work_description',
        r'(?i)^(recommended\s+date|recommendation\s+date)$': 'recommended_date',
        r'(?i)^(sanction\s+date|sanctioned\s+date)$': 'sanction_date',
        r'(?i)^(completion\s+date|completed\s+date)$': 'completion_date',
        r'(?i)^(expenditure\s+date|payment\s+date)$': 'expenditure_date',
        r'(?i)^(work\s+status|status|payment\s+status)$': 'work_status'
    }
}
