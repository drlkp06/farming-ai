import re
from difflib import SequenceMatcher

from core_brain.semantic_engine import (
    blank_record
)

from memory_system.entity_memory import (
    load_entities
)

from knowledge_learning.learning import (
    load_vocab
)
from memory_system.dynamic_memory import load_dynamic_keywords

# ==========================================
# STATIC OPERATION KEYWORDS
# BOOTSTRAP SEMANTIC COGNITION
# ==========================================

STATIC_OPERATION_KEYWORDS = {

    # ==========================================
    # PAYMENT
    # ==========================================

    "payment": [

        "diye",
        "diya",

        "payment",
        "paid",

        "salary",
        "mazdoori",

        "worker",
        "labour",

        "advance"

    ],

    # ==========================================
    # EXPENSE
    # ==========================================

    "expense": [

        "expense",
        "kharcha",

        "diesel",
        "fuel",
        "petrol",

        "repair",
        "service",

        "maintenance",

        "bharwaya",
        "bharaya",

        "machine",
        "tractor"

    ],

    # ==========================================
    # TREATMENT
    # ==========================================

    "treatment": [

        # spray
        "spray",
        "chhidkaav",
        "chhidkav",
        "chhidkao",

        # fertilizer
        "fertilizer",
        "npk",
        "urea",
        "dap",

        # methods
        "drip",
        "drenching",
        "dressing",
        "fertigation",
        "broadcast",

        # treatment semantics
        "medicine",
        "pesticide",
        "fungicide",
        "insecticide"

    ],

    # ==========================================
    # HARVEST
    # ==========================================

    "harvest": [

        "nikla",
        "nikle",

        "harvest",

        "todai",
        "tudai",
        "toda",

        "production",
        "output",

        "yield"

    ],

    # ==========================================
    # PEST ATTACK
    # ==========================================

    "pest_attack": [

        "whitefly",
        "thrips",
        "mites",
        "aphid",
        "leaf miner"

    ]

}

def get_all_operation_keywords():
    dynamic_keywords = load_dynamic_keywords()
    all_keywords = {}
    
    # Merge Static and Dynamic
    for op in set(STATIC_OPERATION_KEYWORDS.keys()).union(dynamic_keywords.keys()):
        static_list = STATIC_OPERATION_KEYWORDS.get(op, [])
        dynamic_list = dynamic_keywords.get(op, [])
        all_keywords[op] = list(set(static_list + dynamic_list))
        
    return all_keywords
# ==========================================
# ENTITY TYPES
# ==========================================

ENTITY_TYPES = [

    "farm",
    "crop",
    "worker",
    "product",
    "vendor",
    "buyer"

]

# ==========================================
# FARM ALIASES
# ==========================================

FARM_ALIASES = {

    "satpuda farm": "satpuda",
    "rajpura farm": "rajpura",

}

# ==========================================
# QUERY WORDS
# ==========================================

QUERY_WORDS = [

    "kitna",
    "kitne",
    "kitni",
    "kitana",
    "kab",

    "history",

    "dikhao",
    "batao",

    "abtak",

    "summary",
    "report",

    "kaunsa",
    "konsa"


]
# ==========================================
# APPLICATION METHODS
# ==========================================

APPLICATION_METHODS = [

    "drip",
    "foliar",
    "drenching",
    "dressing",
    "broadcast",
    "basal",
    "fertigation",
    "soil",
    "rootzone",
    "spray"

]

# ==========================================
# TREATMENT TYPES
# ==========================================

TREATMENT_TYPES = [

    "spray",
    "fertilizer",
    "fungicide",
    "insecticide",
    "micronutrient",
    "soil_amendment",
    "growth_regulator",
    "bio_stimulant"

]
# ==========================================
# HELPERS
# ==========================================


def normalize_text(text):

    text = text.lower().strip()

    for alias, real_name in FARM_ALIASES.items():

        text = text.replace(
            alias,
            real_name
        )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ==========================================
# TOKENS
# ==========================================


def get_tokens(text):

    return re.findall(
        r"[a-zA-Z0-9_]+",
        text.lower()
    )


