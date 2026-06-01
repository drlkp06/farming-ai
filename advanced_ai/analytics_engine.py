from memory_system.product_memory import (
    get_connection
)

# ==========================================
# TOTAL PAYMENTS
# ==========================================

def get_total_payments():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT SUM(amount)

    FROM records

    WHERE intent='payment'

    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0

# ==========================================
# WORKER TOTAL PAYMENT
# ==========================================

def get_worker_total(worker):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT SUM(amount)

    FROM records

    WHERE intent='payment'

    AND (

        worker=?

        OR person=?

    )

    """, (

        worker,

        worker

    ))

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0

# ==========================================
# MOST USED PRODUCT
# ==========================================

def get_most_used_product():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        product,

        COUNT(*) as total

    FROM farm_events

    WHERE product IS NOT NULL

    GROUP BY product

    ORDER BY total DESC

    LIMIT 1

    """)

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return {

        "product": row["product"],

        "count": row["total"]

    }

# ==========================================
# CROP TREATMENT COUNT
# ==========================================

def get_crop_treatment_count(

    crop,

    treatment_type=None

):

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================
    # SPECIFIC TREATMENT TYPE
    # ==========================================

    if treatment_type:

        cursor.execute("""

        SELECT COUNT(*)

        FROM farm_events

        WHERE crop=?

        AND (

            operation='treatment'

            OR operation='spray'

        )

        AND treatment_type=?

        """, (

            crop,

            treatment_type

        ))

    # ==========================================
    # ALL TREATMENTS
    # ==========================================

    else:

        cursor.execute("""

        SELECT COUNT(*)

        FROM farm_events

        WHERE crop=?

        AND (

            operation='treatment'

            OR operation='spray'

        )

        """, (

            crop,

        ))

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0

# ==========================================
# TOTAL HARVEST
# ==========================================

def get_total_harvest(crop=None):

    conn = get_connection()

    cursor = conn.cursor()

    if crop:

        cursor.execute("""

        SELECT SUM(quantity)

        FROM records

       WHERE operation='harvest'

        AND crop=?

        """, (

            crop,

        ))

    else:

        cursor.execute("""

        SELECT SUM(quantity)

        FROM records

        WHERE operation='harvest'

        """)

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0

# ==========================================
# PRODUCT USAGE COUNT
# ==========================================

def get_product_usage_count(product):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT COUNT(*)

    FROM farm_events

    WHERE product=?

    """, (

        product,

    ))

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0

# ==========================================
# MONTHLY PAYMENT SUMMARY
# ==========================================

def get_monthly_payment_summary():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        substr(created_at, 1, 7) as month,

        SUM(amount) as total

    FROM records

    WHERE intent='payment'

    GROUP BY month

    ORDER BY month DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    result = []

    for row in rows:

        result.append({

            "month": row["month"],

            "total": row["total"]

        })

    return result