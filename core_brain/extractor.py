import re
from datetime import datetime, timedelta

from core_brain.semantic_engine import (
    build_semantic_state,
    add_reasoning_trace
)

from farming_domain.rule_engine import (
    extract_by_rules
)

from core_brain.context_engine import (
    resolve_pending_field,
    set_pending_field,
    set_last_query_context,
    inherit_context,
    get_last_query_context,
)

from farming_domain.treatment_engine import (
    apply_treatment_context_rules
)

from memory_system.event_memory import (
    save_farm_event,
)

from knowledge_learning.learning import (
    is_learning_command,
    is_learning_confirmation,
    process_learning_command,
    resolve_learning_confirmation,
    learn_from_semantic_state,
    FUNCTIONAL_LANGUAGE_WORDS,
     load_operation_keywords
)

from knowledge_learning.semantic_learning import (
    approve_candidate_rule
)

from data_layer.query_engine import (
    execute_query
)

from memory_system.entity_memory import (
    load_entities
)

from knowledge_learning.vocabulary import (
    CROPS
)

from config import (
     KNOWN_UNITS
)
# ==========================================
# FARM EVENT OPERATIONS
# ==========================================

FARM_EVENT_OPERATIONS = [

    "treatment",
    "harvest",
    "payment",
    "expense",
    "irrigation"

]

QUERY_MARKERS = [

    "kitna",
    "kitne",
    "kitana",
    "kab",
    "history",
    "summary",
    "report",
    "batao",
    "dikhao"

]

DATE_WORDS = [

    "aaj",
    "kal",
    "parso"

]

ENTRY_OPERATION_WORDS = [

    "nikla",
    "nikle",
    "harvest",
    "todai",
    "tudai",
    "toda",
    "production",
    "output"

]


def strip_chat_prompt_prefix(user_input):

    return re.sub(
        r"^(?:\s*you\s*:\s*)+",
        "",
        user_input,
        flags=re.IGNORECASE
    ).strip()


def detect_crop_from_text(text):

    normalized = (text or "").lower()

    for alias, crop in sorted(
        CROPS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):

        if re.search(
            rf"\b{re.escape(alias.lower())}\b",
            normalized
        ):

            return crop

    for crop in load_entities(
        "crop"
    ):

        if re.search(
            rf"\b{re.escape(crop.lower())}\b",
            normalized
        ):

            return crop

    return None


def detect_relative_date(text):

    if not text:

        return None

    normalized = text.lower()

    today = datetime.now().date()

    if re.search(
        r"\baaj\b",
        normalized
    ):

        return today.isoformat()

    if re.search(
        r"\bkal\b",
        normalized
    ):

        return (
            today - timedelta(days=1)
        ).isoformat()

    if re.search(
        r"\bparso\b",
        normalized
    ):

        return (
            today - timedelta(days=2)
        ).isoformat()

    match = re.search(
        r"\bdo\s+din\s+(?:pahale|pehle)\b",
        normalized
    )

    if match:

        return (
            today - timedelta(days=2)
        ).isoformat()

    return None


# ==========================================
# ATTACH DATE CONTEXT
# ==========================================

def attach_date_context(

    semantic_state

):

    date_value = detect_relative_date(

        semantic_state.get(
            "raw_input",
            ""
        )

    )

    if not date_value:

        return semantic_state

    semantic_state[
        "event_date"
    ] = date_value

    semantic_state[
        "date_filter"
    ] = date_value

    return semantic_state
# ==========================================
# APPLY FOLLOWUP QUERY CONTEXT
# ==========================================

