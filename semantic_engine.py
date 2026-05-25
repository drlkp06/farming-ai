#========================================
# IMPORTS
#========================================

import json
import os
import pickle
import re

from datetime import datetime
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from entity_memory import load_entities

from semantic_learning import (
    load_dynamic_semantic_groups
)

from semantic_knowledge import (
    SEMANTIC_GROUPS,
    SEMANTIC_EQUIVALENTS,
    load_phrase_aliases
)

DYNAMIC_ALL_SEMANTIC_GROUPS = (
    load_dynamic_semantic_groups()
)

# ==========================================
# MERGED SEMANTIC GROUPS
# ==========================================

ALL_SEMANTIC_GROUPS = {
    **SEMANTIC_GROUPS,
    **DYNAMIC_ALL_SEMANTIC_GROUPS
}


def _clone_pattern_clusters(source_clusters):

    cloned = {}

    for name, cluster in source_clusters.items():

        cloned[name] = {
            **cluster,
            "phrases": list(cluster.get("phrases", [])),
            "examples": list(cluster.get("examples", [])),
        }

    return cloned

# ==========================================
# MEMORY FILE
# ==========================================

MEMORY_FILE = "memory/intent_patterns.json"

# ==========================================
# FARM ALIASES
# ==========================================

FARM_ALIASES = {

    "satpuda farm": "satpuda",

    "rajpura farm": "rajpura"

}

# ==========================================
# CROP ALIASES
# ==========================================

CROP_ALIASES = {

    "kheera": "cucumber",

    "keera": "cucumber",

    "khira": "cucumber"

}

# ==========================================
# INTENT PATTERN CLUSTERS
# ==========================================
DEFAULT_PATTERN_CLUSTERS = {
    "hisab": {
        "meaning": "hisab",
        "mapped_intent": "total_payment",
        "mode": "query",
        "confidence": 0.92,
        "phrases": [
            "pura lekha",
            "poora lekha",
            "cash book",
            "payment summary",
            "payment report",
            "khata",
            "hisaab",
            "lekha",
            "pura hisab",
            "poora hisab",
        ],
    },
}


INTENT_ENTITY_REQUIREMENTS = {
    "total_payment": {
        "required_any": [
            "worker",
            "person",
        ],
        "blocked_if_only": [
            "crop",
            "product",
            "vendor",
            "buyer",
        ],
    },
    "payment_history": {
        "required_any": [],
        "blocked_if_only": [
            "crop",
            "product",
        ],
    },
    "total_expense": {
        "required_any": [],
        "blocked_if_only": [],
    },
    "crop_history": {
        "required_any": [
            "crop",
        ],
        "blocked_if_only": [
            "worker",
            "product",
        ],
    },
    "last_treatment": {
        "required_any": [
            "crop",
        ],
        "blocked_if_only": [
            "worker",
            "vendor",
            "buyer",
        ],
    },
    "product_history": {
        "required_any": [
            "product",
        ],
        "blocked_if_only": [
            "worker",
            "crop",
        ],
    },
    "harvest_quantity": {
        "required_any": [
            "crop",
        ],
        "blocked_if_only": [
            "worker",
            "product",
            "vendor",
            "buyer",
        ],
    },
}


DEFAULT_PHRASE_ALIASES = {

    # ==========================================
    # PAYMENT
    # ==========================================

    "rupaye": "rupye",
    "rupyee": "rupye",
    "rupee": "rupye",
    "rypye": "rupye",
    "rupees": "rupye",

    "rs": "rupye",

    "paise": "payment",
    "paisa": "payment",
    "majdoori": "payment",

    "hisab": "total payment",
    "hisaab": "total payment",

    "khata": "total payment",

    "cash book": "total payment",

    "pura lekha": "total payment",
    "poora lekha": "total payment",

    "lekha": "total payment",
    "lekha jokha": "total payment",

    "pura hisab": "total payment",
    "poora hisab": "total payment",

    "abtak": "total payment",
    "ab tak": "total payment",

    "milaake": "total payment",
    "milake": "total payment",

    "mila kar": "total payment",
    "milakar": "total payment",

    "kitna gaya": "total payment",
    "kitna gya": "total payment",
    "kitana": "kitna",

    "kitna diya": "total payment",
    "kitne diye": "total payment",

    "payment summary": "total payment",
    "payment report": "total payment",

    "date waise": "date wise",
    "datewise": "date wise",

    # ==========================================
    # PRODUCT / TREATMENT HISTORY
    # ==========================================

    "kab dala": "product history",
    "kab dali": "product history",

    "kya dala": "treatment history",

    # ==========================================
    # LAST TREATMENT
    # ==========================================

    "last treatment kya hua": "last treatment",

    "last treatment": "last treatment",
    "latest treatment": "last treatment",
    "recent treatment": "last treatment",

    # ==========================================
    # PRODUCT
    # ==========================================

    "dawai": "product",
    "medicine": "product",

    # ==========================================
    # TREATMENT
    # ==========================================

    "chhidkaav": "treatment",
    "chhidkav": "treatment",

    "spray": "treatment",

    # ==========================================
    # HARVEST
    # ==========================================

    "todai": "harvest",
    "tudai": "harvest",

    "maal utrega": "harvest",

}


def extract_worker_before_ko(text):

    blocked_words = {
        "aaj",
        "kal",
        "parso",
        "total",
        "payment",
        "rupye",
        "rupaye",
        "rupyee",
        "diya",
        "diye",
        "kitna",
        "kitne",
    }

    match = re.search(
        r"(?:^|\b)([a-z][a-z0-9_ ]{1,40}?)\s+ko\b",
        text or "",
    )

    if not match:

        return None

    tokens = [
        token
        for token in match.group(1).strip().split()
        if token not in blocked_words
    ]

    if not tokens:

        return None

    return tokens[-1]

INTENT_KEYWORDS = {
    "payment": [
        "payment",
        "rupye",
        "diye",
        "paid",
        "total payment",
    ],
   "treatment": [

        # spray
        "spray",
        "chhidkaav",
        "chhidkav",

        # fertilizer
        "fertilizer",
        "npk",
        "urea",
        "dap",

        # treatment actions
        "dala",
        "daala",
        "kiya",
        "drip",
        "drenching",
        "dressing",
        "fertigation",
   ],
    "harvest": [
        "harvest",
        "nikla",
        "nikale",
        "utrega",
        "toda",
    ],
    "expense": [
        "diesel",
        "repair",
        "fuel",
        "bharwaya",
        "kharcha",
    ],
    "pest_attack": [
        "whitefly",
        "thrips",
        "mites",
        "aphid",
        "leaf miner",
        "pest",
        "rog",
        "bimari",
    ],
}


