import sqlite3

DB_NAME = "tender.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


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
        relevance_score REAL,
        risk_score REAL,
        difficulty_score REAL,
        fit_score REAL
    )
    """)

    conn.commit()
    conn.close()