def apply_followup_query_context(

    semantic_state

):

    last_query = get_last_query_context()

    if not last_query:

        return semantic_state

    current_query_type = semantic_state.get(
        "query_type"
    )

    current_operation = semantic_state.get(
        "operation"
    )

    # ======================================
    # DO NOT OVERRIDE A SPECIFIC CURRENT QUERY
    # ======================================

    if current_query_type not in [

        None,
        "",
        "general_query"

    ]:

        return semantic_state

    if current_operation not in [

        None,
        "",
        "unknown"

    ]:

        return semantic_state

    normalized_text = semantic_state.get(

        "normalized_text",
        ""

    ).strip()

    # ======================================
    # IGNORE EMPTY CONNECTORS
    # ======================================

    if normalized_text in [

        "aur",
        "and",

        "fir",
        "phir"

    ]:

        return semantic_state

    # ======================================
    # STOP EMPTY CONTEXT
    # ======================================

    if (

        not semantic_state.get(
            "date_filter"
        )

        and

        not semantic_state.get(
            "entities"
        )

    ):

        return semantic_state

    # ======================================
    # INHERIT DATE
    # ======================================

    if not semantic_state.get(
        "date_filter"
    ):

        previous_date = last_query.get(
            "date_filter"
        )

        if previous_date:

            semantic_state[
                "date_filter"
            ] = previous_date

            semantic_state[
                "event_date"
            ] = (

                last_query.get(
                    "event_date"
                )

                or

                previous_date

            )

    # ======================================
    # MERGE ENTITIES
    # ======================================

    merged_entities = dict(

        last_query.get(
            "entities",
            {}
        )

    )

    merged_entities.update(

        semantic_state.get(
            "entities",
            {}
        )

    )

    if not merged_entities:

        return semantic_state

    # ======================================
    # QUERY ALIGNMENT
    # ======================================

    semantic_state[
        "query_type"
    ] = last_query.get(
        "query_type"
    )

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

    semantic_state[
        "operation"
    ] = last_query.get(
        "operation"
    )

    semantic_state[
        "entities"
    ] = merged_entities

    for field, value in merged_entities.items():

        if value:

            semantic_state[
                field
            ] = value

    semantic_state.setdefault(

        "reasoning_trace",
        []

    ).append(

        "last query context reused"

    )

    return semantic_state


def remember_query_context(semantic_state):

    query_type = semantic_state.get(
    "query_type"
)

    if not query_type:

        return

    # ==========================================
    # IGNORE WEAK GENERIC QUERIES
    # ==========================================

    if query_type == "general_query":

        return

    if semantic_state.get(
        "needs_clarification"
    ):

        return

    if not semantic_state.get(
        "query_type"
    ):

        return

    set_last_query_context(
        semantic_state
    )

# ==========================================
# ATTACH EXTRA DATA
# ==========================================

def attach_extraction_data(

    semantic_state,
    extracted_data

):

    if not extracted_data:

        return semantic_state

    entities = dict(

        semantic_state.get(
            "entities",
            {}
        )

    )

    preserve_query_fields = bool(
        semantic_state.get("is_query")
    )

    protected_query_fields = {
        "intent",
        "mode",
        "is_query",
        "is_entry",
        "query_type",
        "semantic_focus",
    }

    for key, value in extracted_data.items():

        if (
            preserve_query_fields
            and key in protected_query_fields
        ):

            continue

        if (

            value in [
                None,
                "",
                []
            ]

            and

            semantic_state.get(
                key
            )

        ):

            continue

        semantic_state[key] = value

        if key in [

            "farm",
            "crop",
            "worker",
            "product",
            "vendor",
            "buyer"

        ] and value:

            entities[key] = value

    semantic_state[
        "entities"
    ] = entities

    entity_fields = [

        "farm",
        "crop",
        "worker",
        "product",
        "vendor",
        "buyer"

    ]

    for field in entity_fields:

        if semantic_state.get(
            field
        ):

            entities[
                field
            ] = semantic_state.get(
                field
            )

        elif entities.get(
            field
        ):

            semantic_state[
                field
            ] = entities.get(
                field
            )

    missing_fields = semantic_state.get(
        "missing_fields",
        []
    )

    if missing_fields:

        missing_fields = [

            field

            for field in missing_fields

            if not semantic_state.get(
                field
            )

            and

            not entities.get(
                field
            )

        ]

        semantic_state[
            "missing_fields"
        ] = missing_fields

        if not missing_fields:

            semantic_state[
                "needs_clarification"
            ] = False

            semantic_state[
                "clarification_type"
            ] = None

            semantic_state[
                "context_status"
            ] = "completed"

    # ==========================================
    # CLEAR STALE MISSING FIELDS
    # ==========================================

    current_missing_fields = semantic_state.get(
        "missing_fields",
        []
    )

    if current_missing_fields:

        resolved_fields = set()

        for field in list(current_missing_fields):

            if semantic_state.get(field):

                resolved_fields.add(field)

        if resolved_fields:

            semantic_state["missing_fields"] = [

                field

                for field in current_missing_fields

                if field not in resolved_fields

            ]

        if not semantic_state["missing_fields"]:

            semantic_state[
                "needs_clarification"
            ] = False

            semantic_state[
                "clarification_type"
            ] = None

            semantic_state[
                "context_status"
            ] = "completed"

    return semantic_state

