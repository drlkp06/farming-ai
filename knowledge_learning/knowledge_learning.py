import json
import re

# persistent batch category memory
current_batch_category = "unknown"

# storage file
PRODUCT_FILE = "memory/products.json"


# ==========================================
# LOAD SAVED PRODUCTS
# ==========================================

def load_products():

    try:

        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:

            return json.load(f)

    except:

        return {}


# ==========================================
# SAVE ALL PRODUCTS
# ==========================================

def save_products(products):

    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:

        json.dump(
            products,
            f,
            indent=2,
            ensure_ascii=False
        )


# ==========================================
# SAVE SINGLE PRODUCT
# ==========================================

def save_product(name, data):

    products = load_products()

    normalized_name = name.strip().lower()

    # ==========================================
    # PRODUCT ALREADY EXISTS
    # ==========================================

    if normalized_name in products:

        return {

            "saved": False,

            "message": "Product already exists.",

            "product": normalized_name
        }

    # ==========================================
    # NORMALIZE TARGETS
    # ==========================================

    normalized_targets = []

    for target in data.get("targets", []):

        normalized_targets.append(
            target.strip().lower()
        )

    data["targets"] = normalized_targets

    # ==========================================
    # SAVE PRODUCT
    # ==========================================

    products[normalized_name] = data

    save_products(products)

    return {

        "saved": True,

        "product": normalized_name
    }


# ==========================================
# DETECT BATCH LEARNING COMMAND
# ==========================================

def is_batch_learning_command(text):

    text = text.lower()

    triggers = [
        "learn_products:",
        "batch learn:",
        "knowledge learn:"
    ]

    return any(text.startswith(t) for t in triggers)


# ==========================================
# MAIN BATCH LEARNING PROCESSOR
# ==========================================

def process_batch_learning(text):

    global current_batch_category

    learned_products = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # ==========================================
        # DETECT CATEGORY
        # ==========================================

        if "कीटनाशक" in line or "insecticide" in line.lower():

            current_batch_category = "insecticide"

            continue

        if "fungicide" in line.lower():

            current_batch_category = "fungicide"

            continue

        if "nematicide" in line.lower():

            current_batch_category = "nematicide"

            continue

        # ==========================================
        # PRODUCT EXTRACTION
        # ==========================================

        match = re.search(
            r"([A-Za-z\s]+)\s*\((.*?)\)",
            line
        )

        if match:

            name = match.group(1).strip()

            formulation = match.group(2).strip()

            targets = []

            lower_line = line.lower()

            possible_targets = [
                "whitefly",
                "aphids",
                "thrips",
                "mites",
                "red spider mites",
                "leaf miner",
                "caterpillar",
                "eggs",
            ]

            for pest in possible_targets:

                if pest in lower_line:

                    targets.append(pest)

            # ==========================================
            # PRODUCT DATA
            # ==========================================

            product_data = {

                "category": current_batch_category,

                "formulation": formulation,

                "targets": targets,

                "source": "batch_learning",
            }

            # ==========================================
            # SAVE PRODUCT
            # ==========================================

            save_result = save_product(
                name,
                product_data
            )

            # ==========================================
            # ALREADY EXISTS
            # ==========================================

            if save_result.get("saved") is False:

                learned_products.append({

                    "product": name,

                    "status": "already_exists"
                })

            # ==========================================
            # NEW PRODUCT SAVED
            # ==========================================

            else:

                learned_products.append({

                    "product": name,

                    "status": "saved",

                    "category": current_batch_category,

                    "targets": targets
                })

    return {

        "intent": "batch_knowledge_learning",

        "status": "completed",

        "active_category": current_batch_category,

        "products_learned": learned_products,

        "count": len(learned_products),
    }