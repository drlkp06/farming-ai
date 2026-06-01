# ========================================
# IMPORTS
# ========================================

import json
import os
import pickle
import re

from datetime import datetime
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from memory_system.entity_memory import (
    load_entities
)

from knowledge_learning.semantic_learning import (
    load_dynamic_semantic_groups,
    detect_candidate_rule,
    store_candidate_learning
)

from knowledge_learning.semantic_knowledge import (

    SEMANTIC_GROUPS,
    SEMANTIC_EQUIVALENTS,

    load_phrase_aliases

)

from knowledge_learning.learning import (

    FUNCTIONAL_LANGUAGE_WORDS,
    load_operation_keywords

)

from config import (

    INTENTS_FILE,
    VECTOR_DB_FILE,

    SEMANTIC_MEMORY_FILE,
    INTENT_MEMORY_FILE

)

# ========================================
# DEFAULT SEMANTIC MEMORY
# ========================================

DEFAULT_SEMANTIC_MEMORY = {

    "intents": {},
    "queries": {},

    "language_rules": {},

    "operation_aliases": {},

    "intent_patterns": {}

}

# ========================================
# LOAD JSON
# ========================================

def load_json(path, default=None):

    if default is None:

        default = {}

    if not os.path.exists(path):

        return default

    try:

        with open(

            path,
            "r",
            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return default

# ========================================
# SAVE JSON
# ========================================

def save_json(path, data):

    os.makedirs(

        os.path.dirname(path),
        exist_ok=True

    )

    with open(

        path,
        "w",
        encoding="utf-8"

    ) as f:

        json.dump(

            data,
            f,
            indent=2,
            ensure_ascii=False

        )

# ========================================
# LOAD SEMANTIC MEMORY
# ========================================

def load_semantic_memory():

    memory = load_json(

        SEMANTIC_MEMORY_FILE,
        DEFAULT_SEMANTIC_MEMORY.copy()

    )

    for key, value in DEFAULT_SEMANTIC_MEMORY.items():

        memory.setdefault(
            key,
            value
        )

    return memory

SEMANTIC_MEMORY = (
    load_semantic_memory()
)

# ========================================
# RELOAD SEMANTIC MEMORY
# ========================================

def reload_semantic_memory():

    global SEMANTIC_MEMORY

    SEMANTIC_MEMORY = (
        load_semantic_memory()
    )

# ========================================
# SEMANTIC GROUPS
# ========================================

DYNAMIC_ALL_SEMANTIC_GROUPS = {

    intent: data.get(
        "keywords",
        []
    )

    for intent, data in
    SEMANTIC_MEMORY.get(
        "intents",
        {}
    ).items()

}

ALL_SEMANTIC_GROUPS = {

    **SEMANTIC_GROUPS,
    **DYNAMIC_ALL_SEMANTIC_GROUPS

}

# ========================================
# QUERY WORDS
# ========================================

QUERY_WORDS = {

    "kitna",
    "kitni",
    "kitne",

    "kab",

    "history",
    "summary",
    "report",

    "batao",
    "dikhao",

    "details",
    "record",

    "last",
    "latest",
    "recent",

    "total"

}

# ========================================
# HELPER VERBS
# ========================================

HELPER_VERBS = {

    "hai",
    "hain",

    "hua",
    "hui",
    "hue",

    "tha",
    "thi",
    "the",

    "hoga",
    "hogi"

}

# ========================================
# FILLER WORDS
# ========================================

FILLER_WORDS = {

    "ko",
    "ka",
    "ke",
    "ki",

    "me",
    "mai",
    "mein",

    "se",
    "par",

    "aur",
    "or",
    "and"

}

# ========================================
# BLOCKED WORDS
# ========================================

BLOCKED_WORDS = set(

    SEMANTIC_MEMORY.get(
        "language_rules",
        {}
    ).get(
        "blocked_worker_words",
        [

            "aaj",
            "kal",

            "kitna",
            "kitni",
            "kitne"

        ]
    )

)

# ========================================
# LOAD MODEL
# ========================================

MODEL_NAME = (
    "all-MiniLM-L6-v2"
)

model = SentenceTransformer(

    MODEL_NAME,
    local_files_only=True

)

# ========================================
# LOAD INTENTS
# ========================================

INTENTS = load_json(
    INTENTS_FILE,
    {}
)

# ========================================
# LOAD VECTOR DB
# ========================================

import os
import pickle

VECTOR_DB = []

try:

    with open(

        VECTOR_DB_FILE,
        "rb"

    ) as f:

        VECTOR_DB = pickle.load(f)

    print(

        "Vectors loaded"

    )

except FileNotFoundError:

    print(

        "Vector database not found."

    )

    print(

        "Building vectors..."
    )

    # ====================================
    # CREATE VECTOR DIRECTORY
    # ====================================

    os.makedirs(

        os.path.dirname(
            VECTOR_DB_FILE
        ),

        exist_ok=True

    )

    VECTOR_DB = []

    # ====================================
    # BUILD VECTOR DATABASE
    # ====================================

    for intent, meta in INTENTS.items():

        examples = meta.get(

            "examples",
            []

        )

        if not examples:

            continue

        try:

            embeddings = model.encode(

                examples

            )

        except Exception as e:

            print(

                f"Embedding failed for intent '{intent}': {e}"

            )

            continue

        for sentence, emb in zip(

            examples,
            embeddings

        ):

            VECTOR_DB.append({

                "intent":
                intent,

                "sentence":
                sentence,

                "embedding":
                emb

            })

    # ====================================
    # SAVE VECTOR DATABASE
    # ====================================

    with open(

        VECTOR_DB_FILE,
        "wb"

    ) as f:

        pickle.dump(

            VECTOR_DB,
            f

        )

    print(

        f"Vector database created with {len(VECTOR_DB)} vectors."

    )

except Exception as e:

    print(

        f"Vector loading failed: {e}"

    )

    VECTOR_DB = []

# ========================================
# REASONING TRACE
# ========================================

def add_reasoning_trace(

    semantic_state,
    message

):

    if not semantic_state.get(
        "reasoning_trace"
    ):

        semantic_state[
            "reasoning_trace"
        ] = []

    if message not in semantic_state[
        "reasoning_trace"
    ]:

        semantic_state[
            "reasoning_trace"
        ].append(message)

# ========================================
# NORMALIZE TEXT
# ========================================

def normalize_text(text):

    normalized = (

        text
        .lower()
        .strip()

    )

    normalized = re.sub(

        r"[^a-z0-9_\s.]",

        " ",

        normalized

    )

    normalized = re.sub(

        r"\s+",

        " ",

        normalized

    )

    aliases = load_phrase_aliases()

    for source, target in sorted(

        aliases.items(),

        key=lambda x: len(x[0]),
        reverse=True

    ):

        normalized = re.sub(

            rf"\b{re.escape(source)}\b",

            target,

            normalized

        )

    return re.sub(

        r"\s+",

        " ",

        normalized

    ).strip()

# ========================================
# TOKENS
# ========================================

def get_tokens(text):

    return re.findall(

        r"[a-z0-9_]+",

        text.lower()

    )

# ========================================
# FIND ENTITIES
# ========================================

def find_known_entities(text):

    found = {}

    for entity_type in [

        "farm",
        "crop",

        "worker",

        "product",
        "vendor",
        "buyer"

    ]:

        for entity in load_entities(
            entity_type
        ):

            entity_normalized = (
                normalize_text(entity)
            )

            if re.search(

                rf"\b{re.escape(entity_normalized)}\b",

                text

            ):

                found[
                    entity_type
                ] = entity

                break

    return found

# ========================================
# ABSTRACT PATTERN
# ========================================

def abstract_pattern(

    text,
    entities

):

    pattern = re.sub(

        r"\b\d+(?:\.\d+)?\b",

        "<number>",

        text

    )

    for entity_type, value in entities.items():

        pattern = re.sub(

            rf"\b{re.escape(value)}\b",

            f"<{entity_type}>",

            pattern,

            flags=re.IGNORECASE

        )

    return re.sub(

        r"\s+",

        " ",

        pattern

    ).strip()

# ========================================
# REUSABLE PHRASE
# ========================================

def reusable_phrase(

    text,
    entities

):

    phrase = normalize_text(text)

    for value in entities.values():

        phrase = re.sub(

            rf"\b{re.escape(value)}\b",

            " ",

            phrase,

            flags=re.IGNORECASE

        )

    tokens = [

        token

        for token in get_tokens(phrase)

        if token not in FILLER_WORDS

    ]

    return " ".join(tokens)

# ========================================
# DETECT QUERY
# ========================================

def detect_query_type(

    normalized

):

    def contains_any(markers):

        return any(

            marker in normalized

            for marker in markers

        )

    has_query_words = any(

        word in normalized

        for word in QUERY_WORDS

    )

    # ========================================
    # HISTORY AND DETAIL QUERIES
    # ========================================

    if contains_any([

        "payment history",
        "salary history",
        "mazdoori history"

    ]):

        return {

            "query_type":
            "payment_history",

            "confidence":
            0.94

        }

    if contains_any([

        "product history",
        "medicine history",
        "spray history"

    ]):

        return {

            "query_type":
            "product_history",

            "confidence":
            0.93

        }

    if contains_any([

        "last treatment",
        "latest treatment",
        "recent treatment",
        "aakhri treatment",
        "last spray",
        "latest spray",
        "recent spray",
        "aakhri spray"

    ]):

        return {

            "query_type":
            "last_treatment",

            "confidence":
            0.93

        }

    # ========================================
    # HARVEST QUERY
    # ========================================

    harvest_query = (

        any(

            marker in normalized

            for marker in [

                "harvest",
                "nikla",
                "nikli",
                "nikle",

                "todai",
                "tudai"

            ]

        )

        and

        any(

            marker in normalized

            for marker in [

                "kitna",
                "kitni",
                "kitne",
                "total"

            ]

        )

    )

    if harvest_query:

        return {

            "query_type":
            "harvest_quantity",

            "confidence":
            0.92

        }

    # ========================================
    # PAYMENT QUERY
    # ========================================

    payment_query = (

        any(

            marker in normalized

            for marker in [

                "payment",
                "rupye",

                "diya",
                "diye"

            ]

        )

        and

        any(

            marker in normalized

            for marker in [

                "kitna",
                "kitni",
                "kitne",

                "hisab",
                "total"

            ]

        )

    )

    if payment_query:

        return {

            "query_type":
            "total_payment",

            "confidence":
            0.93

        }

    # ========================================
    # EXPENSE QUERY
    # ========================================

    expense_query = (

        any(

            marker in normalized

            for marker in [

                "expense",
                "kharcha",

                "diesel",
                "fuel",
                "repair"

            ]

        )

        and

        any(

            marker in normalized

            for marker in [

                "kitna",
                "kitni",
                "kitne",

                "hisab",
                "total"

            ]

        )

    )

    if expense_query:

        return {

            "query_type":
            "total_expense",

            "confidence":
            0.91

        }

    if has_query_words:

        return {

            "query_type":
            "general_query",

            "confidence":
            0.60

        }

    return None

# ========================================
# DETECT OPERATION
# ========================================

def detect_operation_type(normalized):

    tokens = get_tokens(normalized)

    harvest_words = {

        "harvest",
        "nikla",
        "nikli",
        "nikle",
        "tudai",
        "todai",
        "utrega",
        "utregi"

    }

    payment_words = {

        "payment",
        "diya",
        "diye",
        "rupye"

    }

    expense_words = {

        "expense",
        "diesel",
        "fuel",
        "repair",
        "kharcha"

    }

    for token in tokens:

        if token in harvest_words:
            return "harvest"

        if token in payment_words:
            return "payment"

        if token in expense_words:
            return "expense"

    return "unknown"

# ========================================
# STRUCTURAL SIGNALS
# ========================================

def detect_structural_signals(

    normalized

):

    has_quantity = bool(

        re.search(

            r"\b\d+(?:\.\d+)?\b",

            normalized

        )

    )

    has_query_words = any(

        word in normalized

        for word in QUERY_WORDS

    )

    return {

        "has_quantity":
        has_quantity,

        "has_query_words":
        has_query_words

    }

# ========================================
# BLANK RECORD
# ========================================

def blank_record():

    return {

        "intent": None,

        "operation": None,

        "query_type": None,

        "mode": "action",

        "entities": {},

        "confidence": 0.0,

        "reasoning_trace": [],

        "semantic_focus": {},

        "is_query": False,

        "is_entry": False,

        "save_status": None,

        "response": None,

        # ====================================
        # REQUIRED STABILITY FIELDS
        # ====================================

        "missing_fields": [],

        "needs_clarification": False,

        "clarification_type": None,

        "context_status": "initialized",

        "context_confidence": None,

        "context_source": "semantic_engine",

        "decision_reason": [],

        "rule_trace": [],

        "rule_result": [],

        "memory_updates": [],

        "inference": [],

        "reasoning_chain": [],

        "merge_source_fields": [],

        "related_operations": [],

        "operation_history": [],

        "learned_attributes": []

    }

# ========================================
# ABSTRACT USER INTENT
# ========================================

def abstract_user_intent(user_input):

    normalized = normalize_text(
        user_input
    )

    tokens = get_tokens(
        normalized
    )

    entities = find_known_entities(
        normalized
    )

    pattern = abstract_pattern(

        normalized,
        entities

    )

    phrase = reusable_phrase(

        normalized,
        entities

    )

    operation = detect_operation_type(
        normalized
    )

    query_result = detect_query_type(
        normalized
    )

    signals = detect_structural_signals(
        normalized
    )

    mode = "action"

    query_type = None

    confidence = 0.0

    # ========================================
    # QUERY MODE
    # ========================================

    if query_result:

        mode = "query"

        query_type = query_result[
            "query_type"
        ]

        confidence = query_result[
            "confidence"
        ]

    # ========================================
    # ENTRY MODE
    # ========================================

    elif (

        signals["has_quantity"]

        and

        operation != "unknown"

    ):

        mode = "entry"

        confidence = 0.82

    # ========================================
    # SEMANTIC LEARNING
    # ========================================

    candidate = detect_candidate_rule(

        normalized,
        intent_abstraction=None

    )

    if candidate:

        confidence = max(

            confidence,

            candidate.get(
                "confidence",
                0.55
            )

        )

    reasoning_trace = [

        f"normalized='{normalized}'",

        f"abstract_pattern='{pattern}'"

    ]

    semantic_trace_state = {

        "reasoning_trace":
        reasoning_trace

    }

    if operation != "unknown":

        add_reasoning_trace(

            semantic_trace_state,

            f"operation='{operation}'"

        )

    if query_type:

        add_reasoning_trace(

            semantic_trace_state,

            f"query='{query_type}'"

        )

    reasoning_trace = semantic_trace_state[
        "reasoning_trace"
    ]

    return {

        "raw_text":
        user_input,

        "normalized_text":
        normalized,

        "tokens":
        tokens,

        "entities":
        entities,

        "abstract_pattern":
        pattern,

        "reusable_phrase":
        phrase,

        "operation":
        operation,

        "mode":
        mode,

        "query_type":
        query_type,

        "confidence":
        round(confidence, 2),

        "is_query":
        mode == "query",

        "semantic_focus": {

            "user_meaning":
            query_type or operation,

            "query_classification":
            query_type,

            "conversational_understanding":
            mode

        },

        "reasoning_trace":
        reasoning_trace

    }

# ========================================
# BUILD SEMANTIC STATE
# ========================================

def build_semantic_state(user_input):

    abstraction = abstract_user_intent(
        user_input
    )

    semantic_state = blank_record()

    semantic_state.update({

        "raw_input":
        user_input,

        "normalized_text":
        abstraction.get(
            "normalized_text"
        ),

        "intent":

        (
            "query"

            if abstraction.get(
                "is_query"
            )

            else

            abstraction.get(
                "operation"
            )

        ),

        "operation":
        abstraction.get(
            "operation"
        ),

        "query_type":
        abstraction.get(
            "query_type"
        ),

        "mode":
        abstraction.get(
            "mode"
        ),

        "entities":
        abstraction.get(
            "entities",
            {}
        ),

        "confidence":
        abstraction.get(
            "confidence",
            0.0
        ),

        "semantic_focus":
        abstraction.get(
            "semantic_focus",
            {}
        ),

        "reasoning_trace":
        abstraction.get(
            "reasoning_trace",
            []
        ),

        "is_query":
        abstraction.get(
            "is_query"
        ),

        "is_entry":

        abstraction.get(
            "mode"
        ) == "entry"

    })

    # ========================================
    # ENTITY SYNC
    # ========================================

    for key, value in semantic_state[
        "entities"
    ].items():

        semantic_state[key] = value

    # ========================================
    # OPERATION EXTRACTOR
    # ========================================

    operation = semantic_state.get(
        "operation"
    )

    extractor = OPERATION_EXTRACTORS.get(
        operation
    )

    if extractor:

        semantic_state = extractor(
            semantic_state
        )

    return semantic_state

# ========================================
# OPERATION EXTRACTORS
# ========================================

def extract_harvest(state):

    add_reasoning_trace(

        state,

        "harvest extractor applied"

    )

    return state

def extract_payment(state):

    add_reasoning_trace(

        state,

        "payment extractor applied"

    )

    return state

def extract_expense(state):

    add_reasoning_trace(

        state,

        "expense extractor applied"

    )

    return state

def extract_spray(state):

    add_reasoning_trace(

        state,

        "spray extractor applied"

    )

    return state

# ========================================
# EXTRACTOR REGISTRY
# ========================================

OPERATION_EXTRACTORS = {

    "harvest":
    extract_harvest,

    "payment":
    extract_payment,

    "expense":
    extract_expense,

    "spray":
    extract_spray

}

# ========================================
# SEMANTIC DETECTION
# ========================================

def detect_intent(text):

    query_embedding = model.encode(
        [text]
    )

    best_score = -1

    best_match = None

    for item in VECTOR_DB:

        score = cosine_similarity(

            query_embedding,

            [item["embedding"]]

        )[0][0]

        if score > best_score:

            best_score = score

            best_match = item

    return {

        "intent":
        best_match["intent"],

        "score":
        float(best_score)

    }

# ========================================
# LEARN SENTENCE
# ========================================

def learn(text, intent):

    emb = model.encode(
        [text]
    )[0]

    VECTOR_DB.append({

        "intent":
        intent,

        "sentence":
        text,

        "embedding":
        emb

    })

    with open(

        VECTOR_DB_FILE,
        "wb"

    ) as f:

        pickle.dump(
            VECTOR_DB,
            f
        )

    return {

        "status":
        "learned",

        "intent":
        intent

    }
# ==========================================
# STATE HELPERS
# ==========================================

def is_entry_operation(state):

    return (

        state.get("is_entry") is True

        or

        state.get("mode") == "entry"

        or

        state.get("intent") == "entry"

    )


def is_query_operation(state):

    return (

        state.get("is_query") is True

        or

        state.get("mode") == "query"

        or

        state.get("intent") == "query"

    )