QUERY_KEYWORDS = {
    "harvest_quantity": [

    "kitna nikla",
    "kitne nikle",
    "kitna harvest",
    "harvest quantity",
    "tudai quantity",
    "todai quantity",

    ] + ALL_SEMANTIC_GROUPS.get(
    "harvest_query",
    []
    ),
    "last_treatment": [
        "last treatment",
        "latest treatment",
        "recent treatment",
        "last treatment kya hua",
        "treatment kya hua",
    ],
    "total_payment": [
        "total payment",
        "total payment",
        "kitna payment",
        "kitne diye",
        "kitna diya",
        "kitna gaya",
        "kitna gya",
        "payment total",
        "payment summary",
        "payment report",
        "pura lekha",
        "poora lekha",
        "lekha dikhao",
        "hisab dikhao",
    ],
    "total_expense": [
        "total expense",
        "expense summary",
        "expense report",
        "kharcha kitna",
        "diesel expense",
        "diesel kharcha",
        "fuel expense",
        "repair expense",
        "kitna kharcha",
    ],
    "payment_history": [
        "payment history",
        "payment list",
        "payment record",
        "payment kab",
        "payment details",
    ],
    "treatment_history": [
        "treatment history",
        "treatment list",
        "treatment record",
        "treatment kab",
        "treatment details",
    ],
    "product_history": [
        "product history",
        "usage history",
        "kab use hua",
        "kab dala",
        "kab dali",
    ],
}


# ==========================================
# MODEL LOAD
# ==========================================

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(
    MODEL_NAME,
    local_files_only=True
)

# ==========================================
# LOAD INTENTS
# ==========================================

with open(
    "intents.json",
    "r",
    encoding="utf-8"
) as f:

    INTENTS = json.load(f)

# ==========================================
# LOAD VECTOR DB
# ==========================================

try:

    with open(
        "vectors.pkl",
        "rb"
    ) as f:

        VECTOR_DB = pickle.load(f)

    print("Vectors loaded")

except FileNotFoundError:

    print("Building vectors...")

    VECTOR_DB = []

    for intent, meta in INTENTS.items():

        examples = meta["examples"]

        embeddings = model.encode(
            examples
        )

        for sentence, emb in zip(
            examples,
            embeddings
        ):

            VECTOR_DB.append(

                {
                    "intent": intent,
                    "sentence": sentence,
                    "embedding": emb
                }

            )

    with open(
        "vectors.pkl",
        "wb"
    ) as f:

        pickle.dump(
            VECTOR_DB,
            f
        )

    print("Vectors saved")

# ==========================================
# BLANK RECORD
# ==========================================

def blank_record():

    return {

        # ==========================================
        # USER INTENTION
        # ==========================================

        "intent": None,

        # ==========================================
        # FARM OPERATION
        # ==========================================

        "operation": None,

        # ==========================================
        # CORE ENTITIES
        # ==========================================

        "farm": None,

        "crop": None,

        "worker": None,

        "product": None,

        "vendor": None,

        "buyer": None,

        # ==========================================
        # METRICS
        # ==========================================

        "quantity": None,

        "unit": None,

        "amount": None,

        # ==========================================
        # OPERATIONAL DATA
        # ==========================================

        "pest": None,

        "status": None,

        "role": None,

        # ==========================================
        # TREATMENT INTELLIGENCE
        # ==========================================

        "treatment_type": None,

        "application_method": None,

        # ==========================================
        # CLARIFICATION SYSTEM
        # ==========================================

        "missing_fields": [],

        "needs_clarification": False,

        "clarification_type": None,

        "context_status": None,

        # ==========================================
        # AI REASONING
        # ==========================================

        "context_confidence": None,

        "context_source": None,

        "decision_engine": None,

        "decision_reason": [],

        "reasoning_trace": [],

        "rule_trace": [],

        "rule_result": [],

        # ==========================================
        # OPERATION MEMORY
        # ==========================================

        "operation_id": None,

        "candidate_operation_id": None,

        "related_operations": [],

        "operation_snapshot": None,

        "operation_history": [],

        # ==========================================
        # AI STATE
        # ==========================================

        "confirmation_required": False,

        "operation_relevance_score": None,

        "risk_level": None,

        "automation_policy": None,

        "state_transition": None,

        "merge_source_fields": [],

        "learned_attributes": [],

        # ==========================================
        # SYSTEM SOURCE
        # ==========================================

        "source": "user_defined"

    }

# ==========================================
# DETECT INTENT
# ==========================================

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

        "intent": best_match["intent"].lower(),

        "score": float(best_score),

        "matched_sentence": best_match["sentence"]

    }

# ==========================================
# LEARN NEW SENTENCE
# ==========================================

def learn(text, intent):

    emb = model.encode(
        [text]
    )[0]

    VECTOR_DB.append(

        {
            "intent": intent,
            "sentence": text,
            "embedding": emb
        }

    )

    with open(
        "vectors.pkl",
        "wb"
    ) as f:

        pickle.dump(
            VECTOR_DB,
            f
        )

    return {

        "status": "learned",

        "intent": intent,

        "sentence": text

    }

# ==========================================
# NORMALIZE INTENT
# ==========================================

def normalize_intent_name(name):

    name = name.lower().strip()

    name = name.replace(
        " ",
        "_"
    )

    return name

# ==========================================
# CREATE NEW INTENT
# ==========================================

def create_new_intent(

    intent_name,

    example_sentence

):

    global INTENTS

    global VECTOR_DB

    intent_name = normalize_intent_name(
        intent_name
    )

    # ==========================================
    # DUPLICATE CHECK
    # ==========================================

    if intent_name in INTENTS:

        return {

            "status": "exists",

            "intent": intent_name

        }

    # ==========================================
    # CREATE INTENT
    # ==========================================

    INTENTS[intent_name] = {

        "examples": [

            example_sentence

        ],

        "created_by": "user",

        "type": "dynamic"

    }

    # ==========================================
    # SAVE intents.json
    # ==========================================

    with open(

        "intents.json",

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            INTENTS,

            f,

            indent=2,

            ensure_ascii=False

        )

    # ==========================================
    # VECTOR UPDATE
    # ==========================================

    emb = model.encode(
        [example_sentence]
    )[0]

    VECTOR_DB.append(

        {
            "intent": intent_name,
            "sentence": example_sentence,
            "embedding": emb
        }

    )

    with open(
        "vectors.pkl",
        "wb"
    ) as f:

        pickle.dump(
            VECTOR_DB,
            f
        )

    return {

        "status": "created",

        "intent": intent_name

    }

