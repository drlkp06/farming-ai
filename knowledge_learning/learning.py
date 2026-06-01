import json
import os
import re

from knowledge_learning.semantic_knowledge import (
    teach_phrase_alias
)

from knowledge_learning.semantic_learning import (
    approve_candidate_learning
)

from core_brain.context_engine import (
    get_pending_learning,
    set_pending_learning,
    clear_pending_learning
)

from memory_system.dynamic_memory import (
    save_dynamic_keyword
)
from memory_system.entity_memory import (
    save_entity
)
# ==========================================
# FILE PATHS
# ==========================================

VOCAB_FILE = (
    "config_memory/vocab.json"
)

SEMANTIC_STATS_FILE = (
    "config_memory/semantic_stats.json"
)

# ==========================================
# VALID LEARNING GROUPS
# ==========================================

VALID_LEARNING_GROUPS = {

    "payment",
    "expense",
    "treatment",
    "harvest",

    "crop",
    "product",

    "worker",
    "vendor",
    "buyer",

    "pest"

}
# ==========================================
# ROLE TYPES
# ==========================================

ROLE_TYPES = {

    "worker",

    "vendor",

    "buyer",

    "crop",

    "product",

    "pest"

}
# ==========================================
# FUNCTIONAL LANGUAGE MEMORY
# ==========================================

FUNCTIONAL_LANGUAGE_WORDS = {

    # QUERY
    "kitna": "query_quantity",
    "kitni": "query_quantity",
    "kitne": "query_quantity",

    "kya": "query_general",
    "kab": "query_date",
    "kaha": "query_location",

    # CONTINUATION
    "aur": "continuation",
    "or": "continuation",
    "and": "continuation",

    "fir": "continuation",
    "phir": "continuation",

    # TIME
    "aaj": "time_reference",
    "kal": "time_reference",
    "abhi": "time_reference",

    # AGGREGATION
    "total": "aggregation",
    "sab": "aggregation",

    # HELPERS
    "hua": "helper_verb",
    "hui": "helper_verb",
    "hoga": "helper_verb",
    "tha": "helper_verb",
    "thi": "helper_verb",
    "the": "helper_verb",

    "hai": "helper_verb",
    "hain": "helper_verb",

    # GRAMMAR CONNECTORS
    "me": "grammar_connector",
    "mai": "grammar_connector",

    "ki": "grammar_connector",
    "ka": "grammar_connector",
    "ke": "grammar_connector",

    "ko": "grammar_connector",
    "se": "grammar_connector",
    "par": "grammar_connector",

    # PAYMENT HELPERS
    "diya": "payment_helper",
    "diye": "payment_helper",

    # HARVEST HELPERS
    "nikla": "harvest_helper",
    "nikli": "harvest_helper",
    "nikle": "harvest_helper",

    # ACTION HELPERS
    "kiya": "action_helper",
    "dala": "action_helper",
    "daala": "action_helper",

}
# ==========================================
# DEBUG CONFIG
# ==========================================

DEBUG_LEARNING = True

def debug_log(*args):

    if DEBUG_LEARNING:

        print(

            "\n[LEARNING DEBUG]",

            *args

        )
# ==========================================
# LOAD OPERATION KEYWORDS
# ==========================================

def load_operation_keywords():

    intents_file = (

        "farming_domain/intents.json"

    )

    if not os.path.exists(

        intents_file

    ):

        return set()

    try:

        with open(

            intents_file,
            "r",
            encoding="utf-8"

        ) as f:

            intents = json.load(f)

    except Exception:

        return set()

    operation_words = set()

    # ==========================================
    # INTENT NAMES
    # ==========================================

    for intent_name in intents:

        operation_words.add(

            intent_name
            .lower()
            .strip()

        )

    # ==========================================
    # INTENT PATTERNS
    # ==========================================

    for intent_data in intents.values():

        patterns = (

        intent_data.get(
            "patterns",
            []
        )

        +

        intent_data.get(
            "examples",
            []
        )

    )

        for pattern in patterns:

            words = re.findall(

                r"\b[a-zA-Z]+\b",

                pattern.lower()

            )

            operation_words.update(
                words
            )

    return operation_words
# ==========================================
# LOAD JSON FILE
# ==========================================

