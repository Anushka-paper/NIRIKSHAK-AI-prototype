import re

# Comprehensive Indian States and Union Territories Mapping
STATE_CANONICAL_MAPPING = {
    # Andhra Pradesh
    "ap": "Andhra Pradesh", "a.p.": "Andhra Pradesh", "andhra pradesh": "Andhra Pradesh",
    # Arunachal Pradesh
    "arunachal pradesh": "Arunachal Pradesh", "arunachal": "Arunachal Pradesh",
    # Assam
    "assam": "Assam", "as": "Assam",
    # Bihar
    "bihar": "Bihar", "br": "Bihar", "bihar_br": "Bihar",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh", "cg": "Chhattisgarh", "chattisgarh": "Chhattisgarh",
    # Goa
    "goa": "Goa",
    # Gujarat
    "gujarat": "Gujarat", "gj": "Gujarat",
    # Haryana
    "haryana": "Haryana", "hr": "Haryana",
    # Himachal Pradesh
    "hp": "Himachal Pradesh", "h.p.": "Himachal Pradesh", "himachal pradesh": "Himachal Pradesh",
    # Jharkhand
    "jharkhand": "Jharkhand", "jh": "Jharkhand",
    # Karnataka
    "karnataka": "Karnataka", "ka": "Karnataka",
    # Kerala
    "kerala": "Kerala", "kl": "Kerala",
    # Madhya Pradesh
    "mp": "Madhya Pradesh", "m.p.": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh",
    # Maharashtra
    "maharashtra": "Maharashtra", "mh": "Maharashtra",
    # Manipur
    "manipur": "Manipur",
    # Meghalaya
    "meghalaya": "Meghalaya",
    # Mizoram
    "mizoram": "Mizoram",
    # Nagaland
    "nagaland": "Nagaland",
    # Odisha
    "odisha": "Odisha", "orissa": "Odisha", "or": "Odisha",
    # Punjab
    "punjab": "Punjab", "pb": "Punjab",
    # Rajasthan
    "rajasthan": "Rajasthan", "rj": "Rajasthan",
    # Sikkim
    "sikkim": "Sikkim",
    # Tamil Nadu
    "tn": "Tamil Nadu", "t.n.": "Tamil Nadu", "tamil nadu": "Tamil Nadu", "tamilnadu": "Tamil Nadu",
    # Telangana
    "telangana": "Telangana", "ts": "Telangana", "tg": "Telangana",
    # Tripura
    "tripura": "Tripura",
    # Uttar Pradesh
    "up": "Uttar Pradesh", "u.p.": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh", "hamirpur_up": "Uttar Pradesh",
    # Uttarakhand
    "uttarakhand": "Uttarakhand", "uk": "Uttarakhand", "uttaranchal": "Uttarakhand",
    # West Bengal
    "wb": "West Bengal", "w.b.": "West Bengal", "west bengal": "West Bengal", "paschim banga": "West Bengal",
    # Union Territories
    "andaman and nicobar islands": "Andaman and Nicobar Islands", "a&n islands": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi", "nct of delhi": "Delhi", "dl": "Delhi", "new delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir", "j&k": "Jammu and Kashmir", "jk": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry", "pondicherry": "Puducherry"
}

# Column Name Canonical Synonym Mappings
COLUMN_NAME_SYNONYM_MAP = {
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
    r'(?i)^(vendor\s+name|vendor)$': 'vendor_name',
    r'(?i)^(calamity\s+name)$': 'calamity_name',
    r'(?i)^(calamity\s+type)$': 'calamity_type'
}

# Tokens representing Missing/NaN Values
MISSING_VALUE_TOKENS = {
    "", " ", "na", "n/a", "na/", "/na", "null", "none", "-", "--", "not available", "nil", "n.a.", "undefined"
}

# Common Person Name Honorifics
PERSON_HONORIFICS = r'(?i)\b(shri|smt|dr|mr|mrs|ms|prof|hon\'ble|honble|adv)\b'

# Work Status Taxonomy Canonical Mapping
STATUS_CANONICAL_MAPPING = {
    "completed": "Completed", "complete": "Completed", "finish": "Completed", "finished": "Completed",
    "ongoing": "Ongoing", "in progress": "Ongoing", "in-progress": "Ongoing", "wip": "Ongoing",
    "sanctioned": "Sanctioned", "approved": "Sanctioned",
    "pending": "Pending", "recommended": "Recommended", "proposed": "Recommended",
    "rejected": "Rejected", "cancelled": "Cancelled", "canceled": "Cancelled"
}

# Work Category Vocabulary Mapping
CATEGORY_VOCABULARY = [
    (r'(?i)(road|bridge|culvert|path|footpath|pavement|highway|street|lane)', 'Roads & Bridges'),
    (r'(?i)(water|tube\s*well|hand\s*pump|sanitation|drain|sewage|toilet|swachh)', 'Drinking Water & Sanitation'),
    (r'(?i)(school|college|education|library|classroom|hostel|computer)', 'Education & Skill Development'),
    (r'(?i)(hospital|health|dispensary|clinic|ambulance|medical|phc|chc)', 'Health & Medical Infrastructure'),
    (r'(?i)(community|hall|kalyan|auditorium|bhavan|shelter|stage|stadium|sports)', 'Community Halls & Infrastructure'),
    (r'(?i)(solar|electric|light|power|generator|transformer|energy)', 'Electricity & Renewable Energy'),
    (r'(?i)(park|tree|irrigation|canal|pond|lake|boundry|wall)', 'Irrigation & Environment'),
]