# ==========================================
# SEMANTIC EXTRACTION
# ==========================================

def semantic_extract(user_input):

    abstraction = abstract_user_intent(
        user_input
    )

    # ==========================================
    # ENTRY OVERRIDE
    # ==========================================

    normalized = user_input.lower()

    has_quantity = bool(

        re.search(

            r"\b\d+(?:\.\d+)?\b",

            normalized

        )

    )

    entry_words = [

        "kg",
        "kilo",
        "harvest",
        "nikla",
        "mila",
        "diya",
        "spray",
        "fertilizer"

    ]

    has_entry_word = any(

        word in normalized

        for word in entry_words

    )

    query_words = [

        "kitna",
        "kitne",
        "kab",
        "batao",
        "dikhao",
        "kaunsa",
        "konsa"

    ]

    has_query_word = any(

        word in normalized

        for word in query_words

    )

    # ==========================================
    # FORCE ENTRY
    # ==========================================

    if (

        has_quantity

        and

        has_entry_word

        and

        not has_query_word

    ):

        abstraction["mode"] = "entry"

    # ==========================================
    # DIRECT QUERY MODE
    # ==========================================

    if abstraction.get("mode") == "query":

        return {

            "raw_text": user_input,

            "mode": "query",

            "is_query": True,

            "is_entry": False,

            "query_mode": True,

            "query_type": abstraction.get("query_type"),

            "candidate_intent": abstraction.get(
                "candidate_intent"
            ),

            "entities": abstraction.get(
                "entities",
                {}
            ),

            "confidence": abstraction.get(
                "confidence",
                0
            ),

            "intent_abstraction": abstraction

        }

    result = detect_intent(
        user_input
    )

    semantic_intent = result["intent"]

    semantic_score = result["score"]

    abstraction_used = False

    # ==========================================
    # LOW CONFIDENCE
    # ==========================================

    if semantic_score < 0.60:

        candidate_intent = abstraction.get(
            "candidate_intent"
        )

        candidate_score = abstraction.get(
            "confidence",
            0
        )

        if (

            not candidate_intent

            or

            candidate_score < 0.65

            or

            abstraction.get("mode") != "action"

        ):

            return None

        semantic_intent = candidate_intent

        semantic_score = candidate_score

        abstraction_used = True

    # ==========================================
    # CREATE RECORD
    # ==========================================

    data = blank_record()

    data["intent"] = semantic_intent

    # ==========================================
    # OPERATION MAPPING
    # ==========================================

    if semantic_intent == "harvest_quantity":

        data["operation"] = "harvest"

    else:

        data["operation"] = semantic_intent

    data["context_confidence"] = round(

        semantic_score,

        2

    )

    data["context_source"] = "semantic_ai"

    data["decision_engine"] = (

        "intent_abstraction_layer"

        if abstraction_used

        else

        "sentence_transformer"

    )

    data["decision_reason"] = [

        (

            "Intent abstraction fallback matched"

            if abstraction_used

            else

            "Semantic similarity matched"

        ),

        "Intent predicted by AI"

    ]

    data["reasoning_trace"] = [

        f"Semantic match found for '{semantic_intent}'",

        f"Confidence = {semantic_score:.2f}"

    ]

    data["intent_abstraction"] = {

        "normalized_text": abstraction.get(
            "normalized_text"
        ),

        "abstract_pattern": abstraction.get(
            "abstract_pattern"
        ),

        "mode": abstraction.get(
            "mode"
        ),

        "candidate_intent": abstraction.get(
            "candidate_intent"
        ),

        "confidence": abstraction.get(
            "confidence"
        ),

        "semantic_focus": abstraction.get(
            "semantic_focus"
        ),

        "query_type": abstraction.get(
            "query_type"
        ),

        "query_mode": abstraction.get(
            "query_mode"
        ),

    }

    data["rule_trace"] = [

        "SEMANTIC_RULE_001"

    ]

    data["rule_result"] = [

        {

            "rule": "SEMANTIC_RULE_001",

            "result": "matched",

            "score_change": f"+{semantic_score:.2f}"

        }

    ]

    data["automation_policy"] = (

        "semantic_auto_accept"

    )

    data["risk_level"] = "low"

    data["state_transition"] = {

        "from": "unknown",

        "to": "completed"

    }

    # ==========================================
    # SEMANTIC CLARIFICATION
    # ==========================================

    clarification = (

        check_semantic_clarification(
            data
        )

    )

    if clarification:

        return clarification

    return data

# ==========================================
# SEMANTIC CLARIFICATION
# ==========================================

def check_semantic_clarification(data):

    # ==========================================
    # SAFETY
    # ==========================================

    if not data:

        return None

    # ==========================================
    # SKIP STABLE OPERATIONS
    # ==========================================

    if data.get("operation") in [

        "payment",
        "harvest"

    ]:

        return None

    abstraction = data.get(

        "intent_abstraction",

        {}

    )

    confidence = abstraction.get(
        "confidence"
    ) or 0

    mode = abstraction.get(
        "mode"
    )

    query_type = abstraction.get(
        "query_type"
    )

    # ==========================================
    # NEEDS CLARIFICATION
    # ==========================================

    if (

        confidence < 0.65

        and

        mode != "query"

        and

        not query_type

    ):

        return {

            "needs_semantic_clarification": True,

            "message": (

                "Kya aap query pooch rahe ho "

                "ya new entry kar rahe ho?"

            ),

            "options": [

                "query",

                "entry",

                "action"

            ]

        }

    return None

def load_intent_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "phrase_aliases": {},
            "pattern_clusters": _clone_pattern_clusters(
                DEFAULT_PATTERN_CLUSTERS
            ),
            "learned_phrases": [],
            "observed_patterns": [],
            "interaction_stats": {},
        }

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)

    memory.setdefault("phrase_aliases", {})
    memory.setdefault("pattern_clusters", {})
    memory.setdefault("learned_phrases", [])
    memory.setdefault("observed_patterns", [])
    memory.setdefault("interaction_stats", {})

    for cluster_name, cluster_data in DEFAULT_PATTERN_CLUSTERS.items():
        memory["pattern_clusters"].setdefault(
            cluster_name,
            {
                **cluster_data,
                "phrases": list(cluster_data.get("phrases", [])),
                "examples": list(cluster_data.get("examples", [])),
            }
        )

    return memory


