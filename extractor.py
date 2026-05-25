import re
from datetime import datetime, timedelta

from semantic_engine import (
    build_semantic_state,
    learn_conversation_pattern,
    detect_operation_type
)

from rule_engine import (
    extract_by_rules
)

from context_engine import (
    resolve_pending_field,
    set_pending_field,
    get_pending_query,
    clear_pending_query,
    set_last_query_context,
    get_last_query_context,
    inherit_context
)

from treatment_engine import (
    apply_treatment_context_rules
)

from event_memory import (
    save_farm_event,
    get_total_payment
)

from learning import (
    is_learning_command,
    is_learning_confirmation,
    process_learning_command,
    resolve_learning_confirmation,
    learn_from_semantic_state
)

from semantic_learning import (
    approve_candidate_rule
)

from query_engine import (
    execute_query
)

from entity_memory import (
    load_entities
)

from vocabulary import (
    CROPS
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


def attach_date_context(semantic_state):

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


def infer_followup_entities(raw_text, previous_entities):

    text = (raw_text or "").lower().strip()

    entities = {}

    if not text:

        return entities

    previous_entities = previous_entities or {}

    if "worker" in previous_entities:

        match = re.search(

            r"\b([a-z][a-z0-9_]*)\s+ko\b",

            text

        )

        if match:

            token = match.group(1)

            if token not in DATE_WORDS + [

                "aur",
                "and",
                "fir"

            ]:

                entities[
                    "worker"
                ] = token

    if "farm" in previous_entities:

        match = re.search(

            r"\b([a-z][a-z0-9_]*)\s*(?:farm)?\s+se\b",

            text

        )

        if match:

            token = match.group(1)

            if token not in DATE_WORDS + [

                "aur",
                "and",
                "fir"

            ]:

                entities[
                    "farm"
                ] = token

    return entities


def apply_followup_query_context(semantic_state):

    last_query = get_last_query_context()

    if not last_query:

        return semantic_state

    query_type = last_query.get(
        "query_type"
    )

    if not query_type:

        return semantic_state

    if (

        semantic_state.get("is_entry")

        or

        semantic_state.get("mode") == "entry"

        or

        semantic_state.get("intent") == "entry"

    ):

        return semantic_state

    normalized = semantic_state.get(
        "normalized_text",
        ""
    )

    has_explicit_query = any(

        marker in normalized

        for marker in QUERY_MARKERS + [

            "nikla",
            "nikle",
            "payment",
            "rupye",
            "diye"

        ]

    )

    if (

        has_explicit_query

        and

        semantic_state.get(
            "is_query"
        )

        and

        not semantic_state.get(
            "needs_clarification"
        )

    ):

        return semantic_state

    raw_text = semantic_state.get(
        "raw_input",
        ""
    )

    normalized_text = semantic_state.get(
        "normalized_text",
        ""
    )

    inferred_entities = infer_followup_entities(

        raw_text,

        last_query.get(
            "entities",
            {}
        )

    )

    if inferred_entities:

        entities = dict(
            semantic_state.get(
                "entities",
                {}
            )
        )

        entities.update(
            inferred_entities
        )

        semantic_state[
            "entities"
        ] = entities

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
            ] = last_query.get(
                "event_date"
            ) or previous_date

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

    semantic_state[
        "query_type"
    ] = query_type

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
        "last query context reused for date follow-up"
    )

    return semantic_state


def remember_query_context(semantic_state):

    if not semantic_state.get(
        "is_query"
    ):

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

    for key, value in extracted_data.items():

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

    parts = re.split(

        r"(?:\n+|[.;]+|\b(?:and|aur)\b)",

        clean_input,

        flags=re.IGNORECASE

    )

    return [

        part.strip()

        for part in parts

        if part and part.strip()

    ]


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

            if state.get(field):

                continue

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

            cleanup_semantic_state(
                state
            )

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

            state.get(
                "mode"
            ) == "entry"

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
def process_unknown_input(user_input, all_known_words):
    words = user_input.lower().split()
    unknown_words = [w for w in words if w not in all_known_words and len(w) > 2]
    
    if unknown_words:
        target_word = unknown_words[0] # Pick the most prominent unknown word
        
        # Ye aapke response_engine.py ke "learning_suggestion" format se match karta hai
        return {
            "status": "pending_learning",
            "learning_suggestion": {
                "message": f"Mujhe '{target_word}' ka matlab nahi pata. Kya yeh koi naya operation (jaise harvest, expense) ya crop hai? (e.g., type 'harvest' to save or 'skip')",
                "target_word": target_word
            }
        }
    return None
