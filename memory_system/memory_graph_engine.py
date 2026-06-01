from collections import defaultdict

# ==========================================
# GRAPH MEMORY
# ==========================================

GRAPH = defaultdict(list)

# ==========================================
# ADD RELATION
# ==========================================

def add_relation(

    source,

    relation,

    target

):

    GRAPH[source].append({

        "relation": relation,

        "target": target

    })

# ==========================================
# GET RELATIONS
# ==========================================

def get_relations(entity):

    return GRAPH.get(

        entity,

        []

    )

# ==========================================
# BUILD EVENT RELATIONS
# ==========================================

def learn_from_event(data):

    crop = data.get(
        "crop"
    )

    product = data.get(
        "product"
    )

    worker = data.get(
        "worker"
    )

    pest = data.get(
        "pest"
    )

    intent = data.get(
        "intent"
    )

    # ==========================================
    # CROP → PRODUCT
    # ==========================================

    if crop and product:

        add_relation(

            crop,

            "uses_product",

            product

        )

        add_relation(

            product,

            "used_in_crop",

            crop

        )

    # ==========================================
    # PEST → PRODUCT
    # ==========================================

    if pest and product:

        add_relation(

            pest,

            "treated_by",

            product

        )

        add_relation(

            product,

            "targets_pest",

            pest

        )

    # ==========================================
    # WORKER → EVENT
    # ==========================================

    if worker and intent:

        add_relation(

            worker,

            "performed",

            intent

        )

# ==========================================
# RELATED PRODUCTS
# ==========================================

def get_related_products(crop):

    relations = get_relations(
        crop
    )

    products = []

    for item in relations:

        if (

            item["relation"]

            ==

            "uses_product"

        ):

            products.append(

                item["target"]

            )

    return list(

        set(products)

    )

# ==========================================
# RELATED CROPS
# ==========================================

def get_related_crops(product):

    relations = get_relations(
        product
    )

    crops = []

    for item in relations:

        if (

            item["relation"]

            ==

            "used_in_crop"

        ):

            crops.append(

                item["target"]

            )

    return list(

        set(crops)

    )

# ==========================================
# PRODUCT FOR PEST
# ==========================================

def get_products_for_pest(pest):

    relations = get_relations(
        pest
    )

    products = []

    for item in relations:

        if (

            item["relation"]

            ==

            "treated_by"

        ):

            products.append(

                item["target"]

            )

    return list(

        set(products)

    )

# ==========================================
# GRAPH SUMMARY
# ==========================================

def graph_summary():

    total_nodes = len(GRAPH)

    total_relations = 0

    for node in GRAPH:

        total_relations += len(
            GRAPH[node]
        )

    return {

        "nodes": total_nodes,

        "relations": total_relations

    }

# ==========================================
# ENTITY CONNECTION SCORE
# ==========================================

def connection_score(

    source,

    target

):

    relations = get_relations(
        source
    )

    score = 0

    for item in relations:

        if item["target"] == target:

            score += 1

    return score

# ==========================================
# SMART RELATION SEARCH
# ==========================================

def smart_relation_search(entity):

    relations = get_relations(
        entity
    )

    grouped = {}

    for item in relations:

        rel = item["relation"]

        target = item["target"]

        if rel not in grouped:

            grouped[rel] = []

        grouped[rel].append(
            target
        )

    return grouped