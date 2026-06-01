from memory_system.entity_memory import (
    load_entities
)

# ==========================================
# APPLY TREATMENT CONTEXT RULES
# ==========================================

def apply_treatment_context_rules(

    semantic_data,

    user_input

):

    # ==========================================
    # NOT TREATMENT
    # ==========================================

    if (

        semantic_data.get("intent")

        !=

        "treatment"

    ):

        return semantic_data

    # ==========================================
    # NORMALIZE TEXT
    # ==========================================

    text = user_input.lower()

    # ==========================================
    # SPLIT:
    # X me Y treatment kiya
    # ==========================================

    if " me " not in text:

        return semantic_data

    parts = text.split(
        " me ",
        1
    )

    left_part = parts[0]

    right_part = parts[1]

    # ==========================================
    # LOAD ENTITIES
    # ==========================================

    crops = load_entities(
        "crop"
    )

    products = load_entities(
        "product"
    )

    # ==========================================
    # FORCE CROP
    # ==========================================

    for crop in crops:

        if crop in left_part:

            semantic_data["crop"] = crop

            break

    # ==========================================
    # FORCE PRODUCT
    # ==========================================

    for product in products:

        if product in right_part:

            semantic_data["product"] = product

            break

    # ==========================================
    # REMOVE WRONG CLARIFICATION
    # ==========================================

    missing_fields = []

    if not semantic_data.get(
        "crop"
    ):

        missing_fields.append(
            "crop"
        )

    if not semantic_data.get(
        "product"
    ):

        missing_fields.append(
            "product"
        )

    semantic_data[
        "missing_fields"
    ] = missing_fields

    # ==========================================
    # FINAL STATUS
    # ==========================================

    if missing_fields:

        semantic_data[
            "needs_clarification"
        ] = True

        semantic_data[
            "clarification_type"
        ] = "missing_field"

        semantic_data[
            "context_status"
        ] = "pending_info"

    else:

        semantic_data[
            "needs_clarification"
        ] = False

        semantic_data[
            "clarification_type"
        ] = None

        semantic_data[
            "context_status"
        ] = "completed"

    # ==========================================
    # OPERATION SNAPSHOT
    # ==========================================

    semantic_data[
        "operation_snapshot"
    ] = {

        "operation_id":

        semantic_data.get(
            "operation_id"
        ),

        "intent":

        semantic_data.get(
            "intent"
        ),

        "crop":

        semantic_data.get(
            "crop"
        ),

        "product":

        semantic_data.get(
            "product"
        ),

        "status":

        semantic_data.get(
            "context_status"
        )

    }

    # ==========================================
    # OPERATION HISTORY
    # ==========================================

    semantic_data[
        "operation_history"
    ] = [

        {

            "operation_id":

            semantic_data.get(
                "operation_id"
            ),

            "intent":

            semantic_data.get(
                "intent"
            ),

            "crop":

            semantic_data.get(
                "crop"
            ),

            "product":

            semantic_data.get(
                "product"
            ),

            "status":

            semantic_data.get(
                "context_status"
            )

        }

    ]

    return semantic_data
