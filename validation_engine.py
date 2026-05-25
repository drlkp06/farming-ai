import re

from entity_memory import (
    load_entities
)

from product_memory import (
    get_product
)

# ==========================================
# VALIDATE RECORD
# ==========================================

def validate_record(

    semantic_data

):

    errors = []

    warnings = []

    # ==========================================
    # INTENT REQUIRED
    # ==========================================

    if not semantic_data.get(
        "intent"
    ):

        errors.append(

            "Missing intent"

        )

    # ==========================================
    # PAYMENT VALIDATION
    # ==========================================

    if semantic_data.get(
        "intent"
    ) == "payment":

        amount = semantic_data.get(
            "amount"
        )

        if amount is None:

            errors.append(

                "Payment amount missing"

            )

        elif amount <= 0:

            errors.append(

                "Invalid payment amount"

            )

        elif amount > 100000:

            warnings.append(

                "Very high payment amount"

            )

    # ==========================================
    # TREATMENT VALIDATION
    # ==========================================

    if semantic_data.get(
        "operation"
    ) == "treatment":
        
        crop = semantic_data.get(
            "crop"
        )

        product = semantic_data.get(
            "product"
        )

        if not crop:

            errors.append(

                "Crop missing"

            )

        if not product:

            errors.append(

                "Product missing"

            )

        # ==========================================
        # PRODUCT EXISTS
        # ==========================================

        if product:

            product_data = get_product(
                product
            )

            if not product_data:

                warnings.append(

                    f"Unknown product: {product}"

                )

    # ==========================================
    # HARVEST VALIDATION
    # ==========================================

    if semantic_data.get(
        "intent"
    ) == "harvest":

        qty = semantic_data.get(
            "quantity"
        )

        if qty is None:

            errors.append(

                "Harvest quantity missing"

            )

        elif qty <= 0:

            errors.append(

                "Invalid harvest quantity"

            )

        elif qty > 100000:

            warnings.append(

                "Very large harvest quantity"

            )

    # ==========================================
    # ENTITY VALIDATION
    # ==========================================

    workers = load_entities(
        "worker"
    )

    if semantic_data.get(
        "worker"
    ):

        if (

            semantic_data["worker"]

            not in workers

        ):

            warnings.append(

                f"Unknown worker: "

                f"{semantic_data['worker']}"

            )

    # ==========================================
    # INVALID CHARACTERS
    # ==========================================

    text_fields = [

        "crop",
        "product",
        "worker",
        "vendor",
        "buyer"

    ]

    for field in text_fields:

        value = semantic_data.get(
            field
        )

        if value:

            if not re.match(

                r"^[a-zA-Z0-9_\-\s]+$",

                str(value)

            ):

                warnings.append(

                    f"Suspicious characters in {field}"

                )

    # ==========================================
    # DUPLICATE FIELD CHECK
    # ==========================================

    if (

        semantic_data.get("crop")

        and

        semantic_data.get("product")

    ):

        if (

            semantic_data["crop"]

            ==

            semantic_data["product"]

        ):

            warnings.append(

                "Crop and product are identical"

            )

    # ==========================================
    # FINAL RESULT
    # ==========================================

    return {

        "valid":

        len(errors) == 0,

        "errors":

        errors,

        "warnings":

        warnings

    }

# ==========================================
# AUTO CLEAN RECORD
# ==========================================

def auto_clean_record(

    semantic_data

):

    # ==========================================
    # LOWERCASE NORMALIZATION
    # ==========================================

    text_fields = [

        "crop",
        "product",
        "worker",
        "vendor",
        "buyer"

    ]

    for field in text_fields:

        value = semantic_data.get(
            field
        )

        if (

            value

            and

            isinstance(value, str)

        ):

            semantic_data[field] = (

                value.lower().strip()

            )

    # ==========================================
    # REMOVE EMPTY STRINGS
    # ==========================================

    for key in semantic_data:

        if semantic_data[key] == "":

            semantic_data[key] = None

    return semantic_data

# ==========================================
# DUPLICATE EVENT DETECTION
# ==========================================

def is_possible_duplicate(

    old_event,

    new_event

):

    important_fields = [

        "intent",
        "crop",
        "product",
        "worker",
        "amount",
        "quantity"

    ]

    matched = 0

    for field in important_fields:

        if (

            old_event.get(field)

            and

            old_event.get(field)

            ==

            new_event.get(field)

        ):

            matched += 1

    return matched >= 4

# ==========================================
# QUICK FIELD VALIDATOR
# ==========================================

def validate_field(

    field,

    value

):

    if field == "amount":

        try:

            value = float(value)

            return value > 0

        except:

            return False

    if field == "quantity":

        try:

            value = float(value)

            return value > 0

        except:

            return False

    if field in [

        "crop",
        "product",
        "worker"

    ]:

        return len(

            str(value).strip()

        ) > 1

    return True