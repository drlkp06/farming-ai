# ==========================================
# GLOBAL CONTEXT MEMORY
# ==========================================

import json
import os

pending_field = None

pending_operation_data = None

pending_query = None

last_query_context = None

pending_learning = None

PENDING_LEARNING_FILE = "memory/pending_learning.json"

# ==========================================
# LAST QUERY CONTEXT
# ==========================================

def set_last_query_context(query_data):

    global last_query_context

    if not query_data:

        return

    last_query_context = {

        "query_type":
        query_data.get("query_type"),

        "intent":
        query_data.get("intent"),

        "mode":
        query_data.get("mode"),

        "operation":
        query_data.get("operation"),

        "date_filter":
        query_data.get("date_filter"),

        "event_date":
        query_data.get("event_date"),

        "entities":
        dict(query_data.get("entities", {})),

    }


def get_last_query_context():

    global last_query_context

    return last_query_context

# ==========================================
# SET PENDING QUERY
# ==========================================

def set_pending_query(query_data):

    global pending_query

    pending_query = query_data


# ==========================================
# GET PENDING QUERY
# ==========================================

def get_pending_query():

    global pending_query

    return pending_query


# ==========================================
# CLEAR PENDING QUERY
# ==========================================

def clear_pending_query():

    global pending_query

    pending_query = None

# ==========================================
# SET PENDING LEARNING
# ==========================================

def set_pending_learning(learning_data):

    global pending_learning

    pending_learning = learning_data

    os.makedirs(
        "memory",
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

    global pending_learning

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

            pending_learning = json.load(f)

            return pending_learning

    except Exception:

        return None

# ==========================================
# CLEAR PENDING LEARNING
# ==========================================

def clear_pending_learning():

    global pending_learning

    pending_learning = None

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

    global pending_field

    global pending_operation_data

    pending_field = field_name

    pending_operation_data = operation_data

# ==========================================
# GET PENDING FIELD
# ==========================================

def get_pending_field():

    global pending_field

    return pending_field

# ==========================================
# CLEAR PENDING FIELD
# ==========================================

def clear_pending_field():

    global pending_field

    global pending_operation_data

    pending_field = None

    pending_operation_data = None

# ==========================================
# RESOLVE PENDING FIELD
# ==========================================

def resolve_pending_field(user_input):

    global pending_field

    global pending_operation_data

    # ==========================================
    # NO PENDING
    # ==========================================

    if not pending_field:

        return None

    raw_value = user_input.strip()

    value = raw_value.lower()

# ==========================================
# AUTO NUMBER
# ==========================================

    if raw_value.isdigit():

        value = int(raw_value)
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

    is_query = any(

        word in lower_text

        for word in query_words

    )

    if is_query:

        pending_field = None

        pending_operation_data = None

        return None

    # ==========================================
    # UPDATE FIELD
    # ==========================================

    pending_operation_data[

        pending_field

    ] = value

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
    # PRESERVE ORIGINAL RAW TEXT
    # ==========================================

    original_raw_text = pending_operation_data.get(
        "raw_text"
    )

    if original_raw_text:

        pending_operation_data["raw_text"] = (
            original_raw_text
        )

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

        from entity_memory import (
            save_entity
        )

        save_entity(

            value,

            pending_field

        )

    # ==========================================
    # REMOVE FIELD FROM MISSING
    # ==========================================

    if (

        pending_field

        in

        pending_operation_data[
            "missing_fields"
        ]

    ):

        pending_operation_data[
            "missing_fields"
        ].remove(

            pending_field

        )

    # ==========================================
    # STATUS UPDATE
    # ==========================================

    if not pending_operation_data[
        "missing_fields"
    ]:

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

            item[pending_field] = value

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

    # ==========================================
    # FARM INHERITANCE
    # ==========================================

    previous_entities = previous_state.get(
        "entities",
        {}
    )

    previous_farm = (

        previous_state.get(
            "farm"
        )

        or

        previous_entities.get(
            "farm"
        )

    )

    if isinstance(

        previous_farm,

        list

    ):

        previous_farm = previous_farm[0]

    if (

        not current_state.get("farm")

        and

        previous_farm

    ):

        current_state["farm"] = (
            previous_farm
        )

        current_state.setdefault(
            "entities",
            {}
        )

        current_state["entities"]["farm"] = (
            previous_farm
        )
        # ==========================================
        # SYNC ENTITIES
        # ==========================================

        current_state.setdefault(

            "entities",

            {}

        )["farm"] = previous_farm

    # ==========================================
    # INHERIT CROP
    # ==========================================

    current_entities = current_state.get(

        "entities",

        {}

    )

    if (

        current_state.get("crop") is None

        and

        "crop" not in current_entities

        and

        (
            previous_state.get("crop")

            or

            previous_entities.get("crop")
        )

    ):

        previous_crop = (

            previous_state.get("crop")

            or

            previous_entities.get("crop")

        )

        current_state["crop"] = (

            previous_crop

        )

        current_state.setdefault(

            "entities",

            {}

        )["crop"] = previous_crop

    # ==========================================
    # INHERIT WORKER
    # ==========================================

    if (

        not current_state.get("worker")

        and

        (
            previous_state.get("worker")

            or

            previous_entities.get("worker")
        )

    ):

        previous_worker = (

            previous_state.get("worker")

            or

            previous_entities.get("worker")

        )

        current_state["worker"] = (

            previous_worker

        )

        current_state.setdefault(

            "entities",

            {}

        )["worker"] = previous_worker

    # ==========================================
    # INHERIT QUERY TYPE
    # ==========================================

    if (

        not current_state.get("query_type")

        and

        previous_state.get("query_type")

    ):

        current_state["query_type"] = (

            previous_state["query_type"]

        )

# ==========================================
# INHERIT OPERATION
# ==========================================

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
    # INHERIT ONLY IF CURRENT EMPTY
    # ==========================================

    if (

        current_operation is None

        and

        previous_operation

    ):

        current_state["operation"] = (
            previous_operation
        )

    # ==========================================
    # STOP CROSS-OPERATION INHERITANCE
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

    current_state.setdefault(

        "reasoning_chain",

        []

    ).append(

        "context inherited from previous state"

    )

    return current_state
