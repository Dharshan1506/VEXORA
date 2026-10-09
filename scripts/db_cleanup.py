import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "vexora_knowledge.db")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Find docs where file doesn't exist on disk
c.execute("SELECT id, name, file_path FROM documents")
docs = c.fetchall()
to_delete = []
for doc_id, name, path in docs:
    if not path or not os.path.exists(path):
        to_delete.append((doc_id, name))

print(f"Found {len(to_delete)} orphan documents to clean:")
for doc_id, name in to_delete:
    print(f" - {name} ({doc_id})")
    c.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
    c.execute("DELETE FROM document_versions WHERE document_id = ?", (doc_id,))
    c.execute("DELETE FROM document_conflicts WHERE document_id_a = ? OR document_id_b = ?", (doc_id, doc_id))
    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

conn.commit()

c.execute("SELECT id, name, category, version, status, total_chunks FROM documents")
rows = c.fetchall()
print(f"\nRemaining real documents in DB ({len(rows)}):")
for r in rows:
    print(r)

conn.close()