# ==========================================
# NUMBER EXTRACTION
# ==========================================


def get_first_number(text):

    match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    if not match:

        return None

    value = match.group()

    if "." in value:

        return float(value)

    return int(value)
# ==========================================
# QUANTITY EXTRACTION
# ==========================================
def get_quantity_before_unit(text):

    match = re.search(

        r"(\d+(?:\.\d+)?)\s*(kg|kilo|liter|litre|gram|ml)",

        text

    )

    if not match:
        return None

    return float(match.group(1))
# ==========================================
# UNIT EXTRACTION
# ==========================================

def detect_unit(text):

    units = [

        "kg",
        "kilo",
        "litre",
        "liter",
        "ml",
        "gram"

    ]

    for unit in units:

        if unit in text:

            return unit

    return None

# ==========================================
# FERTILIZER GRADE EXTRACTION
# ==========================================

def extract_fertilizer_grade(text):

    pattern = r"\d{1,2}[.:]\d{1,2}[.:]\d{1,2}"

    match = re.search(
        pattern,
        text
    )

    if not match:

        return None

    grade = match.group()

    grade = grade.replace(".", ":")

    return grade
# ==========================================
# EXTRACT APPLICATION METHOD
# ==========================================

def extract_application_method(text):

    text = text.lower()

    for method in APPLICATION_METHODS:

        if method in text:

            return method

    return None


# ==========================================
# EXTRACT TREATMENT TYPE
# ==========================================

def extract_treatment_type(text):

    text = text.lower()

    for treatment in TREATMENT_TYPES:

        if treatment in text:

            return treatment

    return None
# ==========================================
# STRUCTURAL SIGNALS
# ==========================================

def detect_structural_signals(text):

    # ==========================================
    # QUANTITY DETECTION
    # ==========================================

    quantity_match = re.search(

        r"\b\d+(?:\.\d+)?\b",

        text

    )

    # ==========================================
    # IGNORE FERTILIZER GRADES
    # ==========================================

    fertilizer_pattern = (

        r"\d{1,2}[.:]\d{1,2}[.:]\d{1,2}"

    )

    if re.search(

        fertilizer_pattern,

        text

    ):

        quantity_match = None

    has_quantity = (

        quantity_match is not None

    )

    # ==========================================
    # QUERY WORDS
    # ==========================================

    has_query_words = any(

        word in text

        for word in QUERY_WORDS

    )

    # ==========================================
    # SEMANTIC QUERY PATTERNS
    # ==========================================

    query_patterns = [

        r"\bkaunsa\b",
        r"\bkonsa\b",
        r"\bkitna\b",
        r"\bkitne\b",
        r"\bkitni\b",
        r"\bkitana\b",
        r"\bkab\b"

    ]

    semantic_query = any(

        re.search(pattern, text)

        for pattern in query_patterns

    )

    # ==========================================
    # FINAL QUERY SIGNAL
    # ==========================================

    has_query_words = (

        has_query_words

        or

        semantic_query

    )

    return {

        "has_quantity": has_quantity,

        "has_query_words": has_query_words

    }


# ==========================================
# ENTITY SANITIZER
# ==========================================


def clean_entity(entity):

    if not entity:

        return None

    entity = entity.strip().lower()

    if len(entity) <= 1:

        return None

    if entity in [

        "(",
        ")",
        ",",
        ".",
        "-"

    ]:

        return None

    return entity


# ==========================================
# FUZZY MATCH
# ==========================================


def fuzzy_match(text, candidate):

    if candidate in text:

        return 1.0

    return SequenceMatcher(
        None,
        text,
        candidate
    ).ratio()


# ==========================================
# ENTITY EXTRACTION
# ==========================================


def extract_entities(text):

    entities = {}

    for entity_type in ENTITY_TYPES:

        entities[entity_type] = None

        all_entities = load_entities(
            entity_type
        )

        best_score = 0.0
        best_entity = None

        for entity in all_entities:

            entity = clean_entity(entity)

            if not entity:

                continue

            score = fuzzy_match(
                text,
                entity
            )

            if score > best_score:

                best_score = score
                best_entity = entity

        if best_score >= 0.85:

            entities[entity_type] = best_entity

    return entities