# ==========================================
# CLEAN SEMANTIC STATE
# ==========================================

def cleanup_semantic_state(

    semantic_state

):

    if not semantic_state:

        return semantic_state

    # ==========================================
    # REMOVE INVALID CLARIFICATION
    # ==========================================

    if not semantic_state.get(

        "needs_clarification"

    ):

        semantic_state[
            "clarification_type"
        ] = None

        semantic_state[
            "missing_fields"
        ] = []

    return semantic_state


# ==========================================
# MULTI EVENT HELPERS
# ==========================================

def split_event_parts(

    user_input,

    semantic_mode=None

):

    # ==========================================
    # QUERY MODE
    # ==========================================

    if semantic_mode == "query":

        return [

            user_input.strip()

        ]

    # Keep shared context for compact harvest lists:
    # "satpuda se 100 kg cucumber aur 50 kg tomato nikla"
    # -> "satpuda se 100 kg cucumber nikla",
    #    "satpuda se 50 kg tomato nikla"
    clean_input = strip_chat_prompt_prefix(
        user_input
    )

    compact_harvest_parts = expand_compact_harvest_parts(
        clean_input
    )

    if compact_harvest_parts:

        return compact_harvest_parts

    # ==========================================
    # ENTRY / EVENT MODE
    # ==========================================

    # SAFE HARD SPLITS ONLY

    parts = re.split(

        r"\n+|[.;]+",

        clean_input,

        flags=re.IGNORECASE

    )

    clean_parts = []

    for part in parts:

        part = part.strip()

        if not part:

            continue

        clean_parts.append(
            part
        )

    return clean_parts


def expand_compact_harvest_parts(user_input):

    if not re.search(
        r"\b(?:and|aur)\b",
        user_input,
        flags=re.IGNORECASE
    ):

        return None

    operation_pattern = "|".join(
        re.escape(word)
        for word in ENTRY_OPERATION_WORDS
    )

    operation_tail_match = re.search(
        rf"\b(?:{operation_pattern})\b(?:\s+(?:hua|hai|tha|thi))?\s*[.!?।]*\s*$",
        user_input,
        flags=re.IGNORECASE
    )

    if not operation_tail_match:

        return None

    operation_tail = re.sub(
        r"[.!?।\s]+$",
        "",
        operation_tail_match.group(0)
    ).strip()

    prefix_match = re.match(
        r"\s*((?:(?:aaj|kal|parso)\s+)?[a-z][a-z0-9_]*(?:\s+farm)?\s+se\s+)",
        user_input,
        flags=re.IGNORECASE
    )

    shared_prefix = (
        prefix_match.group(1).strip()
        if prefix_match
        else None
    )

    parts = re.split(
        r"\b(?:and|aur)\b",
        user_input,
        flags=re.IGNORECASE
    )

    expanded_parts = []

    for part in parts:

        part = re.sub(
            r"[.!?।\s]+$",
            "",
            part.strip()
        )

        if not part:

            continue

        if (
            shared_prefix
            and
            not re.search(
                r"\bse\b",
                part,
                flags=re.IGNORECASE
            )
        ):

            part = f"{shared_prefix} {part}".strip()

        if not re.search(
            rf"\b(?:{operation_pattern})\b",
            part,
            flags=re.IGNORECASE
        ):

            part = f"{part} {operation_tail}".strip()

        expanded_parts.append(
            part
        )

    if len(expanded_parts) <= 1:

        return None

    return expanded_parts

def find_query_marker_position(text):

    positions = [

        match.start()

        for marker in QUERY_MARKERS

        for match in [
            re.search(
                rf"\b{re.escape(marker)}\b",
                text,
                flags=re.IGNORECASE
            )
        ]

        if match

    ]

    if not positions:

        return None

    return min(positions)


