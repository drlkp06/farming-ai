import re

from learning_engine import (

    learn_word,

    get_word

)

# ==========================================
# DETECT UNKNOWN STRUCTURE
# ==========================================

def detect_new_structure(

    user_input,

    semantic_data

):

    text = user_input.lower()

    words = text.split()

    suggestions = []

    # ==========================================
    # POSSIBLE NEW FIELD
    # ==========================================

    known_fields = [

        "intent",
        "crop",
        "product",
        "worker",
        "amount",
        "quantity",
        "vendor",
        "buyer",
        "status"

    ]

    for word in words:

        if len(word) < 3:

            continue

        learned = get_word(word)

        if learned:

            continue

        # ==========================================
        # POSSIBLE ATTRIBUTE
        # ==========================================

        if word.endswith(

            ("level", "type", "mode")

        ):

            suggestions.append({

                "type":

                "new_field",

                "field":

                word

            })

    # ==========================================
    # UNKNOWN NUMERIC CONTEXT
    # ==========================================

    numeric_match = re.findall(
        r"\d+",
        text
    )

    if (

        numeric_match

        and

        not semantic_data.get(
            "amount"
        )

        and

        not semantic_data.get(
            "quantity"
        )

    ):

        suggestions.append({

            "type":

            "unknown_numeric",

            "numbers":

            numeric_match

        })

    # ==========================================
    # UNKNOWN RELATION
    # ==========================================

    if (

        semantic_data.get("crop")

        and

        semantic_data.get("product")

    ):

        crop = semantic_data["crop"]

        product = semantic_data["product"]

        relation_key = (

            f"{crop}_{product}"

        )

        existing = get_word(
            relation_key
        )

        if not existing:

            suggestions.append({

                "type":

                "new_relation",

                "crop":

                crop,

                "product":

                product

            })

    return suggestions

# ==========================================
# AUTO LEARN RELATION
# ==========================================

def auto_learn_relation(

    crop,

    product

):

    key = f"{crop}_{product}"

    learn_word(

        key,

        {

            "type":

            "crop_product_relation",

            "crop":

            crop,

            "product":

            product

        }

    )

    return {

        "learned": True,

        "relation": key

    }

# ==========================================
# SCHEMA SUGGESTION ENGINE
# ==========================================

def generate_schema_suggestions(

    semantic_data

):

    suggestions = []

    # ==========================================
    # MISSING FIELD PATTERN
    # ==========================================

    missing = semantic_data.get(
        "missing_fields",
        []
    )

    for field in missing:

        suggestions.append({

            "suggestion":

            f"Consider permanent schema field for '{field}'"

        })

    # ==========================================
    # NEW ENTITY TYPE POSSIBILITY
    # ==========================================

    if (

        semantic_data.get("vendor")

        and

        semantic_data.get("buyer")

    ):

        suggestions.append({

            "suggestion":

            "Possible transaction schema detected"

        })

    return suggestions

# ==========================================
# AUTO FIELD CLASSIFIER
# ==========================================

def classify_dynamic_field(word):

    word = word.lower()

    if word.endswith("rate"):

        return "numeric_metric"

    if word.endswith("status"):

        return "state_field"

    if word.endswith("date"):

        return "date_field"

    if word.endswith("cost"):

        return "expense_field"

    return "unknown_dynamic_field"