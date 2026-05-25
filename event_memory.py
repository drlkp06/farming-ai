import sqlite3
import json
from datetime import datetime

# ==========================================
# DATABASE PATH
# ==========================================

DB_PATH = "memory/farm.db"

# ==========================================
# CONNECTION
# ==========================================

def get_connection():

    return sqlite3.connect(
        DB_PATH
    )

# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_event_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================
    # FARM EVENTS TABLE
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS farm_events (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        semantic_signature TEXT,

        semantic_snapshot TEXT,

        intent TEXT,
        operation TEXT,

        farm TEXT,
        crop TEXT,

        product TEXT,
        pest TEXT,

        worker TEXT,
        vendor TEXT,
        buyer TEXT,

        quantity REAL,
        unit TEXT,

        amount REAL,

        status TEXT,

        raw_text TEXT,

        event_date TEXT,

        created_at TIMESTAMP

    )

    """)

    cursor.execute(
        "PRAGMA table_info(farm_events)"
    )

    columns = [

        row[1]

        for row in cursor.fetchall()

    ]

    if "event_date" not in columns:

        cursor.execute("""

        ALTER TABLE farm_events
        ADD COLUMN event_date TEXT

        """)

    conn.commit()

    conn.close()

# ==========================================
# GENERATE SEMANTIC SIGNATURE
# ==========================================

def generate_semantic_signature(

    semantic_state

):

    entities = semantic_state.get(
        "entities",
        {}
    )

    def get_entity(field):

        return (

            entities.get(
                field
            )

            or

            semantic_state.get(
                field
            )

            or

            ""

        )

    return "|".join([

        str(
            semantic_state.get(
                "intent",
                ""
            )
        ),

        str(
            semantic_state.get(
                "operation",
                ""
            )
        ),

        str(
            get_entity(
                "farm"
            )
        ),

        str(
            get_entity(
                "crop"
            )
        ),

        str(
            get_entity(
                "worker"
            )
        ),

        str(
            get_entity(
                "product"
            )
        ),

        str(
            semantic_state.get(
                "quantity",
                ""
            )
        ),

        str(
            semantic_state.get(
                "amount",
                ""
            )
        )

        ,

        str(
            semantic_state.get(
                "event_date",
                ""
            )
        )

    ])

# ==========================================
# SAVE FARM EVENT
# ==========================================

def save_farm_event(

    semantic_state

):

    # ==========================================
    # ENTRY ONLY
    # ==========================================

    if not semantic_state.get(
        "is_entry"
    ):

        return {

            "saved":
            False,

            "reason":
            "not_entry"

        }

    conn = get_connection()

    cursor = conn.cursor()

    entities = semantic_state.get(
        "entities",
        {}
    )

    def get_entity(field):

        return (

            entities.get(
                field
            )

            or

            semantic_state.get(
                field
            )

        )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    
    # ==========================================
    # SEMANTIC SIGNATURE
    # ==========================================

    semantic_signature = (

        generate_semantic_signature(

            semantic_state

        )

    )

    # ==========================================
    # DUPLICATE CHECK
    # ==========================================

    cursor.execute("""

    SELECT id

    FROM farm_events

    WHERE semantic_signature=?

    LIMIT 1

    """, (

        semantic_signature,

    ))

    existing = cursor.fetchone()

    # ==========================================
    # DUPLICATE FOUND
    # ==========================================

    if existing:

        conn.close()

        return {

            "saved":
            False,

            "reason":
            "duplicate_event"

        }

    # ==========================================
    # SEMANTIC SNAPSHOT
    # ==========================================

    semantic_snapshot = json.dumps(

        semantic_state,

        ensure_ascii=False,

        default=str

    )

    # ==========================================
    # INSERT EVENT
    # ==========================================

    cursor.execute("""

    INSERT INTO farm_events (

        semantic_signature,
        semantic_snapshot,

        intent,
        operation,

        farm,
        crop,

        product,
        pest,

        worker,
        vendor,
        buyer,

        quantity,
        unit,

        amount,

        status,

        raw_text,

        event_date,

        created_at

    )

    VALUES (

        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?

    )

    """, (

        semantic_signature,
        semantic_snapshot,

        semantic_state.get(
            "intent"
        ),

        semantic_state.get(
            "operation"
        ),

        get_entity(
            "farm"
        ),

        get_entity(
            "crop"
        ),

        get_entity(
            "product"
        ),

        get_entity(
            "pest"
        ),

        get_entity(
            "worker"
        ),

        get_entity(
            "vendor"
        ),

        get_entity(
            "buyer"
        ),

        semantic_state.get(
            "quantity"
        ),

        semantic_state.get(
            "unit"
        ),

        semantic_state.get(
            "amount"
        ),

        semantic_state.get(
            "status"
        ),

        semantic_state.get(
            "raw_input"
        ),

        semantic_state.get(
            "event_date"
        ),

        created_at

    ))

    conn.commit()
    
    # ==========================================
    # UPDATE MEMORY
    # ==========================================

    semantic_state.setdefault(

        "memory_updates",

        []

    ).append(

        "farm event persisted"

    )

    conn.close()

    return {

        "saved":
        True,

        "reason":
        "event_saved"

    }

# ==========================================
# TOTAL PAYMENT
# ==========================================

def get_total_payment(worker, event_date=None):

    conn = get_connection()

    cursor = conn.cursor()

    date_filter = ""
    params = []

    if event_date:

        date_filter = " AND event_date=?"

    if worker:

        cursor.execute("""

    SELECT SUM(amount)

    FROM farm_events

    WHERE lower(trim(worker))=?
    AND (
        lower(trim(intent))='payment'
        OR lower(trim(operation))='payment'
    )
    """ + date_filter + """

    """, tuple([

        worker.lower().strip()

    ] + ([event_date] if event_date else [])))

    else:

        cursor.execute("""

    SELECT SUM(amount)

    FROM farm_events

    WHERE (
        lower(trim(intent))='payment'
        OR lower(trim(operation))='payment'
    )
    """ + date_filter + """

    """, tuple([event_date] if event_date else []))

    result = cursor.fetchone()

    conn.close()

    if not result:

        return 0

    return result[0] or 0

# ==========================================
# TOTAL EXPENSE
# ==========================================

def get_total_expense(

    product=None,

    farm=None,

    event_date=None

):

    conn = get_connection()

    cursor = conn.cursor()

    where_clauses = [

        "("
        "lower(trim(intent))='expense' "
        "OR lower(trim(operation))='expense'"
        ")"

    ]

    params = []

    if product:

        where_clauses.append(

            "lower(trim(product))=?"

        )

        params.append(

            product.lower().strip()

        )

    if farm:

        where_clauses.append(

            "lower(trim(farm))=?"

        )

        params.append(

            farm.lower().strip()

        )

    if event_date:

        where_clauses.append(

            "event_date=?"

        )

        params.append(

            event_date

        )

    cursor.execute(

        """
        SELECT SUM(COALESCE(amount, quantity))
        FROM farm_events
        WHERE
        """
        + " AND ".join(where_clauses),
        tuple(params)

    )

    result = cursor.fetchone()

    conn.close()

    if not result:

        return 0

    return result[0] or 0

# ==========================================
# PAYMENT HISTORY
# ==========================================

def get_payment_history(worker):

    conn = get_connection()

    cursor = conn.cursor()

    if worker:

        cursor.execute("""

        SELECT worker, amount, created_at

        FROM farm_events

        WHERE lower(trim(worker))=?
        AND (
            lower(trim(intent))='payment'
            OR lower(trim(operation))='payment'
        )

        ORDER BY id DESC

        """, (

            worker.lower().strip(),

        ))

    else:

        cursor.execute("""

        SELECT worker, amount, created_at

        FROM farm_events

        WHERE (
            lower(trim(intent))='payment'
            OR lower(trim(operation))='payment'
        )

        ORDER BY id DESC

        """)

    rows = cursor.fetchall()

    conn.close()

    return rows

# ==========================================
# EVENTS BY CROP
# ==========================================

def get_events_by_crop(crop):

    if not crop:

        return []

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM farm_events

    WHERE lower(trim(crop))=?

    ORDER BY id DESC

    """, (

        crop.lower().strip(),

    ))

    rows = cursor.fetchall()

    conn.close()

    return rows