def save_intent_memory(memory):
    os.makedirs("memory", exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def normalize_text(text):
    normalized = text.lower().strip()
    normalized = re.sub(r"[^a-z0-9_\s.]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    aliases = dict(DEFAULT_PHRASE_ALIASES)
    aliases.update(load_intent_memory().get("phrase_aliases", {}))

    for source, target in sorted(
        aliases.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        normalized = re.sub(
            rf"\b{re.escape(source)}\b",
            target,
            normalized,
        )

    return re.sub(r"\s+", " ", normalized).strip()


def get_tokens(text):
    return re.findall(r"[a-z0-9_]+", text.lower())


def find_known_entities(text):

    found = {}

    # ==========================================
    # ENTITY TYPES
    # ==========================================

    for entity_type in [

        "farm",
        "crop",
        "worker",
        "product",
        "vendor",
        "buyer"

    ]:

        # ==========================================
        # LOAD ENTITIES
        # ==========================================

        for entity in load_entities(

            entity_type

        ):

            if not entity:

                continue

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


def abstract_pattern(

    text,

    entities

):

    pattern = text

    # ==========================================
    # REPLACE NUMBERS
    # ==========================================

    pattern = re.sub(

        r"\b\d+(?:\.\d+)?\b",

        "<number>",

        pattern

    )

    # ==========================================
    # ENTITY ABSTRACTION
    # ==========================================

    for entity_type, value in entities.items():

        # ==========================================
        # MULTI ENTITY SUPPORT
        # ==========================================

        if isinstance(

            value,

            list

        ):

            for item in value:

                pattern = re.sub(

                    rf"\b{re.escape(item)}\b",

                    f"<{entity_type}>",

                    pattern,

                    flags=re.IGNORECASE

                )

        # ==========================================
        # SINGLE ENTITY
        # ==========================================

        else:

            pattern = re.sub(

                rf"\b{re.escape(value)}\b",

                f"<{entity_type}>",

                pattern,

                flags=re.IGNORECASE

            )

    # ==========================================
    # CLEAN SPACES
    # ==========================================

    return re.sub(

        r"\s+",

        " ",

        pattern

    ).strip()

def reusable_phrase(

    text,

    entities

):

    phrase = text.lower().strip()

    phrase = re.sub(

        r"[^a-z0-9_\s.]",

        " ",

        phrase

    )

    # ==========================================
    # REMOVE ENTITY VALUES
    # ==========================================

    for value in entities.values():

        # ==========================================
        # MULTI ENTITY SUPPORT
        # ==========================================

        if isinstance(

            value,

            list

        ):

            for item in value:

                phrase = re.sub(

                    rf"\b{re.escape(item)}\b",

                    " ",

                    phrase,

                    flags=re.IGNORECASE

                )

        # ==========================================
        # SINGLE ENTITY
        # ==========================================

        else:

            phrase = re.sub(

                rf"\b{re.escape(value)}\b",

                " ",

                phrase,

                flags=re.IGNORECASE

            )

    # ==========================================
    # FILLER WORDS
    # ==========================================

    filler_words = [

        "ko",
        "ka",
        "ke",
        "ki",
        "me",
        "mein",
        "mai",

    ]

    # ==========================================
    # TOKEN CLEANING
    # ==========================================

    tokens = [

        token

        for token in get_tokens(

            phrase

        )

        if token not in filler_words

    ]

    return " ".join(

        tokens

    ).strip()

def score_keywords(text, keyword_map):
    best_name = None
    best_score = 0.0

    for name, keywords in keyword_map.items():
        score = 0.0

        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                score += 1.0
            else:
                score = max(
                    score,
                    SequenceMatcher(None, keyword, text).ratio() * 0.35,
                )

        score = score / max(len(keywords), 1)

        if score > best_score:
            best_name = name
            best_score = score

    return best_name, min(best_score, 1.0)


def match_learned_pattern(pattern):
    memory = load_intent_memory()
    best = None
    best_score = 0.0

    for item in memory.get("observed_patterns", []):
        learned_pattern = item.get("canonical_pattern", "")

        if not learned_pattern:
            continue

        score = SequenceMatcher(None, pattern, learned_pattern).ratio()

        if score > best_score:
            best = item
            best_score = score

    if best and best_score >= 0.74:
        return best, best_score

    return None, 0.0


def match_learned_phrase(phrase):
    memory = load_intent_memory()
    best = None
    best_score = 0.0

    for item in memory.get("learned_phrases", []):
        learned_phrase = item.get("phrase", "")

        if not learned_phrase:
            continue

        if learned_phrase in phrase:
            score = 1.0
        else:
            score = SequenceMatcher(None, phrase, learned_phrase).ratio()

        score = min(
            score,
            item.get("confidence", 0.55)
        )

        if score > best_score:
            best = item
            best_score = score

    if best and best_score >= 0.70:
        return best, best_score

    return None, 0.0


def match_pattern_cluster(text, phrase):

    memory = load_intent_memory()

    best = None

    best_score = 0.0

    for cluster_name, cluster in memory.get(

        "pattern_clusters",

        {}

    ).items():

        for cluster_phrase in cluster.get(

            "phrases",

            []

        ):

            if not cluster_phrase:

                continue

            # ==========================================
            # EXACT / DIRECT MATCH
            # ==========================================

            if (

                re.search(

                    rf"\b{re.escape(cluster_phrase)}\b",

                    text

                )

                or

                re.search(

                    rf"\b{re.escape(cluster_phrase)}\b",

                    phrase

                )

            ):

                semantic_distance = 1.0

                score = cluster.get(

                    "confidence",

                    0.75

                )

            else:

                # ==========================================
                # SEMANTIC DISTANCE
                # ==========================================

                semantic_distance = max(

                    SequenceMatcher(

                        None,

                        phrase,

                        cluster_phrase

                    ).ratio(),

                    SequenceMatcher(

                        None,

                        text,

                        cluster_phrase

                    ).ratio()

                )

                # ==========================================
                # DISTANCE PENALTY
                # ==========================================

                if semantic_distance < 0.55:

                    continue

                score = (

                    semantic_distance

                    *

                    cluster.get(

                        "confidence",

                        0.75

                    )

                )

            # ==========================================
            # BEST MATCH UPDATE
            # ==========================================

            if score > best_score:

                best = {

                    "cluster":

                    cluster_name,

                    "meaning":

                    cluster.get(

                        "meaning",

                        cluster_name

                    ),

                    "mapped_intent":

                    cluster.get(

                        "mapped_intent"

                    ),

                    "mode":

                    cluster.get(

                        "mode"

                    ),

                    "confidence":

                    min(score, 1.0),

                    "matched_phrase":

                    cluster_phrase,

                    "semantic_distance":

                    semantic_distance

                }

                best_score = score

    # ==========================================
    # FINAL CONFIDENCE CHECK
    # ==========================================

    if best and best_score >= 0.70:

        return best, min(best_score, 1.0)

    return None, 0.0


def validate_intent_entities(intent, entities):
    if not intent:
        return {
            "valid": True,
            "reason": "no_intent"
        }

    requirements = INTENT_ENTITY_REQUIREMENTS.get(
        intent
    )

    if not requirements:
        return {
            "valid": True,
            "reason": "no_entity_rule"
        }

    entity_types = set(entities.keys())
    required_any = set(
        requirements.get("required_any", [])
    )
    blocked_if_only = set(
        requirements.get("blocked_if_only", [])
    )

    if entity_types & required_any:
        return {
            "valid": True,
            "reason": "required_entity_found",
            "required_any": sorted(required_any),
            "found": sorted(entity_types)
        }

    if entity_types and entity_types <= blocked_if_only:
        return {
            "valid": False,
            "reason": "entity_intent_mismatch",
            "intent": intent,
            "required_any": sorted(required_any),
            "found": sorted(entity_types)
        }

    return {
        "valid": True,
        "reason": "entity_missing_or_unknown",
        "required_any": sorted(required_any),
        "found": sorted(entity_types)
    }


def detect_query_type(text):

    if (

        any(
            marker in text
            for marker in [
                "rupye",
                "payment",
                "diye",
                "diya",
            ]
        )

        and

        any(
            marker in text
            for marker in [
                "kitna",
                "kitne",
                "total",
                "hisab",
                "hisaab",
            ]
        )

    ):

        return "total_payment", 0.92

    if (

        any(
            marker in text
            for marker in [
                "nikla",
                "nikle",
                "harvest",
                "todai",
                "tudai"
            ]
        )

        and

        any(
            marker in text
            for marker in [
                "kitna",
                "kitne",
                "quantity"
            ]
        )

    ):

        return "harvest_quantity", 0.90

    if (
        any(
            marker in text
            for marker in [
                "expense",
                "kharcha",
                "diesel",
                "fuel",
                "repair",
            ]
        )
        and any(
            marker in text
            for marker in [
                "kitna",
                "kitne",
                "total",
                "hisab",
                "hisaab",
            ]
        )
    ):

        return "total_expense", 0.90

    query_type, score = score_keywords(text, QUERY_KEYWORDS)

    if not query_type:
        return None, 0.0

    query_markers = [

        "total payment",

        "history",

        "kab",

        "kitna",

        "kitne",

        "abtak",

        "milaake",

        "milake",

        "batao",

        "dikhao",

        "pura",

        "poora",

        "lekha",

        "record",

        "list",

        "summary",

        "report",

        "details",

        "last",

        "latest",

        "recent",

        "kya hua",

]

    has_query_marker = any(
        marker in text
        for marker in query_markers
    )

    # ==========================================
    # ENTRY SAFETY
    # ==========================================

    entry_words = [

        "kg",
        "kilo",

        "hua hai",
        "nikla hai",

        "diya",
        "diye",

        "fertilizer",

    ]

    has_entry_words = any(

        word in text

        for word in entry_words

    )

    # ==========================================
    # ENTRY SHOULD NOT BECOME QUERY
    # ==========================================

    if has_entry_words and not has_query_marker:

        return None, 0.0

    # ==========================================
    # STRICT QUERY DETECTION
    # ==========================================

    if has_query_marker:

        return query_type, max(score, 0.62)

    # ==========================================
    # HIGH CONFIDENCE SEMANTIC QUERY
    # ==========================================

    if (

        score >= 0.85

        and

        not re.search(
            r"\b\d+(?:\.\d+)?\b",
            text
        )

    ):

        return query_type, score

    return None, 0.0
# ==========================================
# DETECT OPERATION TYPE
# ==========================================
def detect_operation_type(text):

    text = normalize_text(text)

    # ==========================================
    # HARVEST
    # ==========================================

    if any(

        word in text

        for word in [

            "nikla",
            "nikla",
            "harvest",
            "todai",
            "output"

        ]

    ):

        return "harvest"

    # ==========================================
    # SPRAY
    # ==========================================

    if any(

        word in text

        for word in [

            "spray",
            "chidkav",
            "sprayed"

        ]

    ):

        return "spray"

    # ==========================================
    # EXPENSE
    # ==========================================

    if any(

        word in text

        for word in [

            "expense",
            "diesel",
            "payment",
            "kharcha",
            "rupye"

        ]

    ):

        return "expense"

    # ==========================================
    # FERTILIZER
    # ==========================================

    if any(

        word in text

        for word in [

            "fertilizer",
            "khad",
            "urea"

        ]

    ):

        return "fertilizer"

    return "unknown"
#===========================================

def abstract_user_intent(user_input):

    # ==========================================
    # NORMALIZATION
    # ==========================================

    normalized = normalize_text(
        user_input
    )

    # ==========================================
    # APPLY CROP ALIASES
    # ==========================================

    for alias, real_crop in CROP_ALIASES.items():

        if alias in normalized:

            normalized = normalized.replace(

                alias,

                real_crop

            )
    # ==========================================
    # APPLY FARM ALIASES
    # ==========================================

    for alias, real_farm in FARM_ALIASES.items():

        if alias in normalized:

            normalized = normalized.replace(

                alias,

                real_farm

            )
    # ==========================================
    # BASIC STRUCTURE
    # ==========================================

    tokens = get_tokens(
        normalized
    )

    entities = find_known_entities(
        normalized
    )

    if (
        "ko" in tokens
        and
        any(
            marker in normalized
            for marker in [
                "rupye",
                "payment",
                "diye",
                "diya",
            ]
        )
    ):

        worker = extract_worker_before_ko(
            normalized
        )

        if worker:

            entities[
                "worker"
            ] = worker
    # ==========================================
    # ABSTRACT PATTERN  + REUSABLE PHRASE
    # ==========================================

    pattern = abstract_pattern(

        normalized,

        entities

    )

    phrase = reusable_phrase(

        user_input,

        entities

    )

    # ==========================================
    # LEARNED MEMORY
    # ==========================================

    learned_pattern, learned_score = (

        match_learned_pattern(
            pattern
        )

    )

    learned_phrase, learned_phrase_score = (

        match_learned_phrase(
            phrase
        )

    )

    matched_cluster, cluster_score = (

        match_pattern_cluster(

            normalized,

            phrase

        )

    )

    # ==========================================
    # QUERY + INTENT
    # ==========================================

    query_type, query_score = (

        detect_query_type(
            normalized
        )

    )

    intent, intent_score = (

        score_keywords(

            normalized,

            INTENT_KEYWORDS

        )

    )

    # ==========================================
    # CLUSTER OVERRIDE
    # ==========================================

    if matched_cluster:

        intent = (

            matched_cluster.get(
                "mapped_intent"
            )

            or

            intent

        )

        intent_score = max(

            intent_score,

            cluster_score

        )

        if matched_cluster.get(
            "mode"
        ) == "query":

            query_type = matched_cluster.get(
                "mapped_intent"
            )

            query_score = max(

                query_score,

                cluster_score

            )

    # ==========================================
    # LEARNED PHRASE OVERRIDE
    # ==========================================

    if learned_phrase:

        intent = (

            learned_phrase.get(
                "mapped_intent"
            )

            or

            intent

        )

        intent_score = max(

            intent_score,

            learned_phrase_score

        )

        if learned_phrase.get(
            "mode"
        ) == "query":

            query_type = learned_phrase.get(
                "mapped_intent"
            )

            query_score = max(

                query_score,

                learned_phrase_score

            )

    # ==========================================
    # LEARNED PATTERN OVERRIDE
    # ==========================================

    if learned_pattern:

        intent = (

            learned_pattern.get(
                "intent"
            )

            or

            intent

        )

        intent_score = max(

            intent_score,

            learned_score

        )

    # ==========================================
    # ENTITY-AWARE QUERY CORRECTION
    # ==========================================

    if (

        entities.get(
            "crop"
        )

        and

        any(
            marker in normalized
            for marker in [
                "nikla",
                "nikle",
                "harvest",
                "todai",
                "tudai"
            ]
        )

        and

        any(
            marker in normalized
            for marker in [
                "kitna",
                "kitne",
                "quantity"
            ]
        )

    ):

        intent = "harvest_quantity"

        query_type = "harvest_quantity"

        query_score = max(

            query_score,

            0.90

        )

    if (

        entities.get(
            "worker"
        )

        and

        any(
            marker in normalized
            for marker in [
                "rupye",
                "payment",
                "diye",
                "diya"
            ]
        )

        and

        any(
            marker in normalized
            for marker in [
                "kitna",
                "kitne",
                "total"
            ]
        )

    ):

        intent = "total_payment"

        query_type = "total_payment"

        query_score = max(

            query_score,

            0.92

        )

    # ==========================================
    # STRUCTURAL SIGNALS
    # ==========================================

    signals = detect_structural_signals(
        normalized
    )

    # ==========================================
    # DEFAULT MODE
    # ==========================================

    mode = "action"

    # ==========================================
    # ENTRY PRIORITY
    # ==========================================

    if (

        signals["has_quantity"]

        and

        intent in [

            "harvest",
            "payment",
            "treatment",
            "expense"

        ]

    ):

        mode = "entry"

    # ==========================================
    # QUERY PRIORITY
    # ==========================================

    elif (

        query_type

        or

        signals["has_query_words"]

    ):

        mode = "query"

    # ==========================================
    # QUESTION MODE
    # ==========================================

    elif "kaise" in normalized:

        mode = "question"
    # ==========================================
    # ENTRY SHOULD NOT HAVE QUERY TYPE
    # ==========================================

    if mode == "entry":

        query_type = None

    # ==========================================
    # CONFIDENCE
    # ==========================================

    confidence = max(

        intent_score,

        query_score,

        learned_score,

        learned_phrase_score,

        cluster_score

    )

    # ==========================================
    # ENTITY VALIDATION
    # ==========================================

    entity_validation = (

        validate_intent_entities(

            query_type or intent,

            entities

        )

    )

    # ==========================================
    # REASONING TRACE
    # ==========================================

    reasoning_trace = [

        f"normalized='{normalized}'",

        f"abstract_pattern='{pattern}'",

    ]

    if learned_pattern:

        reasoning_trace.append(

            f"learned_pattern='{learned_pattern.get('canonical_pattern')}'"

        )

    if learned_phrase:

        reasoning_trace.append(

            f"learned_phrase='{learned_phrase.get('phrase')}'"

        )

    if matched_cluster:

        reasoning_trace.append(

            f"pattern_cluster='{matched_cluster.get('cluster')}'"

        )

    # ==========================================
    # FINAL RESULT
    # ==========================================

    return {

        "raw_text":
        user_input,

        "domain_intent":
        intent,

        "interaction_mode":
        mode,

        "normalized_text":
        normalized,

        "tokens":
        tokens,

        "entities":
        entities,

        "reusable_phrase":
        phrase,

        "abstract_pattern":
        pattern,

        "mode":
        mode,

        "is_query":
        mode == "query",

        "query_type":
        query_type,

        "candidate_intent":
        intent,

        "confidence":
        round(confidence, 2),

        "matched_learned_pattern":
        learned_pattern,

        "matched_learned_phrase":
        learned_phrase,

        "matched_pattern_cluster":
        matched_cluster,

        "entity_validation":
        entity_validation,

        "semantic_focus": {

            "user_meaning":
            query_type or intent,

            "flexible_language":
            normalized != user_input.lower().strip(),

            "query_classification":
            query_type,

            "conversational_understanding":
            mode,

            "entity_validation":
            entity_validation,

        },

        "reasoning_trace":
        reasoning_trace,

    }


def learn_conversation_pattern(

    user_input,

    resolved_data,

    auto_commit=True

):

    if not resolved_data:

        return None

    if resolved_data.get(

        "needs_clarification"

    ):

        return None

    # ==========================================
    # STRICT LEARNING INTENT
    # ==========================================

    if resolved_data.get(
        "intent"
    ) == "entry":

        intent = resolved_data.get(
            "operation"
        )

    else:

        intent = (

            resolved_data.get(
                "query_type"
            )

            or

            resolved_data.get(
                "intent"
            )

        )

    if not intent:

        return None

    abstraction = abstract_user_intent(
        user_input
    )

    normalized = abstraction.get(
        "normalized_text"
    ) or user_input.lower().strip()

    memory = load_intent_memory()

    pattern = abstraction[
        "abstract_pattern"
    ]

    phrase = reusable_phrase(

        user_input,

        abstraction.get(
            "entities",
            {}
        )

    )

    now = datetime.utcnow().isoformat(
        timespec="seconds"
    )

    learned_pattern, learned_score = match_learned_pattern(
        pattern
    )

    learned_phrase, learned_phrase_score = match_learned_phrase(
        phrase
    )

    matched_cluster, cluster_score = match_pattern_cluster(
        normalized,
        phrase
    )

    # ==========================================
    # STAGED LEARNING
    # ==========================================

    if not auto_commit:

        if (

            learned_pattern

            or

            learned_phrase

            or

            matched_cluster

        ):

            return {

                "status":
                "already_known",

                "intent":
                intent,

                "pattern":
                pattern,

                "phrase":
                phrase

            }

        pending_learning = {

            "kind":
            "semantic_pattern",

            "raw_input":
            user_input,

            "semantic_state":
            {
                **resolved_data,
            },

            "intent":
            intent,

            "pattern":
            pattern,

            "phrase":
            phrase,

            "mode":
            abstraction["mode"],

            "confidence":
            round(
                max(
                    abstraction.get(
                        "confidence",
                        0.55
                    ),
                    0.55
                ),
                2
            ),

            "created_at":
            now,

        }

        from semantic_learning import (
            store_candidate_learning
        )

        store_candidate_learning(
            {
                "candidate_phrase":
                pattern,

                "possible_group":
                intent,

                "matched_signal":
                "semantic_pattern",

                "confidence":
                max(
                    abstraction.get(
                        "confidence",
                        0.55
                    ),
                    0.55
                ),

                "example_text":
                user_input,

                "times_observed":
                1,

                "created_at":
                now,
            }
        )

        from context_engine import (
            set_pending_learning
        )

        set_pending_learning(
            pending_learning
        )

        return {

            "status":
            "needs_confirmation",

            "message":
            (
                "Naya semantic pattern mila hai. "
                "Approve karne ke liye yes bolo, "
                "reject karne ke liye no."
            ),

            "suggestion":
            pending_learning

        }

    # ==========================================
    # OBSERVED PATTERNS
    # ==========================================

    for item in memory.get(

        "observed_patterns",

        []

    ):

        if item.get(

            "canonical_pattern"

        ) != pattern:

            continue

        item["count"] = item.get(
            "count",
            0
        ) + 1

        item["intent"] = intent

        item["mode"] = abstraction[
            "mode"
        ]

        item["confidence"] = min(

            1.0,

            item.get(
                "confidence",
                0.55
            ) + 0.03

        )

        item["last_seen"] = now

        examples = item.setdefault(
            "examples",
            []
        )

        if user_input not in examples:

            examples.append(
                user_input
            )

            item["examples"] = examples[-5:]

        break

    else:

        memory.setdefault(

            "observed_patterns",

            []

        ).append(

            {

                "canonical_pattern":
                pattern,

                "intent":
                intent,

                "mode":

                resolved_data.get(
                    "intent",
                    abstraction["mode"]
                ),

                "confidence":
                max(

                    abstraction[
                        "confidence"
                    ],

                    0.55

                ),

                "count":
                1,

                "examples":
                [user_input],

                "created_at":
                now,

                "last_seen":
                now,

            }

        )

    # ==========================================
    # LEARNED PHRASES
    # ==========================================

    if phrase:

        learned_phrases = memory.setdefault(

            "learned_phrases",

            []

        )

        for item in learned_phrases:

            if item.get(
                "phrase"
            ) != phrase:

                continue

            item["count"] = item.get(
                "count",
                0
            ) + 1

            item["mapped_intent"] = intent

            item["mode"] = abstraction[
                "mode"
            ]

            item["confidence"] = min(

                0.99,

                item.get(
                    "confidence",
                    0.55
                ) + 0.05

            )

            item["last_seen"] = now

            examples = item.setdefault(
                "examples",
                []
            )

            if user_input not in examples:

                examples.append(
                    user_input
                )

                item["examples"] = examples[-5:]

            break

        else:

            learned_phrases.append(

                {

                    "phrase":
                    phrase,

                    "mapped_intent":
                    intent,

                    "mode":
                    abstraction["mode"],

                    "confidence":
                    max(

                        abstraction[
                            "confidence"
                        ],

                        0.55

                    ),

                    "count":
                    1,

                    "examples":
                    [user_input],

                    "created_at":
                    now,

                    "last_seen":
                    now,

                }

            )

    # ==========================================
    # AUTONOMOUS CLUSTER LEARNING
    # ==========================================

    if (

        phrase

        and

        len(

            phrase.split()

        ) >= 2

    ):

        clusters = memory.setdefault(

            "pattern_clusters",

            {}

        )

        cluster = clusters.setdefault(

            intent,

            {

                "meaning":
                intent,

                "mapped_intent":
                intent,

                "mode":
                abstraction["mode"],

                "confidence":
                0.72,

                "phrases":
                [],

                "examples":
                [],

                "created_at":
                now,

                "last_seen":
                now

            }

        )

        cluster["last_seen"] = now

        cluster["confidence"] = min(

            0.99,

            cluster.get(
                "confidence",
                0.72
            ) + 0.02

        )

        phrases = cluster.setdefault(
            "phrases",
            []
        )

        if phrase not in phrases:

            phrases.append(
                phrase
            )

        examples = cluster.setdefault(
            "examples",
            []
        )

        if user_input not in examples:

            examples.append(
                user_input
            )

            cluster["examples"] = examples[-10:]

    # ==========================================
    # INTERACTION STATS
    # ==========================================

    stats = memory.setdefault(

        "interaction_stats",

        {}

    )

    stats[intent] = stats.get(
        intent,
        0
    ) + 1

    # ==========================================
    # SAVE MEMORY
    # ==========================================

    save_intent_memory(
        memory
    )

    return {

        "status":
        "learned_pattern",

        "intent":
        intent,

        "pattern":
        pattern,

        "phrase":
        phrase

    }


def teach_phrase_alias(source_phrase, target_phrase):
    memory = load_intent_memory()
    aliases = memory.setdefault("phrase_aliases", {})
    aliases[source_phrase.lower().strip()] = target_phrase.lower().strip()
    save_intent_memory(memory)

    return {
        "status": "learned_alias",
        "source": source_phrase,
        "target": target_phrase,
    }

def detect_structural_signals(text):

    quantity_match = re.search(

        r"\b\d+(?:\.\d+)?\b",

        text

    )

    # ==========================================
    # IGNORE FERTILIZER GRADES
    # ==========================================

    fertilizer_pattern = r"\d{1,2}[.:]\d{1,2}[.:]\d{1,2}"

    if re.search(

        fertilizer_pattern,

        text

    ):

        quantity_match = None

    # ==========================================
    # FINAL QUANTITY FLAG
    # ==========================================

    has_quantity = quantity_match is not None

    # ==========================================
    # QUERY WORDS
    # ==========================================

    query_words = [

        # ==========================================
        # BASIC QUERY
        # ==========================================

        "kitna",
        "kitne",
        "kab",

        # ==========================================
        # INFORMATION SEEKING
        # ==========================================

        "history",
        "summary",
        "report",
        "details",

        # ==========================================
        # ACTION QUERY
        # ==========================================

        "dikhao",
        "batao",

    ]

    # ==========================================
    # SEMANTIC QUERY PATTERNS
    # ==========================================

    query_patterns = [

        r"\bkaunsa\b",
        r"\bkonsa\b",
        r"\bkaunsi\b",
        r"\bkonsi\b",

        r"\bkitna\b",
        r"\bkitne\b",

        r"\bkab\b"

    ]

    # ==========================================
    # QUERY WORD DETECTION
    # ==========================================

    has_query_words = any(

        word in text

        for word in query_words

    )

    # ==========================================
    # SEMANTIC QUERY DETECTION
    # ==========================================

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
# DOMINANT ENTITY TYPE
# ==========================================

def dominant_entity_type(entities):

    if not entities:

        return None

    priority = [

        "worker",
        "crop",
        "product"

    ]

    for entity_type in priority:

        if entity_type in entities:

            return entity_type

    return None

# ==========================================
# DETECT STATEMENT TYPE
# ==========================================

def detect_statement_type(

    text,

    signals

):

    # ==========================================
    # QUESTION
    # ==========================================

    if signals["has_query_words"]:

        return "question"

    # ==========================================
    # FACT / ENTRY
    # ==========================================

    if signals["has_quantity"]:

        return "fact"

    # ==========================================
    # UNKNOWN
    # ==========================================

    return "unknown"
# ==========================================
# NEEDS SEMANTIC CLARIFICATION
# ==========================================

def needs_semantic_clarification(

    confidence,

    mode,

    query_type

):

    # ==========================================
    # HIGH CONFIDENCE
    # ==========================================

    if confidence >= 0.65:

        return False

    # ==========================================
    # QUERY ALREADY UNDERSTOOD
    # ==========================================

    if query_type:

        return False

    # ==========================================
    # NEED USER HELP
    # ==========================================

    return True

# ==========================================
# BUILD SEMANTIC STATE
# ==========================================

def build_semantic_state(

    user_input

):

    abstraction = abstract_user_intent(

        user_input

    )
    

    semantic_state = {

        # ==========================================
        # RAW INPUT
        # ==========================================

        "raw_input":
        user_input,

        # ==========================================
        # NORMALIZED
        # ==========================================

        "normalized_text":
        abstraction.get(
            "normalized_text"
        ),

        # ==========================================
        # CORE UNDERSTANDING
        # ==========================================

        "intent":
        abstraction.get(
            "candidate_intent"
        ),

        "query_type":
        abstraction.get(
            "query_type"
        ),

        "mode":
        abstraction.get(
            "mode"
        ),
        
        # ==========================================
        # ENTITIES
        # ==========================================

        "entities":
        abstraction.get(
            "entities",
            {}
        ).copy(),

        # ==========================================
        # CONFIDENCE
        # ==========================================

        "confidence":
        abstraction.get(
            "confidence"
        ),

        # ==========================================
        # CONFIDENCE UPDATES
        # ==========================================

        "confidence_updates": {

            "intent_confidence":

            abstraction.get(
                "confidence",
                0
            )

        },

        # ==========================================
        # SEMANTIC DETAILS
        # ==========================================

        "semantic_focus":
        dict(
            abstraction.get(
                "semantic_focus",
                {}
            )
        ),

       "reasoning_trace":
        list(
            abstraction.get(
                "reasoning_trace",
                []
            )
        ),

        # ==========================================
        # EXECUTION FLAGS
        # ==========================================

        "is_query":
        abstraction.get(
            "mode"
        ) == "query",

        "is_entry":
        abstraction.get(
            "mode"
        ) == "entry",

        # ==========================================
        # SAVE STATUS
        # ==========================================

        "save_status":
        None,

        # ==========================================
        # RESPONSE
        # ==========================================

        "response":
        None

    }
    # ==========================================
    # ENTITY → TOP LEVEL SYNC
    # ==========================================

    for key, value in semantic_state.get(

        "entities",

        {}

    ).items():

        semantic_state[key] = value
    # ==========================================
    # QUERY OVERRIDES INTENT
    # ==========================================

    if semantic_state.get(

        "query_type"

    ):

        semantic_state[

            "intent"

        ] = "query"

        semantic_state[

            "mode"

        ] = "query"

        semantic_state[

            "is_query"

        ] = True

        semantic_state[

            "is_entry"

        ] = False
    # ==========================================
    # CLARIFICATION CLEANUP
    # ==========================================

    if not semantic_state.get(

        "needs_clarification"

    ):

        semantic_state[
            "clarification_type"
        ] = None

    # ==========================================
    # HARVEST EXTRACTOR
    # ==========================================

    def extract_harvest(

        semantic_state

    ):

        return semantic_state


    # ==========================================
    # SPRAY EXTRACTOR
    # ==========================================

    def extract_spray(

        semantic_state

    ):

        return semantic_state


    # ==========================================
    # EXPENSE EXTRACTOR
    # ==========================================

    def extract_expense(

        semantic_state

    ):

        return semantic_state
    # ==========================================
    # OPERATION
    # ==========================================

    operation = semantic_state.get(
        "operation"
    )

    if operation == "harvest":

        semantic_state = extract_harvest(
            semantic_state
        )

    elif operation == "spray":

        semantic_state = extract_spray(
            semantic_state
        )

    elif operation == "expense":

        semantic_state = extract_expense(
            semantic_state
        )
    # ==========================================
    # FINAL RETURN
    # ==========================================

    return semantic_state