def extract_person_before_ko(text):

    blocked_words = [

        "aaj",
        "kal",
        "parso",
        "farm",
        "payment",
        "rupye",
        "rupaye",
        "rs"

    ]

    match = re.search(

        r"(?:^|\b)(?:aaj\s+)?([a-z][a-z0-9_ ]{1,40}?)\s+ko\b",

        text

    )

    if not match:

        return None

    candidate = match.group(1).strip()

    tokens = [

        token

        for token in candidate.split()

        if token not in blocked_words

    ]

    if not tokens:

        return None

    return clean_entity(
        tokens[-1]
    )


# ==========================================
# OPERATION DETECTION
# ==========================================
def detect_operation(text, tokens):

    best_operation = None

    best_score = 0

    # ==========================================
    # LOAD DYNAMIC KEYWORDS
    # ==========================================

    dynamic_keys = (
        load_dynamic_keywords()
    )

    # ==========================================
    # MERGE STATIC + DYNAMIC
    # ==========================================

    combined_keywords = dict(
        STATIC_OPERATION_KEYWORDS
    )

    for op, keys in dynamic_keys.items():

        if op in combined_keywords:

            combined_keywords[op] = list(

                set(

                    combined_keywords[op]
                    + keys

                )

            )

        else:

            combined_keywords[op] = keys

    # ==========================================
    # SCORE OPERATIONS
    # ==========================================

    operation_scores = {}

    for operation, keywords in combined_keywords.items():

        score = 0

        for keyword in keywords:

            if keyword in text:

                score += 1

        operation_scores[
            operation
        ] = score

    # ==========================================
    # BEST MATCH
    # ==========================================

    best_operation = max(

        operation_scores,

        key=operation_scores.get

    )

    best_score = operation_scores[
        best_operation
    ]

    # ==========================================
    # NO MATCH
    # ==========================================

    if best_score == 0:

        return None

    return best_operation
# ==========================================
# INTENT DETECTION
# ==========================================

def detect_intent(text, signals):

    # ==========================================
    # QUERY PRIORITY
    # ==========================================

    if signals["has_query_words"]:

        return "query"

    # ==========================================
    # ENTRY / FACT
    # ==========================================

    if signals["has_quantity"]:

        return "entry"

    # ==========================================
    # ACTION
    # ==========================================

    return "action"

# ==========================================
# ADD MISSING FIELD
# ==========================================


def add_missing(data, field):

    if field not in data["missing_fields"]:

        data["missing_fields"].append(
            field
        )


# ==========================================
# FINALIZE RECORD
# ==========================================


def finalize_record(data):

    if (
        data.get("intent") == "entry"
        and data.get("quantity") is not None
    ):

        data["mode"] = "entry"
        data["is_entry"] = True

    if data["missing_fields"]:

        data["needs_clarification"] = True

        data["clarification_type"] = "missing_field"

        data["context_status"] = "pending_info"

    else:

        data["needs_clarification"] = False

        data["clarification_type"] = None

        data["context_status"] = "completed"

    return data


# ==========================================
# RULE METADATA
# ==========================================


def add_rule_metadata(data, rule_id, reason):

    data["reasoning_trace"] = [

        reason,

        "Operational cognitive extraction"

    ]

    data["rule_trace"] = [

        rule_id

    ]

    data["rule_result"] = [

        {

            "rule": rule_id,

            "result": "matched",

            "score_change": "+1.0"

        }

    ]

    data["decision_engine"] = "operational_rule_engine"

    data["context_source"] = "rule_engine"

    return data


# ==========================================
# MAIN EXTRACTION
# ==========================================


