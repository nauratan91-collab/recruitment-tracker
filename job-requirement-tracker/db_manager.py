"""
Database Management CLI for RecruitPulse
Usage:
    python db_manager.py status    - Show table counts, schema, and database size
    python db_manager.py export    - Export full database to SQL file (backup.sql)
    python db_manager.py reset     - Reset and re-seed database
"""
import sys
import os
from database import init_db, get_database_stats, export_database_to_sql, DB_PATH, get_db

def show_status():
    stats = get_database_stats()
    print("=" * 60)
    print(f"RECRUITPULSE DATABASE STATUS")
    print("=" * 60)
    print(f"Database File : {stats['database_file']}")
    print(f"File Path     : {stats['database_path']}")
    print(f"File Size     : {stats['size_formatted']}")
    print("-" * 60)
    print("TABLES & RECORD COUNTS:")
    for table, info in stats['tables'].items():
        col_names = ", ".join([c['name'] for c in info['columns']])
        print(f" - {table:<20}: {info['row_count']} records")
        print(f"   Columns: {col_names}")
    print("=" * 60)

def export_sql(out_filename="backup.sql"):
    sql_text = export_database_to_sql()
    out_path = os.path.join(os.path.dirname(__file__), out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sql_text)
    print(f"[SUCCESS] Database exported to: {out_path} ({os.path.getsize(out_path)} bytes)")

def reset_db():
    confirm = input("Are you sure you want to reset and reseed the database? (y/N): ")
    if confirm.lower() == 'y':
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("[INFO] Existing database file deleted.")
        init_db()
        print("[SUCCESS] Database re-initialized and seeded with default data.")
    else:
        print("[INFO] Reset cancelled.")

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if arg == 'status':
        show_status()
    elif arg == 'export':
        export_sql()
    elif arg == 'reset':
        reset_db()
    else:
        print(f"Unknown command: {arg}")
        print(__doc__)
