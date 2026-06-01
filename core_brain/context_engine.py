# ==========================================
# GLOBAL CONTEXT MEMORY
# ==========================================

import json
import os
import re
from config import (

    QUERY_MARKERS,
    DATE_WORDS,

    PAYMENT_QUERY_MARKERS,
    HARVEST_QUERY_MARKERS

)
# ==========================================
# GLOBAL MEMORY STATE
# ==========================================

GLOBAL_CONTEXT = {

    "pending_field":
    None,

    "pending_operation_data":
    None,

    "pending_query":
    None,

    "last_query_context":
    None,

    "pending_learning":
    None

}

# ==========================================
# FILES
# ==========================================

PENDING_LEARNING_FILE = (
    "config_memory/pending_learning.json"
)

# ==========================================
# FOLLOWUP QUERY WORDS
# ==========================================

FOLLOWUP_QUERY_WORDS = {

    "aur",
    "phir",
    "fir",

    "ab",
    "toh",
    "to"

}

# ==========================================
# LAST QUERY CONTEXT
# ==========================================

def set_last_query_context(query_data):

    if not query_data:

        return

    GLOBAL_CONTEXT[
        "last_query_context"
    ] = {

        "query_type":
        query_data.get(
            "query_type"
        ),

        "intent":
        query_data.get(
            "intent"
        ),

        "mode":
        query_data.get(
            "mode"
        ),

        "operation":
        query_data.get(
            "operation"
        ),

        "date_filter":
        query_data.get(
            "date_filter"
        ),

        "event_date":
        query_data.get(
            "event_date"
        ),

        "entities":

        dict(

            query_data.get(
                "entities",
                {}
            )

        )

    }

# ==========================================
# GET LAST QUERY CONTEXT
# ==========================================

def get_last_query_context():

    return GLOBAL_CONTEXT.get(
        "last_query_context"
    )

# ==========================================
# SET PENDING QUERY
# ==========================================

def set_pending_query(query_data):

    GLOBAL_CONTEXT[
        "pending_query"
    ] = query_data

# ==========================================
# GET PENDING QUERY
# ==========================================

def get_pending_query():

    return GLOBAL_CONTEXT.get(
        "pending_query"
    )

# ==========================================
# CLEAR PENDING QUERY
# ==========================================

def clear_pending_query():

    GLOBAL_CONTEXT[
        "pending_query"
    ] = None

# ==========================================
# SET PENDING LEARNING
# ==========================================

def set_pending_learning(learning_data):

    GLOBAL_CONTEXT[
        "pending_learning"
    ] = learning_data

    os.makedirs(

        os.path.dirname(
            PENDING_LEARNING_FILE
        ),

        exist_ok=True

    )

    with open(

        PENDING_LEARNING_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            learning_data,

            f,

            indent=2,

            ensure_ascii=False

        )

# ==========================================
# GET PENDING LEARNING
# ==========================================

