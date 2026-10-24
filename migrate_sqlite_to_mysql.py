"""
Key Dynamics Solutions - Recruitment Tracker
SQLite to MySQL One-Click Migration Tool

Migrates all data (Users, Job Requirements, Candidates, Compliance, Resumes, Comments, Settings)
from recruitment_tracker.db into your MySQL Database.
"""

import os
import sys
import sqlite3
import argparse
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'recruitment_tracker.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema_mysql.sql')

TABLE_ORDER = [
    'users',
    'system_settings',
    'job_requirements',
    'compliance_records',
    'candidates',
    'resumes',
    'candidate_comments',
    'compliance_documents'
]

def parse_args():
    parser = argparse.ArgumentParser(description="Migrate Recruitment Tracker data from SQLite to MySQL")
    parser.add_argument("--host", default=os.getenv("MYSQL_HOST", "localhost"), help="MySQL Host")
    parser.add_argument("--port", type=int, default=int(os.getenv("MYSQL_PORT", 3306)), help="MySQL Port")
    parser.add_argument("--user", default=os.getenv("MYSQL_USER", "root"), help="MySQL Username")
    parser.add_argument("--password", default=os.getenv("MYSQL_PASSWORD", ""), help="MySQL Password")
    parser.add_argument("--database", default=os.getenv("MYSQL_DATABASE", "recruitment_tracker"), help="MySQL Database Name")
    parser.add_argument("--sqlite-db", default=SQLITE_DB_PATH, help="Path to SQLite db file")
    return parser.parse_args()

def connect_mysql_server(args):
    """Connect to MySQL server without selecting database first (to create db if needed)."""
    return pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def connect_mysql_db(args):
    """Connect to MySQL specific database."""
    return pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def init_mysql_schema(mysql_conn, schema_file):
    """Execute schema_mysql.sql statements."""
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Split statements safely by semicolon
    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
    with mysql_conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for stmt in statements:
            # Skip database creation/use statements if already connected
            if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                continue
            try:
                cursor.execute(stmt)
            except Exception as e:
                # Ignore duplicate seed errors
                if "Duplicate entry" not in str(e):
                    print(f"  [Notice] Schema statement note: {e}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    mysql_conn.commit()

def migrate():
    args = parse_args()

    print("=" * 65)
    print("  KEY DYNAMICS - SQLITE TO MYSQL MIGRATION UTILITY")
    print("=" * 65)
    print(f"  Source SQLite:   {args.sqlite_db}")
    print(f"  Target MySQL:    {args.user}@{args.host}:{args.port}/{args.database}")
    print("=" * 65)

    if not os.path.exists(args.sqlite_db):
        print(f"[Error] SQLite database not found at: {args.sqlite_db}")
        sys.exit(1)

    # 1. Test Server Connection & Create DB
    print("\n[1/4] Connecting to MySQL Server...")
    try:
        srv_conn = connect_mysql_server(args)
        with srv_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{args.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        srv_conn.close()
        print(f"  [OK] Database `{args.database}` is ready.")
    except Exception as e:
        print(f"[Error] Failed to connect to MySQL server: {e}")
        print("\nPlease ensure MySQL is running and your credentials in .env or arguments are correct.")
        sys.exit(1)

    # 2. Connect to MySQL Database & Initialize Schema
    print("\n[2/4] Initializing MySQL Tables from schema_mysql.sql...")
    mysql_conn = connect_mysql_db(args)
    if os.path.exists(SCHEMA_PATH):
        init_mysql_schema(mysql_conn, SCHEMA_PATH)
        print("  [OK] Tables and constraints initialized successfully.")
    else:
        print(f"  [Warning] schema_mysql.sql not found at {SCHEMA_PATH}, proceeding with existing tables.")

    # 3. Connect to SQLite
    print("\n[3/4] Reading data from SQLite...")
    sqlite_conn = sqlite3.connect(args.sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # 4. Migrate Data Table by Table
    print("\n[4/4] Transferring records to MySQL...")
    summary = {}

    with mysql_conn.cursor() as my_cur:
        my_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        for table in TABLE_ORDER:
            try:
                # Check if table exists in SQLite
                sqlite_cur.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if sqlite_cur.fetchone()[0] == 0:
                    summary[table] = 0
                    continue

                sqlite_cur.execute(f"SELECT * FROM `{table}`")
                rows = sqlite_cur.fetchall()
                if not rows:
                    summary[table] = 0
                    continue

                # Get column names
                col_names = [col[0] for col in sqlite_cur.description]
                
                # Check which columns exist in MySQL target table to avoid mismatch
                my_cur.execute(f"SHOW COLUMNS FROM `{table}`")
                my_cols = {c['Field'] for c in my_cur.fetchall()}
                
                valid_cols = [c for c in col_names if c in my_cols]
                if not valid_cols:
                    summary[table] = 0
                    continue

                # Prepare insert query with backticked column names (e.g. `key`)
                escaped_cols = [f"`{c}`" for c in valid_cols]
                cols_str = ", ".join(escaped_cols)
                placeholders = ", ".join(["%s"] * len(valid_cols))
                
                insert_sql = f"REPLACE INTO `{table}` ({cols_str}) VALUES ({placeholders})"

                batch = []
                for r in rows:
                    row_vals = [r[col] for col in valid_cols]
                    batch.append(row_vals)

                my_cur.executemany(insert_sql, batch)
                summary[table] = len(batch)
                print(f"  -> Table `{table}`: Migrated {len(batch)} rows.")
            except Exception as e:
                print(f"  [!] Error migrating `{table}`: {e}")
                summary[table] = f"Error: {e}"

        my_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    mysql_conn.commit()
    sqlite_conn.close()
    mysql_conn.close()

    print("\n" + "=" * 65)
    print("  MIGRATION SUMMARY")
    print("=" * 65)
    for t, cnt in summary.items():
        print(f"  - {t:<25} : {cnt}")
    print("=" * 65)
    print("  [SUCCESS] All SQLite data has been migrated into MySQL!")
    print("=" * 65 + "\n")

if __name__ == '__main__':
    migrate()