def load_json_file(path):

    if not os.path.exists(path):

        return {}

    try:

        with open(

            path,
            "r",
            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return {}

# ==========================================
# SAVE JSON FILE
# ==========================================

def save_json_file(path, data):

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

# ==========================================
# VOCAB MEMORY
# ==========================================

def load_vocab():

    return load_json_file(
        VOCAB_FILE
    )

def save_vocab(vocab):

    save_json_file(
        VOCAB_FILE,
        vocab
    )

# ==========================================
# SEMANTIC STATS MEMORY
# ==========================================

def load_semantic_stats():

    return load_json_file(
        SEMANTIC_STATS_FILE
    )

def save_semantic_stats(stats):

    save_json_file(
        SEMANTIC_STATS_FILE,
        stats
    )

# ==========================================
# UPDATE SEMANTIC STATS
# ==========================================

def update_semantic_statistics(

    word,
    semantic_role

):

    stats = load_semantic_stats()

    if word not in stats:

        stats[word] = {

            "count": 0,
            "roles": {}

        }

    stats[word]["count"] += 1

    roles = stats[word]["roles"]

    roles[semantic_role] = (

        roles.get(
            semantic_role,
            0
        ) + 1

    )

    save_semantic_stats(stats)

# ==========================================
# LEARN WORD
# ==========================================

def learn_word(

    word,
    data

):

    vocab = load_vocab()

    word = (

        word
        .lower()
        .strip()

    )

    vocab[word] = data

    save_vocab(vocab)

    return {

        "status":
        "learned",

        "word":
        word

    }

# ==========================================
# GET WORD
# ==========================================

def get_word(word):

    vocab = load_vocab()

    return vocab.get(

        word.lower().strip()

    )

# ==========================================
# WORD EXISTS
# ==========================================

def word_exists(word):

    vocab = load_vocab()

    return (

        word.lower().strip()

        in

        vocab

    )

# ==========================================
# GET ALL WORDS
# ==========================================

def get_all_words():

    return list(

        load_vocab().keys()

    )

# ==========================================
# DELETE WORD
# ==========================================

def delete_word(word):

    vocab = load_vocab()

    word = word.lower().strip()

    if word in vocab:

        del vocab[word]

        save_vocab(vocab)

        return {

            "deleted": True,
            "word": word

        }

    return {

        "deleted": False,
        "word": word

    }

# ==========================================
# CLASSIFY SEMANTIC WORD
# ==========================================

def classify_semantic_word(word):

    word = word.lower().strip()

    if word in FUNCTIONAL_LANGUAGE_WORDS:

        return {

            "type":
            "functional_language",

            "role":

            FUNCTIONAL_LANGUAGE_WORDS[
                word
            ]

        }

    if re.fullmatch(r"\d+", word):

        return {

            "type":
            "numeric"

        }

    return {

        "type":
        "unknown"

    }

# ==========================================
# CHECK LEARNING COMMAND
# ==========================================

def is_learning_command(text):

    text = text.lower().strip()

    prefixes = [

        "remember",
        "learn ",
        "train ",
        "teach "

    ]

    return any(

        text.startswith(prefix)

        for prefix in prefixes

    )

# ==========================================
# CHECK LEARNING CONFIRMATION
# ==========================================

def is_learning_confirmation(text):

    lowered = text.lower().strip()

    confirmations = [

        "yes",
        "y",

        "haan",
        "han",
        "haanji",

        "ok",
        "okay",

        "confirm",
        "approve",
        "save",

        "no",
        "n",

        "nahin",
        "na",

        "cancel",
        "skip",
        "reject"

    ]

    if lowered in confirmations:

        return True

    if lowered in ROLE_TYPES:

        return True

    return False
# ==========================================
# RESOLVE LEARNING CONFIRMATION
# ==========================================

def resolve_learning_confirmation(text):
    print("\n[LEARNING DEBUG]")
    print("INPUT:", text)

    pending = get_pending_learning()

    print("PENDING:", pending)
    from core_brain.semantic_engine import (

    build_semantic_state,

)
    lowered = text.lower().strip()

    pending = get_pending_learning()

    if not pending:

        return {

            "status":
            "idle",

            "message":
            "No pending learning to confirm."

        }
    # ==========================================
    # ROLE RESPONSE
    # ==========================================

    if lowered in ROLE_TYPES:

        debug_log(

            "ROLE DETECTED",

            lowered

        )

        target_word = (

            pending.get(
                "target_word"
            )

            or

            pending.get(
                "raw_input"
            )

        )

        learn_word(

        target_word,

        {

            "type":
            lowered,

            "source":
            "interactive_learning"

        }

    )
        # ==========================================
        # ENTITY DATABASE SAVE
        # ==========================================

        save_entity(

            target_word,

            lowered

        )
        debug_log(

            "LEARNED",

            target_word,

            "AS",

            lowered

        )

        clear_pending_learning()

        return {

            "status":
                "confirmed",

            "entity_type":
                lowered,

            "learned_word":
                target_word

        }
    # ==========================================
    # REJECT
    # ==========================================

    debug_log(

        "REJECT ROUTE"

    )

    if lowered in [
        "no",
        "n",

        "nahin",
        "na",

        "cancel",
        "skip",
        "reject"

    ]:

        clear_pending_learning()

        return {

            "status":
            "rejected",

            "pending_learning":
            None

        }
    print("ROUTE: CONFIRM")
    # ==========================================
    # CONFIRM
    # ==========================================

    pending["confirmed"] = True
    debug_log(

        "CONFIRM ROUTE"

    )
    semantic_state = build_semantic_state(

        pending["raw_input"]

    )

    commit_result = {

        "approved": True,

        "learning_type": "semantic_memory",

        "source": "adaptive_learning"

    }

    if pending.get("type") == "unknown_word":

        learn_word(

            pending["target_word"],

            {
                "context":
                pending.get(
                    "suggested_context"
                ),

                "source":
                "adaptive_learning"
            }

        )

    clear_pending_learning()

    return {

        "status":
        "confirmed",

        "pending_learning":
        None,

        "commit_result":
        commit_result

    }

# ==========================================
# PROCESS LEARNING COMMAND
# ==========================================

def process_learning_command(text):
    from core_brain.semantic_engine import (

    build_semantic_state,

)
    text = text.strip()

    alias_match = re.match(

        r"^(?:learn|teach|train)\s+alias\s+(.+?)\s+(.+)$",

        text,

        re.IGNORECASE

    )

    if alias_match:

        return teach_phrase_alias(

            alias_match.group(1),
            alias_match.group(2)

        )

    phrase_match = re.match(

        r"^(?:learn|teach|train)\s+phrase\s+(.+?)\s+means\s+(.+)$",

        text,

        re.IGNORECASE

    )

    if phrase_match:

        return teach_phrase_alias(

            phrase_match.group(1),
            phrase_match.group(2)

        )

    parts = text.split(
        maxsplit=2
    )

    if len(parts) < 3:

        return {

            "status":
            "error",

            "message":
            "Format: learn <intent> <sentence>"

        }

    intent = parts[1].lower()
    sentence = parts[2]

    if intent not in VALID_LEARNING_GROUPS:

        return {

            "status":
            "invalid_intent",

            "message":
            f"Unknown learning group: {intent}"

        }

    semantic_state = build_semantic_state(
        sentence
    )

    semantic_state[
        "intent"
    ] = intent

    return {

        "status":
        "learned",

        "intent":
        intent,

        "sentence":
        sentence,

    }

# ==========================================
# LEARN FROM SEMANTIC STATE
# ==========================================

def learn_from_semantic_state(

    semantic_state

):

    if not semantic_state:

        return None

    raw_input = semantic_state.get(
        "raw_input"
    )

    if not raw_input:

        return None

    normalized = (

        raw_input
        .lower()
        .strip()

    )

    # ==========================================
    # FUNCTIONAL LANGUAGE COGNITION
    # ==========================================

    semantic_classification = (

        classify_semantic_word(
            normalized
        )

    )

    if (

        semantic_classification.get(
            "type"
        )

        ==

        "functional_language"

    ):

        role = semantic_classification.get(
            "role"
        )

        update_semantic_statistics(

            normalized,
            role

        )

        save_dynamic_keyword(

            "functional_language",
            normalized

        )

        return {

            "status":
            "functional_language",

            "word":
            normalized,

            "role":
            role

        }

    # ==========================================
    # DUPLICATE PENDING PROTECTION
    # ==========================================

    pending = get_pending_learning()

    if pending:

        if pending.get(
            "raw_input"
        ) == raw_input:

            return None

        clear_pending_learning()

    # ==========================================
    # CONFIDENCE FILTER
    # ==========================================

    confidence = semantic_state.get(
        "confidence",
        0
    )

    if confidence >= 0.75:

        return None

    # ==========================================
    # ENTITY PROTECTION
    # ==========================================

    entities = semantic_state.get(
        "entities",
        {}
    )

    if entities:

        known_entity_detected = any(

            value

            for value in entities.values()

        )

        if known_entity_detected:

            return None

    # ==========================================
    # OPERATION PROTECTION
    # ==========================================

    operation = semantic_state.get(
        "operation"
    )

    if (

        operation
        and
        operation != "unknown"

    ):

        return None

    # ==========================================
    # FUNCTIONAL LANGUAGE PROTECTION
    # ==========================================

    tokens = re.findall(

        r"\b\w+\b",

        raw_input.lower()

    )

    functional_only = all(

        token in FUNCTIONAL_LANGUAGE_WORDS

        for token in tokens

    )

    if functional_only:

        return None

    # ==========================================
    # STORE PENDING LEARNING
    # ==========================================
    debug_log(

        "CREATING PENDING LEARNING",

        raw_input

    )
    set_pending_learning({

        "raw_input":
        raw_input,

        "operation":
        semantic_state.get(
            "operation"
        ),

        "mode":
        semantic_state.get(
            "mode"
        ),

        "query_type":
        semantic_state.get(
            "query_type"
        ),

        "entities":

        semantic_state.get(
            "entities",
            {}
        ),

        "semantic_summary": {

            "operation":
            semantic_state.get(
                "operation"
            ),

            "mode":
            semantic_state.get(
                "mode"
            ),

            "query_type":
            semantic_state.get(
                "query_type"
            ),

            "entities":

            semantic_state.get(
                "entities",
                {}
            ),

            "confidence":
            semantic_state.get(
                "confidence"
            )

        }

    })

    return {

        "approved": True,

        "learning_type":
        "semantic_memory",

        "source":
        "adaptive_learning"

    }