def get_pending_learning():

    pending_learning = GLOBAL_CONTEXT.get(
        "pending_learning"
    )

    if pending_learning is not None:

        return pending_learning

    if not os.path.exists(
        PENDING_LEARNING_FILE
    ):

        return None

    try:

        with open(

            PENDING_LEARNING_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            GLOBAL_CONTEXT[
                "pending_learning"
            ] = json.load(f)

            return GLOBAL_CONTEXT[
                "pending_learning"
            ]

    except Exception:

        return None

# ==========================================
# CLEAR PENDING LEARNING
# ==========================================

def clear_pending_learning():

    GLOBAL_CONTEXT[
        "pending_learning"
    ] = None

    if os.path.exists(
        PENDING_LEARNING_FILE
    ):

        try:

            os.remove(
                PENDING_LEARNING_FILE
            )

        except Exception:

            pass

# ==========================================
# SET PENDING FIELD
# ==========================================

def set_pending_field(

    field_name,

    operation_data

):

    GLOBAL_CONTEXT[
        "pending_field"
    ] = field_name

    GLOBAL_CONTEXT[
        "pending_operation_data"
    ] = operation_data

# ==========================================
# GET PENDING FIELD
# ==========================================

def get_pending_field():

    return GLOBAL_CONTEXT.get(
        "pending_field"
    )

# ==========================================
# CLEAR PENDING FIELD
# ==========================================

def clear_pending_field():

    GLOBAL_CONTEXT[
        "pending_field"
    ] = None

    GLOBAL_CONTEXT[
        "pending_operation_data"
    ] = None

# ==========================================
# RESOLVE PENDING FIELD
# ==========================================

def resolve_pending_field(user_input):

    pending_field = GLOBAL_CONTEXT.get(
        "pending_field"
    )

    pending_operation_data = GLOBAL_CONTEXT.get(
        "pending_operation_data"
    )

    # ==========================================
    # NO PENDING
    # ==========================================

    if not pending_field:

        return None

    raw_value = user_input.strip()

    value = raw_value.lower()

    # ==========================================
    # AUTO NUMBER PARSING
    # ==========================================

    try:

        numeric = float(

            raw_value.replace(
                ",",
                ""
            )

        )

        if numeric.is_integer():

            value = int(numeric)

        else:

            value = numeric

    except Exception:

        pass

    # ==========================================
    # EXIT PENDING FOR QUERY MODE
    # ==========================================

    query_words = [

        "total",
        "history",

        "kitna",
        "kitne",
        "kitana",

        "summary",

        "kab",

        "batao",
        "dikhao",

        "nikla",
        "nikle",

        "harvest",
        "tudai",
        "todai",

        "kya"

    ]

    lower_text = user_input.lower()

    is_query = (

        any(

            word in lower_text

            for word in query_words

        )

        or

        any(

            word in lower_text

            for word in FOLLOWUP_QUERY_WORDS

        )

    )

    if is_query:

        clear_pending_field()

        return None

    # ==========================================
    # UPDATE FIELD
    # ==========================================

    pending_operation_data[
        pending_field
    ] = value

    # ==========================================
    # ENTITY SYNC
    # ==========================================

    if pending_field in [

        "farm",
        "crop",
        "worker",
        "product",
        "vendor",
        "buyer"

    ]:

        entities = pending_operation_data.setdefault(

            "entities",

            {}

        )

        entities[
            pending_field
        ] = value

    # ==========================================
    # AUTO LEARN ENTITY
    # ==========================================

    if pending_field in [

        "worker",
        "vendor",
        "buyer",
        "crop",
        "product"

    ]:

        from memory_system.entity_memory import (
            save_entity
        )

        save_entity(

            value,

            pending_field

        )

    # ==========================================
    # REMOVE FIELD FROM MISSING
    # ==========================================

    missing_fields = pending_operation_data.get(
        "missing_fields",
        []
    )

    if pending_field in missing_fields:

        missing_fields.remove(
            pending_field
        )

    # ==========================================
    # STATUS UPDATE
    # ==========================================

    if not missing_fields:

        pending_operation_data[
            "needs_clarification"
        ] = False

        pending_operation_data[
            "clarification_type"
        ] = None

        pending_operation_data[
            "context_status"
        ] = "completed"

    # ==========================================
    # UPDATE SNAPSHOT
    # ==========================================

    if pending_operation_data.get(
        "operation_snapshot"
    ):

        pending_operation_data[
            "operation_snapshot"
        ][
            pending_field
        ] = value

    # ==========================================
    # UPDATE HISTORY
    # ==========================================

    if pending_operation_data.get(
        "operation_history"
    ):

        for item in pending_operation_data[
            "operation_history"
        ]:

            item[
                pending_field
            ] = value

    # ==========================================
    # FINAL DATA
    # ==========================================

    final_data = pending_operation_data

    # ==========================================
    # CLEAR MEMORY
    # ==========================================

    clear_pending_field()

    return final_data

# ==========================================
# INHERIT CONTEXT
# ==========================================

def inherit_context(

    previous_state,

    current_state

):

    # ==========================================
    # NOTHING TO INHERIT
    # ==========================================

    if not previous_state:

        return current_state

    previous_entities = previous_state.get(

        "entities",

        {}

    )

    inheritance_applied = False

    # ==========================================
    # INHERITABLE FIELDS
    # ==========================================

    INHERITABLE_FIELDS = [

        "farm",
        "crop",
        "worker",
        "product",

        "vendor",
        "buyer"

    ]

    for field in INHERITABLE_FIELDS:

        previous_value = (

            previous_state.get(field)

            or

            previous_entities.get(field)

        )

        if (

            not current_state.get(field)

            and

            previous_value

        ):

            current_state[field] = (
                previous_value
            )

            current_state.setdefault(

                "entities",

                {}

            )

            current_state[
                "entities"
            ][field] = previous_value

            inheritance_applied = True

    # ==========================================
    # INHERIT QUERY TYPE
    # ==========================================

    if (

        not current_state.get(
            "query_type"
        )

        and

        previous_state.get(
            "query_type"
        )

    ):

        current_state[
            "query_type"
        ] = previous_state[
            "query_type"
        ]

        inheritance_applied = True

    # ==========================================
    # OPERATION SAFETY
    # ==========================================

    current_operation = current_state.get(
        "operation"
    )

    previous_operation = previous_state.get(
        "operation"
    )

    # ==========================================
    # INHERIT OPERATION
    # ==========================================

    if (

        current_operation is None

        and

        previous_operation

    ):

        current_state[
            "operation"
        ] = previous_operation

        inheritance_applied = True

    # ==========================================
    # STOP CROSS OPERATION LEAK
    # ==========================================

    elif (

        current_operation

        and

        previous_operation

        and

        current_operation != previous_operation

    ):

        return current_state

    # ==========================================
    # TRACE
    # ==========================================

    if inheritance_applied:

        current_state.setdefault(

            "reasoning_chain",

            []

        ).append(

            "context inherited from previous query"

        )

    return current_state
# ==========================================
# INFER FOLLOWUP ENTITIES
# ==========================================

def infer_followup_entities(

    raw_text,

    previous_entities

):

    from memory_system.entity_memory import (
        load_entities
    )

    normalized = (

        raw_text
        .lower()
        .strip()

    )

    inferred = {}

    # ==========================================
    # ENTITY TYPES
    # ==========================================

    entity_types = [

        "worker",
        "crop",
        "farm",
        "product",

        "vendor",
        "buyer"

    ]

    # ==========================================
    # DETECT ENTITIES
    # ==========================================

    for entity_type in entity_types:

        known_entities = load_entities(
            entity_type
        )

        for entity in known_entities:

            entity_lower = entity.lower()

            if entity_lower in normalized:

                inferred[
                    entity_type
                ] = entity

                break

    # ==========================================
    # FALLBACK TO PREVIOUS ENTITIES
    # ==========================================

    for key, value in previous_entities.items():

        if key not in inferred:

            inferred[key] = value

    return inferred

# ==========================================
# APPLY FOLLOWUP QUERY CONTEXT
# ==========================================

def apply_followup_query_context(

    semantic_state

):

    last_query = get_last_query_context()

    # ==========================================
    # NO CONTEXT
    # ==========================================

    if not last_query:

        return semantic_state

    # ==========================================
    # ENTRY SAFETY
    # ==========================================

    if (

        semantic_state.get("is_entry")

        or

        semantic_state.get("mode") == "entry"

        or

        semantic_state.get("intent") == "entry"

    ):

        return semantic_state

    normalized_text = (

        semantic_state.get(
            "normalized_text",
            ""
        )

        .lower()
        .strip()

    )

    # ==========================================
    # IGNORE EMPTY CONNECTORS
    # ==========================================

    if normalized_text in [

        "aur",
        "and",

        "fir",
        "phir"

    ]:

        return semantic_state

    # ==========================================
    # STOP EMPTY FOLLOWUPS
    # ==========================================

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

    # ==========================================
    # EXPLICIT QUERY DETECTION
    # ==========================================

    explicit_query_markers = (

        QUERY_MARKERS

        +

        PAYMENT_QUERY_MARKERS

        +

        HARVEST_QUERY_MARKERS

    )
    has_explicit_query = any(

        marker in normalized_text

        for marker in explicit_query_markers

    )

    # ==========================================
    # ALREADY COMPLETE QUERY
    # ==========================================

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

    # ==========================================
    # FOLLOWUP ENTITY INFERENCE
    # ==========================================

    inferred_entities = infer_followup_entities(

        semantic_state.get(
            "raw_input",
            ""
        ),

        last_query.get(
            "entities",
            {}
        )

    )

    inheritance_applied = False

    # ==========================================
    # APPLY ENTITIES
    # ==========================================

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

        for key, value in inferred_entities.items():

            semantic_state[
                key
            ] = value

        inheritance_applied = True

    # ==========================================
    # INHERIT QUERY TYPE
    # ==========================================

    if not semantic_state.get(
        "query_type"
    ):

        semantic_state[
            "query_type"
        ] = last_query.get(
            "query_type"
        )

        inheritance_applied = True

    # ==========================================
    # INHERIT OPERATION
    # ==========================================

    if not semantic_state.get(
        "operation"
    ):

        semantic_state[
            "operation"
        ] = last_query.get(
            "operation"
        )

        inheritance_applied = True

    # ==========================================
    # QUERY MODE
    # ==========================================

    semantic_state[
        "is_query"
    ] = True

    semantic_state[
        "mode"
    ] = "query"

    semantic_state[
        "intent"
    ] = "query"

    # ==========================================
    # REASONING TRACE
    # ==========================================

    if inheritance_applied:

        reasoning_trace = semantic_state.setdefault(

            "reasoning_trace",

            []

        )

        trace_message = (

            "context inherited from previous query"

        )

        if trace_message not in reasoning_trace:

            reasoning_trace.append(
                trace_message
            )

    return semantic_state
# ==========================================
# ADD REASONING TRACE
# ==========================================

def add_reasoning_trace(

    semantic_state,

    message

):

    traces = semantic_state.setdefault(

        "reasoning_trace",

        []

    )

    if message not in traces:

        traces.append(
            message
        )
# ==========================================
# CONFIRM PENDING LEARNING
# ==========================================

def confirm_pending_learning(

    approved

):

    pending_learning = get_pending_learning()

    if not pending_learning:

        return None

    result = {

        "raw_input":
        "confirmation",

        "is_query":
        False,

        "is_entry":
        False,

        "learning_confirmation": {

            "status":

            "confirmed"

            if approved

            else

            "rejected",

            "pending_learning":
            pending_learning

        },

        "missing_fields":
        []

    }

    # ==========================================
    # APPROVED
    # ==========================================

    if approved:

        pending_learning[
            "confirmed"
        ] = True

        result[
            "learning_confirmation"
        ][
            "commit_result"
        ] = {

            "status":
            "learned_pattern",

            "intent":
            pending_learning.get(
                "intent"
            ),

            "pattern":
            pending_learning.get(
                "pattern"
            ),

            "phrase":
            pending_learning.get(
                "phrase"
            )

        }

    # ==========================================
    # CLEAR PENDING
    # ==========================================

    clear_pending_learning()

    return result
# ==========================================
# LAST QUERY MEMORY
# ==========================================

LAST_QUERY_CONTEXT = None

# ==========================================
# SET LAST QUERY CONTEXT
# ==========================================

def set_last_query_context(

    semantic_state

):

    global LAST_QUERY_CONTEXT

    if not semantic_state:

        return

    if not semantic_state.get(
        "is_query"
    ):

        return

    LAST_QUERY_CONTEXT = {

        "query_type":
        semantic_state.get(
            "query_type"
        ),

        "operation":
        semantic_state.get(
            "operation"
        ),

        "entities":

        dict(

            semantic_state.get(
                "entities",
                {}
            )

        ),

        "date_filter":
        semantic_state.get(
            "date_filter"
        ),

        "event_date":
        semantic_state.get(
            "event_date"
        )

    }

# ==========================================
# GET LAST QUERY CONTEXT
# ==========================================

def get_last_query_context():

    global LAST_QUERY_CONTEXT

    return LAST_QUERY_CONTEXT