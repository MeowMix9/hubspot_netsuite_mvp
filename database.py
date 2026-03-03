import sqlite3
import os
from datetime import datetime

# ---------------------------
# Paths
# ---------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "fwd_crm.db")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------
# Database Connection
# ---------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================
def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # ===============================
    # CUSTOMERS
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        hubspot_id TEXT,
        netsuite_id TEXT,
        source_system TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        company TEXT,
        brand TEXT,
        lifecycle_stage TEXT,
        pipeline_stage TEXT,
        customer_type TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        country TEXT,
        notes TEXT,
        created_at TEXT,
        last_synced_at TEXT,
        environment TEXT
    )
    """)

    # ===============================
    # BRANDS (NEW)
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        environment TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(name, environment)
    )
    """)

    # ===============================
    # EMAIL TEMPLATES (NEW)
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        subject TEXT,
        body TEXT,
        image_url TEXT,
        environment TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (brand_id) REFERENCES brands(id)
    )
    """)

    # ===============================
    # STATES
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS states (
        code TEXT PRIMARY KEY,
        name TEXT
    )
    """)

    # ===============================
    # COUNTRIES
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        name TEXT PRIMARY KEY
    )
    """)

    # ===============================
    # PIPELINE STAGES
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_stages (
        id TEXT PRIMARY KEY,
        name TEXT,
        environment TEXT
    )
    """)

    # ===============================
    # TICKETS
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        ticket_name TEXT,
        pipeline TEXT,
        status TEXT,
        created_at TEXT,
        priority TEXT,
        source TEXT,
        last_activity TEXT,
        assigned_to TEXT,
        environment TEXT
    )
    """)

    # ===============================
    # IMPORT JOBS
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS import_jobs (
        id TEXT PRIMARY KEY,
        source TEXT,
        filename TEXT,
        record_count INTEGER,
        status TEXT,
        imported_at TEXT
    )
    """)

    # ===============================
    # AUDIT LOG
    # ===============================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id TEXT PRIMARY KEY,
        entity_type TEXT,
        entity_id TEXT,
        action TEXT,
        changed_at TEXT,
        changed_by TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


# =========================================================
# BRAND FUNCTIONS
# =========================================================
def fetch_brands(environment):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM brands WHERE environment=? ORDER BY name",
        (environment,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_brand(name, environment):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO brands (name, environment, created_at) VALUES (?, ?, ?)",
        (name, environment, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_brand_by_name(name, environment):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM brands WHERE name=? AND environment=?",
        (name, environment)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# =========================================================
# TEMPLATE FUNCTIONS
# =========================================================
def fetch_templates_by_brand(brand_id, environment):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM email_templates
        WHERE brand_id=? AND environment=? AND is_active=1
        ORDER BY created_at DESC
    """, (brand_id, environment)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_template(brand_id, name, subject, body, image_url, environment):
    conn = get_conn()
    conn.execute("""
        INSERT INTO email_templates
        (brand_id, name, subject, body, image_url, environment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_id,
        name,
        subject,
        body,
        image_url,
        environment,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def deactivate_template(template_id):
    conn = get_conn()
    conn.execute("""
        UPDATE email_templates
        SET is_active=0, updated_at=?
        WHERE id=?
    """, (datetime.now().isoformat(), template_id))
    conn.commit()
    conn.close()


# =========================================================
# EXISTING FETCH FUNCTIONS
# =========================================================
def fetch_customers(environment=None):
    conn = get_conn()
    cursor = conn.cursor()
    if environment:
        cursor.execute("SELECT * FROM customers WHERE environment = ?", (environment,))
    else:
        cursor.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_pipeline_stages(environment=None):
    conn = get_conn()
    cursor = conn.cursor()
    if environment:
        cursor.execute("SELECT * FROM pipeline_stages WHERE environment = ?", (environment,))
    else:
        cursor.execute("SELECT * FROM pipeline_stages")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_tickets(environment=None):
    conn = get_conn()
    cursor = conn.cursor()
    if environment:
        cursor.execute("SELECT * FROM tickets WHERE environment = ?", (environment,))
    else:
        cursor.execute("SELECT * FROM tickets")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

import uuid

def generate_id(prefix="ID"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"