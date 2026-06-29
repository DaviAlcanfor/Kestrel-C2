import sqlite3
import os

DB_PATH = "kast.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS victims (
            vic_id     TEXT PRIMARY KEY,
            hostname   TEXT,
            ip_priv    TEXT,
            ip_pub     TEXT,
            plat       TEXT,
            system     TEXT,
            machine    TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def insert_victim(info: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO victims 
        (vic_id, hostname, ip_priv, ip_pub, plat, system, machine)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        info["vic_id"],
        info["hostname"],
        info["ip_priv"],
        info["ip_pub"],
        info["plat"],
        info["system"],
        info["machine"]
    ))

    conn.commit()
    conn.close()


def get_victims():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM victims")
    rows = cursor.fetchall()

    conn.close()
    return rows