def extract_by_rules(user_input):

    text = normalize_text(
        user_input
    )

    tokens = get_tokens(
        text
    )

    signals = detect_structural_signals(
        text
    )

    operation = detect_operation(
        text,
        tokens
    )

    if not operation:

        return None

    intent = detect_intent(
        text,
        signals
    )

    data = blank_record()

    # ==========================================
    # CORE COGNITION
    # ==========================================

    data["intent"] = intent

    data["operation"] = operation

    # ==========================================
    # ENTITIES
    # ==========================================

    entities = extract_entities(
        text
    )

    data["farm"] = entities.get(
        "farm"
    )

    data["crop"] = entities.get(
        "crop"
    )

    data["worker"] = entities.get(
        "worker"
    )

    data["product"] = entities.get(
        "product"
    )

    data["vendor"] = entities.get(
        "vendor"
    )

    data["buyer"] = entities.get(
        "buyer"
    )

    # ==========================================
    # METRICS
    # ==========================================

    fertilizer_grade = extract_fertilizer_grade(
        text
    )

    # ==========================================
    # PAYMENT
    # ==========================================

    if operation == "payment":

        number = get_first_number(text)

        data["amount"] = number

        if not data["worker"]:

            data["worker"] = extract_person_before_ko(
                text
            )

            if data["worker"]:

                data[
                    "entities"
                ] = {

                    **data.get(
                        "entities",
                        {}
                    ),

                    "worker":
                    data["worker"]

                }

    # ==========================================
    # EXPENSE
    # ==========================================

    elif operation == "expense":

        number = get_first_number(text)

        data["amount"] = number

        if not data["product"]:

           for expense_term in [

                "diesel",
                "fuel",
                "petrol",

                "repair",
                "service"

            ]:

                if expense_term in text:

                    data["product"] = expense_term
                    break

    # ==========================================
    # TREATMENT OPERATIONS
    # ==========================================

    elif operation == "treatment":

        data["treatment_type"] = (
            extract_treatment_type(text)
        )

        data["application_method"] = (
            extract_application_method(text)
        )

        # ==========================================
        # FERTILIZER GRADE AS PRODUCT
        # ==========================================

        if fertilizer_grade:

            data["product"] = fertilizer_grade

            data["quantity"] = None

            data["unit"] = None

        else:

            number = get_quantity_before_unit(text)

            data["quantity"] = number

            data["unit"] = detect_unit(text)
    # ==========================================
    # NORMAL OPERATIONS
    # ==========================================

    else:

        number = get_quantity_before_unit(text)

        data["quantity"] = number

        data["unit"] = detect_unit(
            text
        )
    # ==========================================
    # PEST EXTRACTION
    # ==========================================

    if operation == "pest_attack":

        for pest in  STATIC_OPERATION_KEYWORDS[
            "pest_attack"
        ]:

            if pest in text:

                data["pest"] = pest
                break

    # ==========================================
    # VALIDATION
    # ==========================================

    if operation == "payment":

        if not data["worker"]:

            add_missing(
                data,
                "worker"
            )

        if not data["amount"]:

            add_missing(
                data,
                "amount"
            )

    elif operation == "expense":

        if not data["amount"]:

            add_missing(
                data,
                "amount"
            )

    elif operation == "harvest":

        if not data["farm"]:

            add_missing(
                data,
                "farm"
            )

        if not data["crop"]:

            add_missing(
                data,
                "crop"
            )

        # ==========================================
        # QUANTITY REQUIRED ONLY FOR ENTRY
        # ==========================================

        if (

            intent == "entry"

            and

            not data["quantity"]

        ):

            add_missing(
                data,
                "quantity"
            )
    elif operation == "treatment":

        if not data["farm"]:

            add_missing(
                data,
                "farm"
            )

        if not data["crop"]:

            add_missing(
                data,
                "crop"
            )

        if(    
           
           intent == "entry"

           and

           not data["product"]

           ):

            add_missing(
                data,
                "product"
            )

    elif operation == "pest_attack":

        if not data["crop"]:

            add_missing(
                data,
                "crop"
            )

    # ==========================================
    # FINALIZE
    # ==========================================

    finalize_record(
        data
    )

    # ==========================================
    # RULE IDS
    # ==========================================

    rule_id = f"RULE_{operation.upper()}_001"

    add_rule_metadata(
        data,
        rule_id,
        f"{operation} operation detected"
    )

    return data