def find_entity_phrase(text, entity_types):

    candidates = []

    for entity_type in entity_types:

        for entity in load_entities(
            entity_type
        ):

            if not entity:

                continue

            candidates.append(
                entity.lower()
            )

            if entity_type == "farm":

                candidates.append(
                    f"{entity.lower()} farm"
                )

    candidates = sorted(

        set(candidates),

        key=len,

        reverse=True

    )

    for candidate in candidates:

        match = re.search(

            rf"\b{re.escape(candidate)}\b",

            text.lower()

        )

        if match:

            return match

    fallback = re.search(

        r"(?:^|\s)(?!aaj\b|kal\b|parso\b)([a-z][a-z0-9_]*)(?=\s*(?:ko|se)?\s*$)",

        text.lower()

    )

    if fallback:

        return fallback

    return None


def expand_shared_query_parts(user_input):

    marker_position = find_query_marker_position(
        user_input
    )

    if marker_position is None:

        return None

    if not re.search(
        r"\b(?:aur|and)\b",
        user_input,
        flags=re.IGNORECASE
    ):

        return None

    head = user_input[:marker_position].strip()

    tail = user_input[marker_position:].strip()

    segments = [

        segment.strip()

        for segment in re.split(

            r"\b(?:aur|and)\b",

            head,

            flags=re.IGNORECASE

        )

        if segment and segment.strip()

    ]

    if len(segments) <= 1:

        return None

    entity_types = [

        "farm",
        "worker"

    ]

    if not all(

        find_entity_phrase(
            segment,
            entity_types
        )

        for segment in segments

    ):

        return None

    last_segment = segments[-1]

    last_match = find_entity_phrase(
        last_segment,
        entity_types
    )

    relation_suffix = ""

    if last_match:

        relation_suffix = last_segment[
            last_match.end():
        ].strip()

    expanded_parts = []

    for segment in segments:

        part = segment

        if relation_suffix:

            match = find_entity_phrase(
                part,
                entity_types
            )

            current_suffix = ""

            if match:

                current_suffix = part[
                    match.end():
                ].strip()

            if not current_suffix:

                part = (
                    f"{part} {relation_suffix}"
                ).strip()

        expanded_parts.append(
            f"{part} {tail}".strip()
        )

    return expanded_parts


def backfill_common_fields(semantic_states):

    for state in semantic_states:

        normalized_text = state.get(
            "normalized_text",
            ""
        )

        if state.get(
            "quantity"
        ) is None:

            quantity_match = re.search(

                r"\b\d+(?:\.\d+)?\b",

                normalized_text

            )

            if quantity_match:

                value = quantity_match.group()

                state[
                    "quantity"
                ] = (

                    float(value)

                    if "." in value

                    else int(value)

                )

        if not state.get(
            "unit"
        ):

            unit_match = re.search(

                r"\b(kg|kilo|litre|liter|ml|gram)\b",

                normalized_text

            )

            if unit_match:

                state[
                    "unit"
                ] = unit_match.group(1)

        explicit_crop = detect_crop_from_text(
            normalized_text
        )

        if explicit_crop:

            state[
                "crop"
            ] = explicit_crop

            state.setdefault(
                "entities",
                {}
            )[
                "crop"
            ] = explicit_crop

    common_fields = [

        "farm",
        "crop",
        "unit",
        "operation",
        "event_date",
        "date_filter"

    ]

    for field in common_fields:

        values = [

            state.get(field)

            for state in semantic_states

            if state.get(field)

        ]

        if len(set(values)) != 1:

            continue

        value = values[0]

        for state in semantic_states:

            if not state.get(field):

                state[field] = value

            entities = state.setdefault(
                "entities",
                {}
            )

            if field in [

                "farm",
                "crop",
                "worker",
                "product",
                "vendor",
                "buyer"

            ]:

                entities[field] = value

            missing_fields = state.get(
                "missing_fields",
                []
            )

            if field in missing_fields:

                missing_fields.remove(field)

            if not missing_fields:

                state[
                    "needs_clarification"
                ] = False

                state[
                    "context_status"
                ] = "completed"

    # ==========================================
    # REMOVE STALE MISSING FIELDS
    # ==========================================

    for state in semantic_states:

        missing_fields = state.get(
            "missing_fields",
            []
        )

        if not missing_fields:

            continue

        resolved_missing_fields = [

            field

            for field in missing_fields

            if not state.get(field)

        ]

        state[
            "missing_fields"
        ] = resolved_missing_fields

        if not resolved_missing_fields:

            state[
                "needs_clarification"
            ] = False

            state[
                "clarification_type"
            ] = None

            state[
                "context_status"
            ] = "completed"

    for state in semantic_states:

        if (

            state.get(
                "operation"
            )

            and

            state.get(
                "quantity"
            ) is not None

             and

            state.get("mode") in [

            "entry",
            "action"

    ]

):

            state[
                "intent"
            ] = "entry"

            state[
                "is_entry"
            ] = True

    return semantic_states

