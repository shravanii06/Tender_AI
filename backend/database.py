import sqlite3

DB_NAME = "tender.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_profile_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        business_type TEXT,
        category TEXT,
        experience TEXT,
        location TEXT,
        budget TEXT
    )
    """)

    conn.commit()
    conn.close()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE (UPDATED)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        category TEXT,
        location TEXT,
        budget INTEGER
    )
    """)

    # TENDERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        department TEXT,
        location TEXT,
        deadline TEXT,
        emd INTEGER,
        category TEXT,
        description TEXT,
        link TEXT,
        pdf_link TEXT,
        relevance_score REAL,
        risk_score REAL,
        difficulty_score REAL,
        fit_score REAL
    )
    """)
    # NOTIFICATIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()