# ==========================================
# HANDLE PENDING QUERY
# ==========================================

def handle_pending_query(

    semantic_state

):

    pending_query = get_pending_query()

    if not pending_query:

        return None

    entities = semantic_state.get(
        "entities",
        {}
    )

    worker = entities.get(
        "worker"
    )

    if not worker:

        workers = load_entities(
            "worker"
        )

        normalized = semantic_state.get(
            "normalized_text",
            ""
        )

        for item in workers:

            if item.lower() == normalized:

                worker = item
                break

    if not worker:

        return None

    total = get_total_payment(
        worker
    )

    clear_pending_query()

    semantic_state[
        "query_result"
    ] = {

        "query_type":
        "total_payment",

        "worker":
        worker,

        "total_payment":
        total,

        "currency":
        "Rs",

        "formatted":
        f"{total} Rs"

    }

    semantic_state[
        "is_query"
    ] = True

    return cleanup_semantic_state(

        semantic_state

    )

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
    # EMPTY
    # ==========================================

    if not user_input:

        return None

    user_input = strip_chat_prompt_prefix(
        user_input.strip()
    )

    if not user_input:

        return None

    if is_learning_confirmation(
        user_input
    ):

        confirmation_result = resolve_learning_confirmation(
            user_input
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

    semantic_states = []

    previous_state = None

    for part in parts:

        operation_type = (
            detect_operation_type(part)
        )

        state = build_semantic_state(
            part
        )

        state["operation"] = (
            operation_type
        )

        state = attach_date_context(

            state

        )

        state = apply_followup_query_context(

            state

        )

        state = inherit_context(

            previous_state,

            state

        )

        semantic_states.append(

            state

        )

        previous_state = state

    semantic_state = semantic_states[0]
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

        phrase = user_input.lower().replace(
            "approve rule ",
            ""
        ).strip()

        approved = approve_candidate_rule(
            phrase
        )

        semantic_state[
            "query_result"
        ] = {

            "query_type":
            "rule_approval",

            "approved":
            approved,

            "phrase":
            phrase

        }

        semantic_state[
            "is_query"
        ] = True

        return [

            cleanup_semantic_state(

            semantic_state

            )

        ]

    semantic_states = [

        process_semantic_state(
            state
        )

        for state in semantic_states

    ]

    semantic_states = backfill_common_fields(
        semantic_states
    )

    if any(state.get("is_query") for state in semantic_states):

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

    if any(state.get("is_entry") for state in semantic_states):

        processed_states = []

        for state in semantic_states:

            set_pending_if_needed(
                state
            )

            save_if_needed(
                state
            )

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
    # PENDING QUERY
    # ==========================================

    pending_query_result = (

        handle_pending_query(
            semantic_state
        )

    )

    if pending_query_result:

        return [

            cleanup_semantic_state(

            pending_query_result

            )

        ]

    # ==========================================
    # QUERY ENGINE
    # ==========================================

    if semantic_state.get(
        "is_query"
    ):

        processed_states = []

        for semantic_state in semantic_states:

            semantic_state = execute_query(

                semantic_state

            )

            remember_query_context(
                semantic_state
            )

            learn_result = learn_from_semantic_state(

                semantic_state

            )

            if learn_result:

                semantic_state[
                    "learning_suggestion"
                ] = learn_result

            processed_states.append(

                cleanup_semantic_state(

                    semantic_state

                )

            )

        return processed_states

    # ==========================================
    # LEARNING
    # ==========================================

    learn_result = learn_from_semantic_state(

        semantic_state

    )

    if learn_result:

        semantic_state[
            "learning_suggestion"
        ] = learn_result

    # ==========================================
    # FINAL RETURN
    # ==========================================

    return [

        cleanup_semantic_state(

        semantic_state

        )

    ]
