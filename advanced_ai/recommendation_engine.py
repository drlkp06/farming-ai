from memory_system.product_memory import (

    search_products_by_target,

    get_product,

    get_all_products

)

from memory_system.event_memory import (

    get_events_by_crop

)

# ==========================================
# RECOMMEND PRODUCTS BY PEST
# ==========================================

def recommend_products_by_pest(

    pest

):

    products = search_products_by_target(
        pest
    )

    if not products:

        return {

            "recommendations": []

        }

    recommendations = []

    for item in products:

        recommendations.append({

            "product":

            item.get(
                "product_name"
            ),

            "formulation":

            item.get(
                "formulation"
            ),

            "moa_group":

            item.get(
                "moa_group"
            ),

            "dose":

            item.get(
                "dose"
            ),

            "effectiveness_score":

            item.get(
                "effectiveness_score"
            )

        })

    recommendations.sort(

        key=lambda x:

        x.get(
            "effectiveness_score"
        ) or 0,

        reverse=True

    )

    return {

        "recommendations":

        recommendations

    }

# ==========================================
# GET LAST USED PRODUCTS
# ==========================================

def get_last_used_products(

    crop,

    limit=5

):

    events = get_events_by_crop(
        crop
    )

    used_products = []

    for item in events:

        product = item.get(
            "product"
        )

        if (

            product

            and

            product not in used_products

        ):

            used_products.append(
                product
            )

        if len(used_products) >= limit:

            break

    return used_products

# ==========================================
# RECOMMEND ROTATION PRODUCTS
# ==========================================

def recommend_rotation_products(

    crop,

    pest

):

    recommendations = recommend_products_by_pest(
        pest
    )

    all_products = recommendations.get(
        "recommendations",
        []
    )

    last_used = get_last_used_products(
        crop
    )

    rotation_products = []

    used_moa_groups = []

    # ==========================================
    # GET USED MOA GROUPS
    # ==========================================

    for product_name in last_used:

        product_data = get_product(
            product_name
        )

        if product_data:

            moa = product_data.get(
                "moa_group"
            )

            if moa:

                used_moa_groups.append(
                    moa
                )

    # ==========================================
    # FILTER SAME MOA
    # ==========================================

    for item in all_products:

        moa = item.get(
            "moa_group"
        )

        if moa not in used_moa_groups:

            rotation_products.append(
                item
            )

    return {

        "last_used_products":

        last_used,

        "avoid_moa_groups":

        used_moa_groups,

        "recommended_rotation":

        rotation_products

    }

# ==========================================
# BEST PRODUCT
# ==========================================

def get_best_product_for_pest(

    pest

):

    recommendations = recommend_products_by_pest(
        pest
    )

    products = recommendations.get(
        "recommendations",
        []
    )

    if not products:

        return None

    return products[0]

# ==========================================
# CHECK PRODUCT REPETITION
# ==========================================

def check_product_repetition(

    crop,

    product_name

):

    last_used = get_last_used_products(
        crop,
        limit=3
    )

    if product_name in last_used:

        return {

            "repeated": True,

            "warning":

            f"{product_name} recently used in {crop}"

        }

    return {

        "repeated": False

    }

# ==========================================
# GET PRODUCTS BY MOA
# ==========================================

def get_products_by_moa(

    moa_group

):

    products = get_all_products()

    matched = []

    for item in products:

        if (

            item.get(
                "moa_group"
            )

            ==

            moa_group

        ):

            matched.append(item)

    return matched

# ==========================================
# SMART TREATMENT SUGGESTION
# ==========================================

def smart_treatment_advisor(

    crop,

    pest

):

    best_product = get_best_product_for_pest(
        pest
    )

    rotation = recommend_rotation_products(

        crop,

        pest

    )

    return {

        "crop": crop,

        "pest": pest,

        "best_product": best_product,

        "rotation_plan": [

            product

            for product in rotation.get(

                "recommended_rotation",
                []

            )

            if product.get(

                "product"

            )

            !=

            best_product.get(
                "product"
            )

        ],

        "avoid_recent_treatments":

        rotation.get(
            "last_used_products",
            []
        ),

        "avoid_repeated_groups":

        rotation.get(
            "avoid_repeated_groups",
            []
        )

    }