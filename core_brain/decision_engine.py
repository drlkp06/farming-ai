from core_brain.validation_engine import (
    validate_record
)

# ==========================================
# DECIDE ACTION
# ==========================================

def decide_action(

    semantic_data

):

    validation = validate_record(
        semantic_data
    )

    errors = validation.get(
        "errors",
        []
    )

    warnings = validation.get(
        "warnings",
        []
    )

    # ==========================================
    # HARD FAILURE
    # ==========================================

    if errors:

        return {

            "decision":

            "reject",

            "reason":

            errors,

            "automation_policy":

            "manual_required"

        }

    # ==========================================
    # WARNING MODE
    # ==========================================

    if warnings:

        return {

            "decision":

            "review",

            "reason":

            warnings,

            "automation_policy":

            "human_review"

        }

    # ==========================================
    # MISSING FIELDS
    # ==========================================

    if semantic_data.get(
        "needs_clarification"
    ):

        return {

            "decision":

            "clarify",

            "reason":

            semantic_data.get(
                "missing_fields",
                []
            ),

            "automation_policy":

            "clarification_required"

        }

    # ==========================================
    # SAFE AUTO SAVE
    # ==========================================

    return {

        "decision":

        "accept",

        "reason":

        [

            "Record validated successfully"

        ],

        "automation_policy":

        "safe_auto_save"

    }

# ==========================================
# CONFIDENCE DECISION
# ==========================================

def confidence_decision(

    confidence_score

):

    if confidence_score >= 0.90:

        return {

            "confidence_level":

            "very_high",

            "action":

            "auto_accept"

        }

    if confidence_score >= 0.75:

        return {

            "confidence_level":

            "high",

            "action":

            "accept"

        }

    if confidence_score >= 0.60:

        return {

            "confidence_level":

            "medium",

            "action":

            "confirm"

        }

    return {

        "confidence_level":

        "low",

        "action":

        "reject"

    }

# ==========================================
# AUTOMATION RISK LEVEL
# ==========================================

def automation_risk(

    semantic_data

):

    intent = semantic_data.get(
        "intent"
    )

    # ==========================================
    # LOW RISK
    # ==========================================

    low_risk = [

        "payment",

        "treatment",

        "harvest"

    ]

    if intent in low_risk:

        return {

            "risk_level":

            "low"

    }
    # ==========================================
    # MEDIUM RISK
    # ==========================================

    medium_risk = [

        "purchase",
        "expense"

    ]

    if intent in medium_risk:

        return {

            "risk_level":

            "medium"

        }

    # ==========================================
    # HIGH RISK
    # ==========================================

    return {

        "risk_level":

        "high"

    }

# ==========================================
# FINAL AI DECISION
# ==========================================

def final_ai_decision(

    semantic_data

):

    validation = decide_action(
        semantic_data
    )

    risk = automation_risk(
        semantic_data
    )

    confidence = confidence_decision(

        semantic_data.get(
            "context_confidence"
        ) or 1.0

    )

    return {

        "validation":

        validation,

        "risk":

        risk,

        "confidence":

        confidence

    }

# ==========================================
# SHOULD AUTO SAVE
# ==========================================

def should_auto_save(semantic_data):

    decision = final_ai_decision(
        semantic_data
    )

    validation = decision[
        "validation"
    ][
        "decision"
    ]

    confidence = decision[
        "confidence"
    ][
        "action"
    ]

    print("\n=== AUTO SAVE DEBUG ===")
    print("VALIDATION:", validation)
    print("CONFIDENCE:", confidence)
    print("INTENT:", semantic_data.get("intent"))
    print("OPERATION:", semantic_data.get("operation"))

    if validation != "accept":
        return False

    if confidence == "reject":
        return False

    return True