def process_semantic_state(semantic_state):

    extracted_data = extract_by_rules(

        semantic_state.get(
            "normalized_text"
        )

    )
    # ==========================================
    # STORE QUERY CONTEXT
    # ==========================================

    if semantic_state.get(

        "is_query"

    ):

        set_last_query_context(

            semantic_state

        )

        add_reasoning_trace(

            semantic_state,

            "query context stored"

        )

    if extracted_data:

        extracted_data = apply_treatment_context_rules(

            extracted_data,

            semantic_state.get(
                "normalized_text"
            )

        )

        semantic_state = attach_extraction_data(

            semantic_state,

            extracted_data

        )

    return semantic_state

# ==========================================
# SET PENDING FIELD
# ==========================================

def set_pending_if_needed(

    semantic_state

):

    if not semantic_state:

        return

    if not semantic_state.get(
        "needs_clarification"
    ):

        return

    missing_fields = semantic_state.get(
        "missing_fields",
        []
    )

    if not missing_fields:

        return

    set_pending_field(

        missing_fields[0],

        semantic_state

    )
# ==========================================
# PROCESS UNKNOWN INPUT
# ==========================================

def process_unknown_input(

    user_input,

    all_known_words

):

    from knowledge_learning.learning import (
        FUNCTIONAL_LANGUAGE_WORDS
    )

    normalized = (

        user_input
        .lower()
        .strip()

    )

    words = normalized.split()

    # ==========================================
    # CLEAN WORDS
    # ==========================================

    cleaned_words = []

    for word in words:

        word = word.strip(

            ".,!?()[]{}<>:;\"'"

        )

        if not word:

            continue

        cleaned_words.append(
            word
        )

    # ==========================================
    # FIND UNKNOWN WORDS
    # ==========================================

    unknown_words = []

    for word in cleaned_words:

        # ==========================================
        # IGNORE SMALL TOKENS
        # ==========================================

        if len(word) <= 2:

            continue

        # ==========================================
        # IGNORE NUMBERS
        # ==========================================

        if word.replace(

            ".",

            "",

            1

        ).isdigit():

            continue

        # ==========================================
        # IGNORE CONNECTOR WORDS
        # ==========================================

        if word in FUNCTIONAL_LANGUAGE_WORDS:

            continue

        # ==========================================
        # IGNORE KNOWN WORDS
        # ==========================================

        if word in all_known_words:

            continue

        unknown_words.append(
            word
        )

    # ==========================================
    # NO UNKNOWN WORD
    # ==========================================

    if not unknown_words:

        return None

    # ==========================================
    # TARGET WORD
    # ==========================================

    target_word = unknown_words[0]

    # ==========================================
    # CONTEXT DETECTION
    # ==========================================

    detected_context = None

    expense_words = [

        "diesel",
        "petrol",
        "fuel",
        "expense",
        "kharcha"

    ]

    payment_words = [

        "payment",
        "rupye",
        "diye",
        "diya"

    ]

    harvest_words = [

        "harvest",
        "tudai",
        "todai",
        "nikla"

    ]

    treatment_words = [

        "spray",
        "treatment",
        "dawai",
        "medicine"

    ]

    if any(

        word in normalized

        for word in expense_words

    ):

        detected_context = "expense"

    elif any(

        word in normalized

        for word in payment_words

    ):

        detected_context = "payment"

    elif any(

        word in normalized

        for word in harvest_words

    ):

        detected_context = "harvest"

    elif any(

        word in normalized

        for word in treatment_words

    ):

        detected_context = "treatment"

    # ==========================================
    # LEARNING RESPONSE
    # ==========================================

    if detected_context:

        message = (

            f"Mujhe '{target_word}' ka matlab nahi pata. "

            f"Kya yeh '{detected_context}' "

            f"category se related hai? "

            f"(yes/no)"

        )

    else:

        message = (

            f"Mujhe '{target_word}' ka matlab nahi pata. "

            "Kya yeh koi naya operation, "

            "entity ya semantic concept hai? "

            "(yes/no)"

        )

    return {

        "status":
        "pending_learning",

        "learning_suggestion": {

            "message":
            message,

            "target_word":
            target_word,

            "suggested_context":
            detected_context

        }

    }

