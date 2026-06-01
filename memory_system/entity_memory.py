from data_layer.db_core import get_connection
import json
import os

# ==========================================
# SAVE ENTITY
# ==========================================

def save_entity(

    name,

    entity_type

):

    # ==========================================
    # BASIC SAFETY
    # ==========================================

    if not name:

        return

    if not entity_type:

        return

    # ==========================================
    # NORMALIZATION
    # ==========================================

    name = name.strip().lower()

    entity_type = entity_type.strip().lower()

    # ==========================================
    # EMPTY SAFETY
    # ==========================================

    if not name:

        return

    # ==========================================
    # GARBAGE FILTER
    # ==========================================

    blocked_entities = [

        "(",
        ")",
        ",",
        ".",
        "-",
        "_",
        "=",
        ":",
        ";"

    ]

    if name in blocked_entities:

        return

    # ==========================================
    # VERY SMALL TOKENS BLOCK
    # ==========================================

    if len(name) <= 1:

        return

    # ==========================================
    # LOAD EXISTING
    # ==========================================

    entities = load_entities(
        entity_type
    )

    # ==========================================
    # DEDUPLICATION
    # ==========================================

    normalized_entities = [

        item.strip().lower()

        for item in entities

        if item

    ]

    if name in normalized_entities:

        return

    # ==========================================
    # SAVE ENTITY
    # ==========================================

    entities.append(name)

    # ==========================================
    # SORT CLEANLY
    # ==========================================

    entities = sorted(

        list(
            set(entities)
        )

    )

    # ==========================================
    # SAVE FILE
    # ==========================================

    save_entities(

        entity_type,

        entities

    )

# ==========================================
# LOAD ENTITIES
# ==========================================

def load_entities(entity_type=None):

    conn = get_connection()

    cursor = conn.cursor()

    if entity_type:

        cursor.execute("""

        SELECT name

        FROM entities

        WHERE type=?

        """, (

            entity_type.lower(),

        ))

    else:

        cursor.execute("""

        SELECT name

        FROM entities

        """)

    rows = cursor.fetchall()

    conn.close()

    return [

        row["name"]

        for row in rows

    ]

# ==========================================
# INITIALIZE ENTITY DATABASE
# ==========================================

def initialize_entity_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================
    # ENTITY TABLE
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS entities (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT UNIQUE,

        type TEXT

    )

    """)

    # ==========================================
    # DEFAULT FARMS
    # ==========================================

    default_farms = [

        "satpuda",
        "rajpura"

    ]

    for farm in default_farms:

        cursor.execute("""

        INSERT OR IGNORE INTO entities (

            name,
            type

        )

        VALUES (?, ?)

        """, (

            farm,
            "farm"

        ))

    # ==========================================
    # DEFAULT CROPS
    # ==========================================

    default_crops = [

        "cucumber",
        "tomato",
        "tamatar",
        "kapas"

    ]

    for crop in default_crops:

        cursor.execute("""

        INSERT OR IGNORE INTO entities (

            name,
            type

        )

        VALUES (?, ?)

        """, (

            crop,
            "crop"

        ))

    # ==========================================
    # DEFAULT WORKERS
    # ==========================================

    default_workers = [

        "banwari"

    ]

    for worker in default_workers:

        cursor.execute("""

        INSERT OR IGNORE INTO entities (

            name,
            type

        )

        VALUES (?, ?)

        """, (

            worker,
            "worker"

        ))

    conn.commit()

    conn.close()

# ==========================================
# SAVE ENTITIES
# ==========================================

def save_entities(entity_type, entities):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("DELETE FROM entities WHERE type=?", (entity_type.lower(),))

    for entity in entities:

        cursor.execute("INSERT INTO entities (name, type) VALUES (?, ?)", (entity, entity_type.lower()))

    conn.commit()
    conn.close()
# ==========================================
# AUTO INITIALIZE ENTITY DATABASE
# ==========================================

initialize_entity_database()