import re

from memory_system.event_memory import (

    get_connection,

    get_total_payment,
    get_total_expense,

    get_payment_history,

    get_events_by_crop,

    get_last_treatment,

    get_product_history,

    get_harvest_quantity

)


def infer_worker_before_ko(text):

    match = re.search(
        r"(?:^|\b)([a-z][a-z0-9_ ]{1,40}?)\s+ko\b",
        text or "",
    )

    if not match:

        return None

    blocked = {
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

    tokens = [
        token
        for token in match.group(1).strip().split()
        if token not in blocked
    ]

    if not tokens:

        return None

    return tokens[-1]

# ==========================================
# EXECUTE QUERY
# ==========================================

def execute_query(

    semantic_state

):
    # ==========================================
    # SAFE LOCAL DEFAULTS
    # ==========================================

    product = None

    worker = None

    crop = None

    farm = None

    buyer = None
    # ==========================================
    # INITIALIZE SHARED COGNITION
    # ==========================================

    semantic_state.setdefault(

        "inference",

        []

    )

    semantic_state.setdefault(

        "confidence_updates",

        {}

    )

    semantic_state.setdefault(

        "memory_updates",

        []

    )

    semantic_state.setdefault(

        "reasoning_chain",

        []

    )

    # ==========================================
    # QUERY TYPE
    # ==========================================

    query_type = semantic_state.get(
        "query_type"
    )

    normalized_text = (
        semantic_state.get(
            "normalized_text"
        )
        or
        semantic_state.get(
            "raw_input"
        )
        or
        ""
    ).lower()

    if (
        any(
            marker in normalized_text
            for marker in [
                "rupye",
                "rupaye",
                "rupyee",
                "payment",
                "diye",
                "diya",
            ]
        )
        and
        any(
            marker in normalized_text
            for marker in [
                "kitna",
                "kitne",
                "total",
            ]
        )
    ):

        query_type = "total_payment"

        semantic_state[
            "query_type"
        ] = query_type

    # ==========================================
    # QUERY REASONING
    # ==========================================

    semantic_state[
        "reasoning_chain"
    ].append(

        f"query detected: {query_type}"

    )
    
    # ==========================================
    # ENTITIES
    # ==========================================

    entities = semantic_state.get(
        "entities",
        {}
    )

    crop = entities.get(
        "crop"
    )

    worker = entities.get(
        "worker"
    )

    if (
        not worker
        and
        query_type == "total_payment"
    ):

        worker = infer_worker_before_ko(
            normalized_text
        )

        if worker:

            entities[
                "worker"
            ] = worker

            semantic_state[
                "worker"
            ] = worker

    product = entities.get(
        "product"
    )

    farm = entities.get(
        "farm"
    )

    if (
        query_type == "total_expense"
        and not product
    ):

       for expense_term in [

            "diesel",
            "fuel",
            "petrol",

            "repair",
            "service",

        ]:

            if expense_term in normalized_text:

                product = expense_term
                entities["product"] = product
                semantic_state["product"] = product
                break

    date_filter = semantic_state.get(
        "date_filter"
    )

    # ==========================================
    # ENTITY REASONING
    # ==========================================

    if crop:

        semantic_state[
            "reasoning_chain"
        ].append(

            f"crop matched: {crop}"

        )

    if worker:

        semantic_state[
            "reasoning_chain"
        ].append(

            f"worker matched: {worker}"

        )

    if product:

        semantic_state[
            "reasoning_chain"
        ].append(

            f"product matched: {product}"

        )

    if farm:

        semantic_state[
            "reasoning_chain"
        ].append(

            f"farm matched: {farm}"

        )

    # ==========================================
    # QUERY REQUIRED FIELDS
    # ==========================================

    required_fields = {

        "total_payment": [],

        "total_expense": [],

        "payment_history": [],

        "crop_history": [
            "crop"
        ],

        "last_treatment": [
            "crop"
        ],

        "product_history": [
            "product"
        ],

        "harvest_quantity": [
            "crop"
        ]

    }

    entity_values = {

        "worker": worker,
        "crop": crop,
        "product": product,
        "farm": farm

    }

    missing_fields = [

        field

        for field in required_fields.get(
            query_type,
            []
        )

        if not entity_values.get(
            field
        )

    ]

    if missing_fields:

        semantic_state[
            "missing_fields"
        ] = missing_fields

        semantic_state[
            "needs_clarification"
        ] = True

        semantic_state[
            "query_result"
        ] = {

            "query_type":
            query_type,

            "message":
            f"{missing_fields[0].title()} not found."

        }

        return semantic_state

    semantic_state[
        "missing_fields"
    ] = []

    semantic_state[
        "needs_clarification"
    ] = False

    # ==========================================
    # CONFIDENCE UPDATE
    # ==========================================

    semantic_state[
        "confidence_updates"
    ][
        "query_engine_confidence"
    ] = 0.91

    # ==========================================
    # INFERENCE
    # ==========================================

    semantic_state[
        "inference"
    ].append(

        "query execution pipeline started"

    )

    # ==========================================
    # TOTAL PAYMENT
    # ==========================================

    if query_type == "total_payment":

        result = execute_total_payment_query(

            worker,

            date_filter

        )
        semantic_state[
        "inference"
        ].append(

            "total payment query executed"

        )

        semantic_state[
            "memory_updates"
        ].append(

            "worker payment history accessed"

        )
    # ==========================================
    # PAYMENT HISTORY
    # ==========================================

    elif query_type == "payment_history":

        result = execute_payment_history_query(

            worker

        )

    # ==========================================
    # TOTAL EXPENSE QUERY
    # ==========================================

    elif query_type == "total_expense":

        total = get_total_expense(

            product=product,

            event_date=date_filter

        )

        result = {

            "query_type":
            "total_expense",

            "total_expense":
            total,

            "currency":
            "Rs",

            "date_filter":
            date_filter,

            "formatted":
            f"{total} Rs"

        }

    # ==========================================
    # CROP HISTORY
    # ==========================================

    elif query_type == "crop_history":

        result = execute_crop_history_query(

            crop

        )

    # ==========================================
    # LAST TREATMENT
    # ==========================================

    elif query_type == "last_treatment":

        result = execute_last_treatment_query(

            crop

        )

    # ==========================================
    # PRODUCT HISTORY
    # ==========================================

    elif query_type == "product_history":

        result = execute_product_history_query(

            product

        )

    # ==========================================
    # HARVEST QUANTITY
    # ==========================================

    elif query_type == "harvest_quantity":

        total = get_harvest_quantity(

            crop,

            farm,

            date_filter

        )

        result = {

            "query_type":
            "harvest_quantity",

            "farm":
            farm,

            "crop":
            crop,

            "total_harvest":
            total,

            "unit":
            "kg",

            "date_filter":
            date_filter,

            "formatted":
            f"{total} kg"

        }

        semantic_state.setdefault(

            "inference",

            []

        ).append(

            "harvest aggregation executed"

        )

        semantic_state.setdefault(

            "reasoning_chain",

            []

        ).append(

            "harvest quantity summed from farm_events"

        )

    # ==========================================
    # UNKNOWN QUERY
    # ==========================================

    else:

        result = {

            "query_type":
            "unsupported_query",

            "message":
            (
                "Query understood "
                "but no handler found."
            )

        }

    # ==========================================
    # WRITEBACK TO SEMANTIC STATE
    # ==========================================

    semantic_state[
        "query_result"
    ] = result

    # ==========================================
    # QUERY COMPLETED
    # ==========================================

    semantic_state[
        "context_status"
    ] = "completed"

    semantic_state.setdefault(

        "inference",

        []

    ).append(

        "query result generated"

    )

    semantic_state.setdefault(

        "reasoning_chain",

        []

    ).append(

        f"{query_type} query completed"

    )

    return semantic_state

# ==========================================
# TOTAL PAYMENT
# ==========================================

def execute_total_payment_query(

    worker,

    event_date=None

):

    total = get_total_payment(
        worker,

        event_date
    )

    result = {

        "query_type":
        "total_payment",

        "total_payment":
        total,

        "currency":
        "Rs",

        "date_filter":
        event_date,

        "formatted":
        f"{total} Rs"

    }

    if worker:

        result[
            "worker"
        ] = worker

    else:

        result[
            "scope"
        ] = "all_workers"

    return result

# ==========================================
# PAYMENT HISTORY
# ==========================================

def execute_payment_history_query(

    worker

):

    history = get_payment_history(
        worker
    )

    result = {

        "query_type":
        "payment_history",

        "history":
        history

    }

    if worker:

        result[
            "worker"
        ] = worker

    else:

        result[
            "scope"
        ] = "all_workers"

    return result

# ==========================================
# CROP HISTORY
# ==========================================

def execute_crop_history_query(

    crop

):

    if not crop:

        return {

            "query_type":
            "crop_history",

            "message":
            "Crop not found."

        }

    history = get_events_by_crop(
        crop
    )

    return {

        "query_type":
        "crop_history",

        "crop":
        crop,

        "history":
        history

    }

# ==========================================
# LAST TREATMENT
# ==========================================

def execute_last_treatment_query(

    crop

):

    if not crop:

        return {

            "query_type":
            "last_treatment",

            "message":
            "Crop not found."

        }

    treatment = get_last_treatment(
        crop
    )

    return {

        "query_type":
        "last_treatment",

        "crop":
        crop,

        "treatment":
        treatment

    }

# ==========================================
# PRODUCT HISTORY
# ==========================================

def execute_product_history_query(

    product

):

    if not product:

        return {

            "query_type":
            "product_history",

            "message":
            "Product not found."

        }

    history = get_product_history(
        product
    )

    return {

        "query_type":
        "product_history",

        "product":
        product,

        "history":
        history

    }

# ==========================================
# HARVEST QUERY
# ==========================================

def execute_harvest_query(

    crop,

    farm

):

    if not crop:

        return {

            "query_type":
            "harvest_quantity",

            "message":
            "Crop not found."

        }

    quantity = get_harvest_quantity(

        crop,

        farm

    )

    return {

        "query_type":
        "harvest_quantity",

        "crop":
        crop,

        "farm":
        farm,

        "quantity":
        quantity

    }