# ==========================================
# SAVE EVENT
# ==========================================

def save_if_needed(

    semantic_state

):

    if not semantic_state.get(
        "is_entry"
    ):

        return semantic_state

    if semantic_state.get(
        "needs_clarification"
    ):

        semantic_state[
            "save_status"
        ] = {

            "saved":
            False,

            "reason":
            "needs_clarification"

        }

        return semantic_state

    operation = semantic_state.get(
        "operation"
    )

    if operation not in FARM_EVENT_OPERATIONS:

        return semantic_state

    save_status = save_farm_event(
        semantic_state
    )

    semantic_state[
        "save_status"
    ] = save_status

    return semantic_state

# ==========================================
# MAIN PROCESS ENGINE
# ==========================================

def process_input(user_input):

    # ==========================================
    # EMPTY INPUT
    # ==========================================

    if not user_input:

        return None

    user_input = strip_chat_prompt_prefix(

        user_input.strip()

    )

    if not user_input:

        return None

    # ==========================================
    # LEARNING CONFIRMATION
    # ==========================================

    if is_learning_confirmation(

        user_input

    ):

        confirmation_result = (

            resolve_learning_confirmation(

                user_input

            )

        )

        confirmation_state = {

            "raw_input":
            user_input,

            "is_query":
            False,

            "is_entry":
            False,

            "learning_confirmation":
            confirmation_result,

        }

        return [

            cleanup_semantic_state(

                confirmation_state

            )

        ]

    # ==========================================
    # LEARNING COMMAND
    # ==========================================

    if is_learning_command(

        user_input

    ):

        return process_learning_command(

            user_input

        )

    # ==========================================
    # MULTI EVENT DETECTION
    # ==========================================

    parts = (

        expand_shared_query_parts(
            user_input
        )

        or

        split_event_parts(
            user_input
        )

    )

    if not parts:

        parts = [

            user_input

        ]

    # ==========================================
    # BUILD STATES
    # ==========================================

    semantic_states = []

    previous_state = None

    for part in parts:

        state = build_semantic_state(
            part
        )

        # ==========================================
        # DATE CONTEXT
        # ==========================================

        state = attach_date_context(
            state
        )

        # ==========================================
        # CONTEXT INHERITANCE
        # ==========================================

        state = inherit_context(

            previous_state,

            state

        )
        # ==========================================
        # FOLLOWUP QUERY CONTEXT
        # ==========================================

        state = apply_followup_query_context(

            state

        )
        semantic_states.append(
            state
        )

        previous_state = state

    # ==========================================
    # PRIMARY STATE
    # ==========================================

    primary_state = semantic_states[0]

    # ==========================================
    # PENDING FIELD RESOLUTION
    # ==========================================

    pending_result = resolve_pending_field(
        user_input
    )

    if pending_result:

        save_if_needed(
            pending_result
        )

        pending_result[
            "is_entry"
        ] = True

        pending_result[
            "save_status"
        ] = {

            "saved":
            True,

            "reason":
            "clarification_completed"

        }

        return [

            cleanup_semantic_state(

                pending_result

            )

        ]

    # ==========================================
    # APPROVE RULE
    # ==========================================

    if user_input.lower().startswith(
        "approve rule "
    ):

        phrase = (

            user_input
            .lower()
            .replace(
                "approve rule ",
                ""
            )
            .strip()

        )

        approved = approve_candidate_rule(
            phrase
        )

        primary_state[
            "learning_confirmation"
        ] = {

            "status":
            "confirmed"

            if approved.get(
                "approved"
            )

            else

            "rejected",

            "commit_result":
            approved,

            "phrase":
            phrase

        }

        # ==========================================
        # CLEAR WORKING MEMORY
        # ==========================================

        primary_state[
            "pending_learning"
        ] = None

        primary_state[
            "query_result"
        ] = {

            "query_type":
            "rule_approval",

            "approved":
            approved,

            "phrase":
            phrase

        }

        primary_state[
            "is_query"
        ] = True

    # ==========================================
    # PROCESS STATES
    # ==========================================

    semantic_states = [

        process_semantic_state(
            state
        )

        for state in semantic_states

    ]

    # ==========================================
    # BACKFILL COMMON FIELDS
    # ==========================================

    semantic_states = backfill_common_fields(
        semantic_states
    )
   # ==========================================
    # NORMALIZED INPUT
    # ==========================================

    normalized_input = (

        user_input
        .lower()
        .strip()

    )

    # ==========================================
    # UNKNOWN INPUT LEARNING
    # ==========================================

    if not any(

        state.get("is_query")

        for state in semantic_states

    ):

        all_known_words = set()

        # ==========================================
        # LOAD ENTITY WORDS
        # ==========================================

        for entity_type in [

            "worker",
            "crop",
            "farm",
            "product",
            "vendor",
            "buyer"

        ]:

            all_known_words.update(

                load_entities(
                    entity_type
                )

            )

        # ==========================================
        # LOAD SYSTEM WORDS
        # ==========================================

        all_known_words.update(
            QUERY_MARKERS
        )

        all_known_words.update(
            DATE_WORDS
        )

        all_known_words.update(
            FUNCTIONAL_LANGUAGE_WORDS
        )

        all_known_words.update(
            KNOWN_UNITS
        )
        all_known_words.update(
            load_operation_keywords()
        )
        # ==========================================
        # UNKNOWN DETECTION
        # ==========================================
       
        unknown_result = process_unknown_input(

            user_input,

            all_known_words

        )
        
        # ==========================================
        # APPLY RESULT
        # ==========================================

        if unknown_result:

            semantic_states[0].update(
                unknown_result
            )

            from core_brain.context_engine import (
                set_pending_learning
            )

            set_pending_learning(

                {

                    "type":
                    "unknown_word",

                    "target_word":

                    unknown_result[
                        "learning_suggestion"
                    ].get(
                        "target_word"
                    ),

                    "suggested_context":

                    unknown_result[
                        "learning_suggestion"
                    ].get(
                        "suggested_context"
                    ),

                    "raw_input":
                    user_input

                }

            )
            return [

                cleanup_semantic_state(

                    semantic_states[0]

                )

            ]
    # ==========================================
    # QUERY PIPELINE
    # ==========================================

    if any(

        state.get("is_query")

        for state in semantic_states

    ):

        processed_states = []

        for state in semantic_states:

            if state.get(
                "is_query"
            ):

                state = execute_query(
                    state
                )

                remember_query_context(
                    state
                )

            processed_states.append(
                cleanup_semantic_state(
                    state
                )
            )

        return processed_states

    # ==========================================
    # ENTRY PIPELINE
    # ==========================================

    if any(

        state.get("is_entry")

        for state in semantic_states

    ):

        processed_states = []

        for state in semantic_states:

            # ==========================================
            # PENDING FIELD
            # ==========================================

            set_pending_if_needed(
                state
            )

            # ==========================================
            # SAVE EVENT
            # ==========================================

            save_if_needed(
                state
            )

            # ==========================================
            # LEARNING
            # ==========================================

            learn_result = learn_from_semantic_state(
                state
            )

            if learn_result:

                state[
                    "learning_suggestion"
                ] = learn_result

            processed_states.append(

                cleanup_semantic_state(
                    state
                )

            )

        return processed_states
    
    # ==========================================
    # FINAL RETURN
    # ==========================================

    return [

        cleanup_semantic_state(

            primary_state

        )

    ]
