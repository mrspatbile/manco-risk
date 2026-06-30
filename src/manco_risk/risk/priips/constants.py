"""PRIIPs constants and regulatory lookup tables.

Commission Delegated Regulation (EU) 2017/653 Annex II:
SRI combination table (MRM class × CRM class).
"""

# PRIIPs SRI combination table from Delegated Regulation 2017/653 Annex II
# Rows: CRM class (1-6), Columns: MRM class (1-7)
# Value: Final SRI class (1-7)
# Format: SRI_COMBINATION_TABLE[crm_class][mrm_class] = sri_class
SRI_COMBINATION_TABLE = {
    1: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},  # CR1
    2: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},  # CR2
    3: {1: 3, 2: 3, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},  # CR3
    4: {1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 6, 7: 7},  # CR4
    5: {1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 6, 7: 7},  # CR5
    6: {1: 6, 2: 6, 3: 6, 4: 6, 5: 6, 6: 6, 7: 7},  # CR6
}

# Class ranges and defaults
SRI_MIN_CLASS: int = 1
SRI_MAX_CLASS: int = 7
MRM_MIN_CLASS: int = 1
MRM_MAX_CLASS: int = 7
CRM_MIN_CLASS: int = 1
CRM_MAX_CLASS: int = 6
CRM_DEFAULT_CLASS: int = 1  # Neutral credit risk; used when CRM is not applicable

# Performance scenario types
# Commission Delegated Regulation (EU) 2017/653 Annex IV/V
SCENARIO_TYPES = ["stress", "unfavourable", "moderate", "favourable"]

# Recommended Holding Period (RHP) validation
RHP_MIN_YEARS: int = 1
