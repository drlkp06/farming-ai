import sqlite3
import os

DB_FILE = "memory/farm.db"

# ==========================================
# CONNECTION
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
# INIT DATABASE
# ==========================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================
    # PRODUCTS
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

    # ==========================================
    # ENTITIES
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS entities (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT UNIQUE,

        entity_type TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ==========================================
    # RECORDS
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS records (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        intent TEXT,

        worker TEXT,

        person TEXT,

        amount REAL,

        quantity REAL,

        unit TEXT,

        crop TEXT,

        product TEXT,

        buyer TEXT,

        vendor TEXT,

        status TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ==========================================
    # FARM EVENTS
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS farm_events (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        event_type TEXT,

        crop TEXT,

        product TEXT,

        pest TEXT,

        worker TEXT,

        notes TEXT,

        raw_input TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    conn.commit()

    conn.close()

    print("DATABASE INITIALIZED")

# ==========================================