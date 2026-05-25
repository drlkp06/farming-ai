import sqlite3
import json
import os

# ==========================================
# DATABASE FILE
# ==========================================

DB_FILE = "memory/farm.db"

# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    os.makedirs(
        "memory",
        exist_ok=True
    )

    conn = sqlite3.connect(
        DB_FILE
    )

    conn.row_factory = sqlite3.Row

    return conn

# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_database():

    print("DATABASE INITIALIZED")

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================
    # PRODUCTS TABLE
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS products (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        product_name TEXT UNIQUE,

        category TEXT,

        formulation TEXT,

        targets TEXT,

        dose TEXT,

        moa_group TEXT,

        type TEXT,

        effectiveness_score INTEGER,

        source TEXT,

        crop_stage TEXT,

        resistance_risk TEXT,

        reentry_hours TEXT,

        phi_days TEXT,

        application_type TEXT,

        systemic_contact TEXT

    )

    """)

    conn.commit()

    conn.close()

# ==========================================
# DATABASE UPGRADE
# ==========================================

def upgrade_database():

    conn = get_connection()

    cursor = conn.cursor()

    upgrade_queries = [

        "ALTER TABLE products ADD COLUMN crop_stage TEXT",

        "ALTER TABLE products ADD COLUMN resistance_risk TEXT",

        "ALTER TABLE products ADD COLUMN reentry_hours TEXT",

        "ALTER TABLE products ADD COLUMN phi_days TEXT",

        "ALTER TABLE products ADD COLUMN application_type TEXT",

        "ALTER TABLE products ADD COLUMN systemic_contact TEXT"

    ]

    for query in upgrade_queries:

        try:

            cursor.execute(query)

        except:

            pass

    conn.commit()

    conn.close()

# ==========================================
# SAVE PRODUCT
# ==========================================

def save_product(

    product_name,

    product_data

):

    conn = get_connection()

    cursor = conn.cursor()

    product_name = product_name.strip().lower()

    existing = get_product(
        product_name
    )

    # ==========================================
    # ALREADY EXISTS
    # ==========================================

    if existing:

        conn.close()

        return {

            "saved": False,

            "message": "Product already exists.",

            "product": product_name

        }

# ==========================================
# NORMALIZE TARGETS
# ==========================================

    targets = product_data.get(
        "targets",
        []
    )

    # ==========================================
    # FORCE LIST
    # ==========================================

    if isinstance(
        targets,
        str
    ):

        targets = [

            targets

        ]

    elif not isinstance(
        targets,
        list
    ):

        targets = []

    # ==========================================
    # NORMALIZE
    # ==========================================

    normalized_targets = []

    for target in targets:

        normalized_targets.append(

            target.strip().lower()

        )

    product_data["targets"] = (

        normalized_targets

    )

    targets_json = json.dumps(

        normalized_targets

    )

    # ==========================================
    # INSERT
    # ==========================================

    cursor.execute("""

    INSERT OR REPLACE INTO products (

        product_name,
        category,
        formulation,
        targets,
        dose,
        moa_group,
        type,
        effectiveness_score,
        source,
        crop_stage,
        resistance_risk,
        reentry_hours,
        phi_days,
        application_type,
        systemic_contact

    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        product_name,

        product_data.get(
            "category"
        ),

        product_data.get(
            "formulation"
        ),

        targets_json,

        product_data.get(
            "dose"
        ),

        product_data.get(
            "moa_group"
        ),

        product_data.get(
            "type"
        ),

        product_data.get(
            "effectiveness_score"
        ),

        product_data.get(
            "source"
        ),

        product_data.get(
            "crop_stage"
        ),

        product_data.get(
            "resistance_risk"
        ),

        product_data.get(
            "reentry_hours"
        ),

        product_data.get(
            "phi_days"
        ),

        product_data.get(
            "application_type"
        ),

        product_data.get(
            "systemic_contact"
        )

    ))

    conn.commit()

    conn.close()

    return {

        "saved": True,

        "product": product_name

    }

# ==========================================
# GET PRODUCT
# ==========================================

def get_product(product_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM products

    WHERE product_name = ?

    """, (

        product_name.lower(),

    ))

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    data = dict(row)

    data["targets"] = json.loads(
        data["targets"]
    )

    return data

# ==========================================
# SEARCH PRODUCTS BY TARGET
# ==========================================

def search_products_by_target(target):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM products

    """)

    rows = cursor.fetchall()

    conn.close()

    matched = []

    for row in rows:

        data = dict(row)

        targets = data.get(
            "targets"
        )

        # ==========================================
        # HANDLE JSON LIST
        # ==========================================

        if isinstance(
            targets,
            str
        ):

            try:

                targets = json.loads(
                    targets
                )

            except:

                targets = [

                    targets

                ]

        # ==========================================
        # MATCH TARGET
        # ==========================================

        if target.lower() in [

            t.lower()

            for t in targets

        ]:

            data["targets"] = targets

            matched.append(
                data
            )

    return matched

# ==========================================
# UPDATE PRODUCT
# ==========================================

def update_product(

    product_name,

    field,

    value

):

    allowed_fields = [

        "category",
        "formulation",
        "dose",
        "moa_group",
        "type",
        "effectiveness_score",
        "source",
        "crop_stage",
        "resistance_risk",
        "reentry_hours",
        "phi_days",
        "application_type",
        "systemic_contact"

    ]

    if field not in allowed_fields:

        return {

            "updated": False,

            "reason": "invalid_field"

        }

    conn = get_connection()

    cursor = conn.cursor()

    query = f"""

    UPDATE products

    SET {field} = ?

    WHERE product_name = ?

    """

    cursor.execute(

        query,

        (

            value,

            product_name.lower()

        )

    )

    conn.commit()

    conn.close()

    return {

        "updated": True,

        "product": product_name,

        "field": field,

        "value": value

    }

# ==========================================
# DELETE PRODUCT
# ==========================================

def delete_product(product_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    DELETE FROM products

    WHERE product_name = ?

    """, (

        product_name.lower(),

    ))

    conn.commit()

    conn.close()

    return {

        "deleted": True,

        "product": product_name

    }

# ==========================================
# GET ALL PRODUCTS
# ==========================================

def get_all_products():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM products

    """)

    rows = cursor.fetchall()

    conn.close()

    all_products = []

    for row in rows:

        data = dict(row)

        data["targets"] = json.loads(
            data["targets"]
        )

        all_products.append(data)

    return all_products
# ==========================================
# INITIALIZE PRODUCT DATABASE
# ==========================================

def initialize_product_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

CREATE TABLE IF NOT EXISTS products (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_name TEXT UNIQUE,

    category TEXT,

    formulation TEXT,

    targets TEXT,

    dose TEXT,

    moa_group TEXT,

    type TEXT,

    effectiveness_score REAL,

    source TEXT,

    crop_stage TEXT,

    resistance_risk TEXT,

    reentry_hours INTEGER,

    phi_days INTEGER,

    application_type TEXT,

    systemic_contact TEXT

)

""")

    conn.commit()

    conn.close()
    