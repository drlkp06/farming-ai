from advanced_ai.analytics_engine import (

    get_crop_treatment_count,

    get_product_usage_count

)

from memory_system.memory_graph_engine import (

    get_related_products,

    get_products_for_pest

)

from memory_system.event_memory import (

    get_events_by_crop

)

from advanced_ai.recommendation_engine import (

    recommend_rotation_products

)

# ==========================================
# PEST RISK PREDICTION
# ==========================================

def predict_pest_risk(

    crop,

    pest

):

    events = get_events_by_crop(
        crop
    )

    treatment_count = (

        get_crop_treatment_count(
            crop
        )

    )

    related_products = (

        get_products_for_pest(
            pest
        )

    )

    risk_score = 0

    reasoning = []

    # ==========================================
    # LOW TREATMENT COUNT
    # ==========================================

    if treatment_count <= 1:

        risk_score += 30

        reasoning.append(

            "Very low treatment protection"

        )

    elif treatment_count <= 3:

        risk_score += 15

        reasoning.append(

            "Moderate treatment protection"

        )

    # ==========================================
    # NO PEST PRODUCTS
    # ==========================================

    if not related_products:

        risk_score += 25

        reasoning.append(

            "No known product history "

            f"for {pest}"

        )

    # ==========================================
    # MANY EVENTS
    # ==========================================

    if len(events) >= 10:

        risk_score += 10

        reasoning.append(

            "High crop activity detected"

        )

    # ==========================================
    # FINAL RISK LEVEL
    # ==========================================

    if risk_score >= 50:

        level = "high"

    elif risk_score >= 25:

        level = "medium"

    else:

        level = "low"

    return {

        "crop": crop,

        "pest": pest,

        "risk_score": risk_score,

        "risk_level": level,

        "reasoning": reasoning

    }

# ==========================================
# RESISTANCE RISK
# ==========================================

def predict_resistance_risk(

    crop,

    product

):

    usage_count = get_product_usage_count(
        product
    )

    related_products = get_related_products(
        crop
    )

    risk = 0

    reasoning = []

    # ==========================================
    # HIGH USAGE
    # ==========================================

    if usage_count >= 10:

        risk += 40

        reasoning.append(

            "Product heavily used"

        )

    elif usage_count >= 5:

        risk += 20

        reasoning.append(

            "Moderate repeated usage"

        )

    # ==========================================
    # REPEATED CROP LINK
    # ==========================================

    crop_usage = related_products.count(
        product
    )

    if crop_usage >= 3:

        risk += 30

        reasoning.append(

            "Repeated same product "

            "in crop"

        )

    # ==========================================
    # FINAL LEVEL
    # ==========================================

    if risk >= 50:

        level = "high"

    elif risk >= 25:

        level = "medium"

    else:

        level = "low"

    return {

        "crop": crop,

        "product": product,

        "risk_score": risk,

        "risk_level": level,

        "reasoning": reasoning

    }

# ==========================================
# YIELD PREDICTION
# ==========================================

def predict_yield_health(

    crop

):

    events = get_events_by_crop(
        crop
    )

    treatment_count = (

        get_crop_treatment_count(
            crop
        )

    )

    score = 50

    reasoning = []

    # ==========================================
    # TREATMENT ACTIVITY
    # ==========================================

    if treatment_count >= 3:

        score += 20

        reasoning.append(

            "Treatment activity detected"

        )

    elif treatment_count == 0:

        score -= 20

        reasoning.append(

            "No treatment activity detected"

        )

    # ==========================================
    # EVENT DENSITY
    # ==========================================

    if len(events) >= 5:

        score += 10

        reasoning.append(

            "Good farm activity"

        )

    # ==========================================
    # FINAL STATUS
    # ==========================================

    if score >= 75:

        status = "excellent"

    elif score >= 55:

        status = "good"

    elif score >= 35:

        status = "average"

    else:

        status = "poor"

    return {

        "crop": crop,

        "health_score": score,

        "yield_prediction": status,

        "reasoning": reasoning

    }

# ==========================================
# NEXT TREATMENT PREDICTION
# ==========================================

def predict_next_treatment_need(

    crop,

    pest

):

    pest_risk = predict_pest_risk(

        crop,

        pest

    )

    resistance = recommend_rotation_products(

        crop,

        pest

    )

    risk_level = pest_risk.get(
        "risk_level"
    )

    if risk_level == "high":

        urgency = "immediate"

        days = 1

    elif risk_level == "medium":

        urgency = "soon"

        days = 3

    else:

        urgency = "monitor"

        days = 7

    return {

        "crop": crop,

        "pest": pest,

        "urgency": urgency,

        "suggested_days": days,

        "rotation_products":

        resistance.get(
            "recommended_rotation",
            []
        ),

        "reasoning":

        pest_risk.get(
            "reasoning",
            []
        )

    }

# ==========================================
# FARM HEALTH PREDICTION
# ==========================================

def overall_farm_prediction(

    crop,

    pest=None

):

    result = {}

    # ==========================================
    # YIELD HEALTH
    # ==========================================

    result["yield"] = predict_yield_health(
        crop
    )

    # ==========================================
    # PEST RISK
    # ==========================================

    if pest:

        result["pest_risk"] = (

            predict_pest_risk(

                crop,

                pest

            )

        )

        result["next_action"] = (

            predict_next_treatment_need(

                crop,

                pest

            )

        )

    return result