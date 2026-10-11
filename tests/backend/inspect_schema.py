import sqlite3

conn = sqlite3.connect("dev.db")
cursor = conn.cursor()

print("=== TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
for t in tables:
    print(f"  {t}")
    cursor.execute(f"PRAGMA table_info({t})")
    for col in cursor.fetchall():
        print(f"    col[{col[0]}]: {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} pk={col[5]}")

print("\n=== INDEXES ===")
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name")
for r in cursor.fetchall():
    print(f"  {r[1]}.{r[0]}")

print("\n=== UNIQUE CONSTRAINTS ===")
for t in tables:
    cursor.execute(f"PRAGMA index_list({t})")
    for idx in cursor.fetchall():
        if idx[2]:  # unique
            print(f"  UNIQUE on {t}: {idx[1]}")

conn.close()
print("Schema inspection complete.")