# ==========================================
# LAST TREATMENT
# ==========================================

def get_last_treatment(crop):

    if not crop:

        return None

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT product, created_at

    FROM farm_events

    WHERE lower(trim(crop))=?
    AND lower(trim(operation))='treatment'

    ORDER BY id DESC

    LIMIT 1

    """, (

        crop.lower().strip(),

    ))

    row = cursor.fetchone()

    conn.close()

    return row

# ==========================================
# PRODUCT HISTORY
# ==========================================

def get_product_history(product):

    if not product:

        return []

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT crop, created_at

    FROM farm_events

    WHERE lower(trim(product))=?

    ORDER BY id DESC

    """, (

        product.lower().strip(),

    ))

    rows = cursor.fetchall()

    conn.close()

    return rows

# ==========================================
# HARVEST QUANTITY
# ==========================================

def get_harvest_quantity(

    crop,

    farm=None,

    event_date=None

):

    if not crop:

        return 0

    conn = get_connection()

    cursor = conn.cursor()

    date_filter = ""

    if event_date:

        date_filter = " AND event_date=?"

    # ==========================================
    # FARM FILTER
    # ==========================================

    if farm:

        cursor.execute("""

        SELECT SUM(quantity)

        FROM farm_events

        WHERE lower(trim(crop))=?
        AND lower(trim(farm))=?
        AND lower(trim(operation))='harvest'
        """ + date_filter + """

        """, tuple([

            crop.lower().strip(),
            farm.lower().strip()

        ] + ([event_date] if event_date else [])))

    else:

        cursor.execute("""

        SELECT SUM(quantity)

        FROM farm_events

        WHERE lower(trim(crop))=?
        AND lower(trim(operation))='harvest'
        """ + date_filter + """

        """, tuple([

            crop.lower().strip()

        ] + ([event_date] if event_date else [])))

    result = cursor.fetchone()

    conn.close()

    if not result:

        return 0

    return result[0] or 0
