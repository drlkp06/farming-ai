# ==========================================
# reasoning_engine.py
# ==========================================

from advanced_ai.recommendation_engine import (

    smart_treatment_advisor,

    check_product_repetition

)

from advanced_ai.analytics_engine import (

    get_crop_treatment_count,

    get_worker_total

)

from memory_system.memory_graph_engine import (

    get_related_products,

    get_products_for_pest,

    connection_score

)

from memory_system.product_memory import (

    get_product

)

# ==========================================
# BUILD REASONING CHAIN
# ==========================================

def build_reasoning_chain(

    semantic_state

):

    reasoning_chain = []

    # ==========================================
    # INTENT
    # ==========================================

    intent = semantic_state.get(
        "intent"
    )

    if intent:

        reasoning_chain.append(

            f"intent detected: {intent}"

        )

    # ==========================================
    # OPERATION
    # ==========================================

    operation = semantic_state.get(
        "operation"
    )

    if operation:

        reasoning_chain.append(

            f"operation detected: {operation}"

        )

    # ==========================================
    # QUERY TYPE
    # ==========================================

    query_type = semantic_state.get(
        "query_type"
    )

    if query_type:

        reasoning_chain.append(

            f"query classified: {query_type}"

        )

    # ==========================================
    # ENTITIES
    # ==========================================

    entities = semantic_state.get(
        "entities",
        {}
    )

    for entity_type, value in entities.items():

        if value:

            reasoning_chain.append(

                f"{entity_type} matched: {value}"

            )

    # ==========================================
    # CONFIDENCE
    # ==========================================

    confidence = semantic_state.get(
        "confidence"
    )

    if confidence is not None:

        reasoning_chain.append(

            f"confidence score: {confidence}"

        )

    # ==========================================
    # SAVE STATUS
    # ==========================================

    save_status = semantic_state.get(
        "save_status"
    )

    if save_status:

        reasoning_chain.append(

            f"save result: "

            f"{save_status.get('reason')}"

        )

    semantic_state[
        "reasoning_chain"
    ] = reasoning_chain

    return semantic_state

# ==========================================
# REASON ABOUT TREATMENT
# ==========================================

def reason_about_treatment(

    crop,

    pest

):

    reasoning = []

    advisor = smart_treatment_advisor(

        crop,

        pest

    )

    best_product = advisor.get(
        "best_product"
    )

    if best_product:

        reasoning.append(

            f"Best treatment product for "

            f"{pest} appears to be "

            f"{best_product['product']}"

        )

    # ==========================================
    # ROTATION LOGIC
    # ==========================================

    rotation_products = advisor.get(
        "rotation_plan",
        []
    )

    if rotation_products:

        reasoning.append(

            "Alternative treatment rotation "

            "products available"

        )

    # ==========================================
    # RECENT PRODUCT WARNING
    # ==========================================

    avoid_products = advisor.get(
        "avoid_recent_products",
        []
    )

    if avoid_products:

        reasoning.append(

            f"Recently used products: "

            f"{', '.join(avoid_products)}"

        )

    # ==========================================
    # PRODUCT REPETITION
    # ==========================================

    repetition = check_product_repetition(

        crop,

        best_product.get(
            "product"
        ) if best_product else None

    )

    if repetition:

        reasoning.append(

            "Repeated product usage detected"

        )

    return {

        "crop":
        crop,

        "pest":
        pest,

        "advisor":
        advisor,

        "reasoning":
        reasoning

    }

# ==========================================
# REASON ABOUT PRODUCT
# ==========================================

def reason_about_product(

    product

):

    reasoning = []

    product_data = get_product(
        product
    )

    if not product_data:

        return {

            "reasoning": [

                "Unknown product"

            ]

        }

    # ==========================================
    # MOA
    # ==========================================

    moa = product_data.get(
        "moa_group"
    )

    if moa:

        reasoning.append(

            f"MOA group is {moa}"

        )

    # ==========================================
    # SYSTEMIC / CONTACT
    # ==========================================

    systemic = product_data.get(
        "systemic_contact"
    )

    if systemic:

        reasoning.append(

            f"Type: {systemic}"

        )

    # ==========================================
    # TARGETS
    # ==========================================

    targets = product_data.get(
        "targets",
        []
    )

    if targets:

        reasoning.append(

            f"Targets: "

            f"{', '.join(targets)}"

        )

    # ==========================================
    # CONNECTED PRODUCTS
    # ==========================================

    connected = get_related_products(
        product
    )

    if connected:

        reasoning.append(

            f"Related products: "

            f"{', '.join(connected)}"

        )

    return {

        "product":
        product,

        "reasoning":
        reasoning

    }

# ==========================================
# REASON ABOUT CROP
# ==========================================

def reason_about_crop(crop):

    reasoning = []

    treatment_count = (

        get_crop_treatment_count(
            crop
        )

    )

    reasoning.append(

        f"{crop} has "

        f"{treatment_count} treatment events"

    )

    related_products = get_related_products(
        crop
    )

    if related_products:

        reasoning.append(

            f"Frequently linked products: "

            f"{', '.join(related_products)}"

        )

    return {

        "crop":
        crop,

        "reasoning":
        reasoning

    }

# ==========================================
# REASON ABOUT WORKER
# ==========================================

def reason_about_worker(worker):

    reasoning = []

    total_payment = get_worker_total(
        worker
    )

    reasoning.append(

        f"Total payment to "

        f"{worker} is "

        f"{total_payment}"

    )

    return {

        "worker":
        worker,

        "reasoning":
        reasoning

    }

# ==========================================
# REASON ABOUT PEST
# ==========================================

def reason_about_pest(pest):

    reasoning = []

    products = get_products_for_pest(
        pest
    )

    if products:

        reasoning.append(

            f"Known products for "

            f"{pest}: "

            f"{', '.join(products)}"

        )

    return {

        "pest":
        pest,

        "reasoning":
        reasoning

    }

# ==========================================
# GLOBAL REASONING
# ==========================================

def run_global_reasoning(

    semantic_state

):

    semantic_state = build_reasoning_chain(

        semantic_state

    )

    entities = semantic_state.get(
        "entities",
        {}
    )

    crop = entities.get(
        "crop"
    )

    pest = entities.get(
        "pest"
    )

    product = entities.get(
        "product"
    )

    worker = entities.get(
        "worker"
    )

    reasoning_outputs = {}

    # ==========================================
    # CROP + PEST
    # ==========================================

    if crop and pest:

        reasoning_outputs[
            "treatment_reasoning"
        ] = reason_about_treatment(

            crop,

            pest

        )

    # ==========================================
    # PRODUCT
    # ==========================================

    if product:

        reasoning_outputs[
            "product_reasoning"
        ] = reason_about_product(

            product

        )

    # ==========================================
    # CROP
    # ==========================================

    if crop:

        reasoning_outputs[
            "crop_reasoning"
        ] = reason_about_crop(

            crop

        )

    # ==========================================
    # WORKER
    # ==========================================

    if worker:

        reasoning_outputs[
            "worker_reasoning"
        ] = reason_about_worker(

            worker

        )

    # ==========================================
    # PEST
    # ==========================================

    if pest:

        reasoning_outputs[
            "pest_reasoning"
        ] = reason_about_pest(

            pest

        )

    semantic_state[
        "reasoning_outputs"
    ] = reasoning_outputs

    return semantic_state