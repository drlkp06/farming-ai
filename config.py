INTENTS_FILE = (
    "farming_domain/intents.json"
)

VECTOR_DB_FILE = (
    "knowledge_learning/vectors.pkl"
)

SEMANTIC_MEMORY_FILE = (
    "config_memory/semantic_memory.json"
)

INTENT_MEMORY_FILE = (
    "config_memory/intent_patterns.json"
)
# ==========================================
# QUERY MARKERS
# ==========================================

QUERY_MARKERS = [

    "kitna",
    "kitne",
    "kitni",

    "total",
    "history",

    "batao",
    "dikhao",

    "kab",

    "summary",

    "nikla",
    "nikle"

]

# ==========================================
# DATE WORDS
# ==========================================

DATE_WORDS = [

    "aaj",
    "kal",

    "parso",

    "today",
    "yesterday"

]
# ==========================================
# PAYMENT QUERY MARKERS
# ==========================================

PAYMENT_QUERY_MARKERS = [

    "payment",

    "rupye",
    "rupees",

    "diye",
    "diya"

]

# ==========================================
# HARVEST QUERY MARKERS
# ==========================================

HARVEST_QUERY_MARKERS = [

    "nikla",
    "nikle",
    "nikli",

    "kitni",
    "kitna",
    "kitne",

    "harvest",
    "tudai",
    "todai"

]
# ==========================================
# KNOWN UNITS MARKERS
# ==========================================
KNOWN_UNITS = [

    "kg",
    "kilo",
    "kilogram",

    "gram",

    "liter",
    "litre",

    "packet",
    "bag",

    "acre",
    "bigha"

]