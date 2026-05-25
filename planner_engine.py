from recommendation_engine import (

    smart_treatment_advisor

)

from analytics_engine import (

    get_crop_treatment_count

)

from event_memory import (

    get_events_by_crop

)

from reasoning_engine import (

    smart_farm_analysis

)

# ==========================================
# CREATE TREATMENT PLAN
# ==========================================

def create_treatment_plan(

    crop,

    pest

):

    advisor = smart_treatment_advisor(

        crop,

        pest

    )

    best_product = advisor.get(
        "best_product"
    )

    rotation_plan = advisor.get(
        "rotation_plan",
        []
    )

    plan_steps = []

    # ==========================================
    # STEP 1
    # ==========================================

    if best_product:

        plan_steps.append({

            "step": 1,

            "action":

            f"Use "

            f"{best_product['product']}",

            "reason":

            f"Recommended against {pest}"

        })

    # ==========================================
    # STEP 2
    # ==========================================

    if rotation_plan:

        alt = rotation_plan[0]

        plan_steps.append({

            "step": 2,

            "action":

            f"Keep "

            f"{alt['product']} "

            f"for next rotation",

            "reason":

            "MOA rotation"

        })

    # ==========================================
    # STEP 3
    # ==========================================

    plan_steps.append({

        "step": 3,

        "action":

        "Monitor pest population",

        "reason":

        "Evaluate treatment effectiveness"

    })

    return {

        "crop": crop,

        "pest": pest,

        "plan": plan_steps

    }

# ==========================================
# CREATE MONITORING PLAN
# ==========================================

def create_monitoring_plan(

    crop

):

    treatment_count = get_crop_treatment_count(
        crop
    )

    plan = []

    plan.append({

        "step": 1,

        "action":

        "Inspect crop leaves",

        "reason":

        "Early pest detection"

    })

    # ==========================================
    # HIGH TREATMENT WARNING
    # ==========================================

    if treatment_count >= 5:

        plan.append({

            "step": 2,

            "action":

            "Check resistance risk",

            "reason":

            "Too many treatment events"

        })

    plan.append({

        "step": 3,

        "action":

        "Record observations",

        "reason":

        "Improve future decisions"

    })

    return {

        "crop": crop,

        "monitoring_plan": plan

    }

# ==========================================
# CREATE TREATMENT ROTATION PLAN
# ==========================================

def create_treatment_rotation_plan(

    crop,

    pest

):

    advisor = smart_treatment_advisor(

        crop,

        pest

    )

    recommendations = advisor.get(
        "rotation_plan",
        []
    )

    rotation_steps = []

    step_no = 1

    for item in recommendations[:3]:

        rotation_steps.append({

            "step": step_no,

            "product":

            item.get(
                "product"
            ),

            "moa_group":

            item.get(
                "moa_group"
            ),

            "reason":

            "Avoid resistance"

        })

        step_no += 1

    return {

        "crop": crop,

        "pest": pest,

        "rotation_plan":

        rotation_steps

    }

# ==========================================
# CREATE SEASON PLAN
# ==========================================

def create_season_plan(

    crop

):

    events = get_events_by_crop(
        crop
    )

    plan = []

    # ==========================================
    # BASIC STAGES
    # ==========================================

    plan.append({

        "stage":

        "Early Stage",

        "action":

        "Monitor sucking pests"

    })

    plan.append({

        "stage":

        "Vegetative Stage",

        "action":

        "Balanced nutrition"

    })

    plan.append({

        "stage":

        "Flowering Stage",

        "action":

        "Disease monitoring"

    })

    plan.append({

        "stage":

        "Harvest Stage",

        "action":

        "Reduce residue risk"

    })

    return {

        "crop": crop,

        "event_count": len(events),

        "season_plan": plan

    }

# ==========================================
# NEXT ACTION ENGINE
# ==========================================

def next_best_action(

    crop,

    pest=None

):

    analysis = smart_farm_analysis(

        crop,

        pest

    )

    if pest:

        treatment_plan = create_treatment_plan(

            crop,

            pest

        )

        return {

            "type":

            "treatment_action",

            "analysis":

            analysis,

            "next_steps":

            treatment_plan

        }

    monitoring = create_monitoring_plan(
        crop
    )

    return {

        "type":

        "monitoring_action",

        "analysis":

        analysis,

        "next_steps":

        monitoring

    }

# ==========================================
# FULL AI FARM PLAN
# ==========================================

def generate_full_farm_plan(

    crop,

    pest=None

):

    result = {

        "crop": crop

    }

    # ==========================================
    # ANALYSIS
    # ==========================================

    result["analysis"] = (

        smart_farm_analysis(

            crop,

            pest

        )

    )

    # ==========================================
    # MONITORING
    # ==========================================

    result["monitoring"] = (

        create_monitoring_plan(
            crop
        )

    )

    # ==========================================
    # SEASON PLAN
    # ==========================================

    result["season_plan"] = (

        create_season_plan(
            crop
        )

    )

    # ==========================================
    # TREATMENT PLAN
    # ==========================================

    if pest:

        result["treatment_plan"] = (

            create_treatment_plan(

                crop,

                pest

            )

        )

        result["treatment_rotation_plan"] = (

            create_treatment_rotation_plan(

                crop,

                pest

            )

        )

    return result