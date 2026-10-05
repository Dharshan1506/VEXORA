"""
database.py — VEXORA SQLite schema with full RAG support.
Tables:
  users, documents, document_versions, document_chunks,
  conversations, messages, retrieval_logs, document_conflicts
"""

import sqlite3
import os
import json
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "vexora_knowledge.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _migrate(conn):
    """Add columns to existing tables if missing (safe migration)."""
    cursor = conn.cursor()
    migrations = [
        # users
        ("users", "hashed_password", "TEXT NOT NULL DEFAULT ''"),
        # documents
        ("documents", "file_size", "INTEGER DEFAULT 0"),
        ("documents", "mime_type", "TEXT DEFAULT ''"),
        ("documents", "total_chunks", "INTEGER DEFAULT 0"),
        ("documents", "uploaded_by", "TEXT"),
        ("documents", "content_hash", "TEXT DEFAULT ''"),
        ("documents", "ocr_used", "INTEGER DEFAULT 0"),
        ("documents", "ocr_confidence", "REAL DEFAULT 0.0"),
        ("documents", "doc_type", "TEXT DEFAULT ''"),
        ("documents", "superseded_by", "TEXT"),
        # document_chunks
        ("document_chunks", "chunk_index", "INTEGER DEFAULT 0"),
        ("document_chunks", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("document_chunks", "ocr_used", "INTEGER DEFAULT 0"),
        ("document_chunks", "ocr_confidence", "REAL DEFAULT 1.0"),
        ("document_chunks", "content_hash", "TEXT DEFAULT ''"),
        # messages — new RAG metadata columns
        ("messages", "key_information", "TEXT"),
        ("messages", "evidence_strength", "TEXT"),
        ("messages", "evidence_status", "TEXT DEFAULT 'unknown'"),
        ("messages", "citations", "TEXT"),
        ("messages", "sources", "TEXT"),
        ("messages", "debug_info", "TEXT"),
    ]
    for table, column, col_def in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()

    # Create helpful indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status)",
        "CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(content_hash)",
        "CREATE INDEX IF NOT EXISTS idx_convs_user ON conversations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_msgs_conv ON messages(conversation_id)",
    ]
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ── Users ─────────────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'Student',
        hashed_password TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ── Documents ─────────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'General',
        version TEXT NOT NULL DEFAULT 'v1.0',
        upload_date TEXT NOT NULL,
        effective_date TEXT,
        expiry_date TEXT,
        status TEXT NOT NULL DEFAULT 'processing',
        file_path TEXT,
        file_size INTEGER DEFAULT 0,
        mime_type TEXT DEFAULT '',
        doc_type TEXT DEFAULT '',
        total_chunks INTEGER DEFAULT 0,
        uploaded_by TEXT,
        content_hash TEXT DEFAULT '',
        ocr_used INTEGER DEFAULT 0,
        ocr_confidence REAL DEFAULT 0.0,
        superseded_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    )
    """)

    # ── Document Version History ───────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_versions (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        version TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        is_superseded INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)

    # ── Document Chunks ────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL DEFAULT 0,
        content TEXT NOT NULL,
        content_hash TEXT DEFAULT '',
        page_number INTEGER DEFAULT NULL,
        section_name TEXT DEFAULT '',
        ocr_used INTEGER DEFAULT 0,
        ocr_confidence REAL DEFAULT 1.0,
        embedding TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)

    # ── Conversations ──────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT NOT NULL DEFAULT 'New Conversation',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ── Messages ───────────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        key_information TEXT,
        evidence_strength TEXT,
        evidence_status TEXT DEFAULT 'unknown',
        citations TEXT,
        sources TEXT,
        debug_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )
    """)

    # ── Retrieval Logs (for debug/audit) ──────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retrieval_logs (
        id TEXT PRIMARY KEY,
        message_id TEXT,
        query TEXT NOT NULL,
        bm25_results TEXT,
        vector_results TEXT,
        rrf_results TEXT,
        reranker_results TEXT,
        evidence_status TEXT,
        evidence_threshold REAL,
        top_scores TEXT,
        llm_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
    )
    """)

    # ── Document Conflicts ─────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_conflicts (
        id TEXT PRIMARY KEY,
        document_id_a TEXT NOT NULL,
        document_id_b TEXT NOT NULL,
        chunk_id_a TEXT,
        chunk_id_b TEXT,
        conflict_type TEXT DEFAULT 'content',
        description TEXT,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id_a) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id_b) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)

    conn.commit()

    # Run migrations on existing tables
    _migrate(conn)

    # Seed default users if none exist
    _seed_default_users(conn)

    conn.close()


def _seed_default_users(conn):
    """Create default admin and student accounts on first run."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from auth import hash_password

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    count = cursor.fetchone()["cnt"]
    if count > 0:
        return

    defaults = [
        {
            "id": str(uuid.uuid4()),
            "name": "Admin Administrator",
            "email": "admin@vexora.edu",
            "role": "System Architect",
            "password": "Admin@2026",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Student Scholar",
            "email": "student@vexora.edu",
            "role": "Computer Science Undergrad",
            "password": "Student@2026",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dr. Alex Mercer",
            "email": "scholar@university.edu",
            "role": "Professor & Researcher",
            "password": "Scholar@2026",
        },
    ]

    for u in defaults:
        hashed = hash_password(u["password"])
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, name, email, role, hashed_password) VALUES (?, ?, ?, ?, ?)",
            (u["id"], u["name"], u["email"], u["role"], hashed),
        )
        print(f"[DB] Seeded user: {u['email']} / {u['password']}")

    conn.commit()


if __name__ == "__main__":
    init_db()
    print("VEXORA SQLite Database initialized.")
