import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

ORIGINAL_DB_PATH = os.path.join(os.path.dirname(__file__), 'recruitment_tracker.db')

# On Vercel serverless runtime, filesystem is read-only except /tmp
if os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    import shutil
    DB_PATH = '/tmp/recruitment_tracker.db'
    if not os.path.exists(DB_PATH):
        if os.path.exists(ORIGINAL_DB_PATH):
            try:
                shutil.copy2(ORIGINAL_DB_PATH, DB_PATH)
            except Exception as e:
                print("Notice: Error copying database to /tmp:", e)
else:
    DB_PATH = ORIGINAL_DB_PATH

def get_default_rights(role):
    """Returns standard rights mapping for a given role."""
    r = (role or 'User').capitalize()
    if r == 'Admin':
        return {
            'can_manage_requirements': True,
            'can_manage_candidates': True,
            'can_post_comments': True,
            'can_manage_compliance': True,
            'can_view_reports': True,
            'can_access_database': True,
            'can_access_admin': True
        }
    elif r == 'Manager':
        return {
            'can_manage_requirements': True,
            'can_manage_candidates': True,
            'can_post_comments': True,
            'can_manage_compliance': True,
            'can_view_reports': True,
            'can_access_database': False,
            'can_access_admin': False
        }
    else:  # User / Recruiter
        return {
            'can_manage_requirements': True,
            'can_manage_candidates': True,
            'can_post_comments': False,
            'can_manage_compliance': True,
            'can_view_reports': False,
            'can_access_database': False,
            'can_access_admin': False
        }

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Job Requirements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            end_client TEXT,
            job_title TEXT NOT NULL,
            job_description TEXT,
            work_location_type TEXT NOT NULL DEFAULT 'Hybrid', -- Remote, Work From Office, Hybrid
            location_city TEXT,
            budget TEXT,
            spoc_name TEXT, -- Client SPOC Person Name
            spoc_mobile TEXT, -- Client SPOC Mobile / Contact Number
            open_positions INTEGER NOT NULL DEFAULT 1,
            status TEXT DEFAULT 'Active',
            open_date TEXT, -- Requirement Opening Date (YYYY-MM-DD)
            close_date TEXT, -- Requirement Closure Date (YYYY-MM-DD)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migrations for job_requirements table: add open_date, close_date, spoc_name, spoc_mobile if missing
    try:
        cursor.execute("ALTER TABLE job_requirements ADD COLUMN open_date TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE job_requirements ADD COLUMN close_date TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE job_requirements ADD COLUMN spoc_name TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE job_requirements ADD COLUMN spoc_mobile TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE job_requirements ADD COLUMN updated_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    # Ensure any rows with empty open_date are backfilled from created_at
    cursor.execute("UPDATE job_requirements SET open_date = SUBSTR(created_at, 1, 10) WHERE open_date IS NULL OR open_date = ''")

    # 2. Compliance Table (NDA & MSA for Client, Vendor, Consultant)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_requirement_id INTEGER NOT NULL UNIQUE,
            client_nda_shared INTEGER DEFAULT 0,
            client_msa_shared INTEGER DEFAULT 0,
            vendor_nda_shared INTEGER DEFAULT 0,
            vendor_msa_shared INTEGER DEFAULT 0,
            consultant_nda_shared INTEGER DEFAULT 0,
            consultant_msa_shared INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
        )
    ''')

    # 3. Candidates table (Profile shared, Shortlisted, 1st Round, 2nd Round, Final Selected, DOJ, Billing Rate, Resume)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_requirement_id INTEGER NOT NULL,
            candidate_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            current_stage TEXT NOT NULL DEFAULT 'Profile Shared', 
            -- Stages: 'Profile Shared', 'Shortlisted', '1st Round', '2nd Round', 'Final Selected', 'Rejected'
            doj TEXT, -- Date of Joining / Project Start Date
            final_billing_rate TEXT, -- What we bill the client
            consultant_pay_rate TEXT, -- What we pay the consultant
            resume_filename TEXT,
            resume_original_name TEXT,
            notes TEXT,
            -- Sourcing details:
            source_type TEXT DEFAULT 'Internal', -- 'Internal' or 'Vendor'
            current_ctc TEXT,
            expected_ctc TEXT,
            notice_period TEXT,
            current_location TEXT,
            remarks TEXT,
            vendor_name TEXT,
            vendor_billing_rate TEXT,
            current_company TEXT,
            office_work_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
        )
    ''')

    # Migrations for existing databases: add candidate columns if missing
    candidate_cols = [
        ("consultant_pay_rate", "TEXT"),
        ("source_type", "TEXT DEFAULT 'Internal'"),
        ("current_ctc", "TEXT"),
        ("expected_ctc", "TEXT"),
        ("notice_period", "TEXT"),
        ("current_location", "TEXT"),
        ("remarks", "TEXT"),
        ("vendor_name", "TEXT"),
        ("vendor_billing_rate", "TEXT"),
        ("current_company", "TEXT"),
        ("office_work_type", "TEXT")
    ]
    for col_name, col_type in candidate_cols:
        try:
            cursor.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # 4. Resumes table (Stores file binary BLOB and metadata in database)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_requirement_id INTEGER NOT NULL,
            candidate_id INTEGER,
            file_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            file_data BLOB,
            file_path TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE SET NULL
        )
    ''')

    # 5. Users table (Authentication & Role-Based Access Control)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User', -- 'Admin', 'Manager', 'User'
            full_name TEXT,
            rights TEXT, -- JSON string of permissions
            status TEXT DEFAULT 'Active', -- 'Active', 'Inactive'
            auth_provider TEXT DEFAULT 'Local', -- 'Local', 'Microsoft 365'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migrations for users table: add email, rights, status, auth_provider if missing
    for col_name, col_def in [
        ('email', 'TEXT'),
        ('rights', 'TEXT'),
        ('status', "TEXT DEFAULT 'Active'"),
        ('auth_provider', "TEXT DEFAULT 'Local'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
        except sqlite3.OperationalError:
            pass

    # Ensure index on users email
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    except Exception:
        pass

    # Seed or backfill default corporate Key Dynamics emails & rights
    default_accounts = [
        ('admin', 'admin@keydynamicssolutions.com', 'Admin@123', 'Admin', 'System Administrator'),
        ('manager', 'manager@keydynamicssolutions.com', 'Manager@123', 'Manager', 'Hiring Manager'),
        ('user', 'user@keydynamicssolutions.com', 'User@123', 'User', 'Recruiter User')
    ]
    for uname, uemail, upass, urole, ufullname in default_accounts:
        cursor.execute("SELECT id, email, rights, status FROM users WHERE username = ?", (uname,))
        row = cursor.fetchone()
        role_rights_json = json.dumps(get_default_rights(urole))
        if not row:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role, full_name, rights, status, auth_provider) VALUES (?, ?, ?, ?, ?, ?, 'Active', 'Local')",
                (uname, uemail, generate_password_hash(upass), urole, ufullname, role_rights_json)
            )
        else:
            # Backfill email and rights if empty or outdated domain
            cursor.execute(
                "UPDATE users SET email = COALESCE(email, ?), rights = COALESCE(rights, ?), status = COALESCE(status, 'Active') WHERE id = ?",
                (uemail, role_rights_json, row['id'])
            )

    # Migrate any existing records with @keydynamics.com to @keydynamicssolutions.com
    cursor.execute("UPDATE users SET email = REPLACE(email, '@keydynamics.com', '@keydynamicssolutions.com') WHERE email LIKE '%@keydynamics.com'")

    # 6. Candidate Comments & Notifications table (Manager notes, feedback, and priority notifications)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_requirement_id INTEGER,
            author_user_id INTEGER,
            author_name TEXT NOT NULL,
            author_role TEXT NOT NULL DEFAULT 'Manager',
            comment_type TEXT NOT NULL DEFAULT 'Comment', -- 'Comment', 'Notification', 'Feedback', 'Shortlist Decision'
            comment_text TEXT NOT NULL,
            is_notification INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')

    # 7. Compliance Documents Table (Signed Agreements, Uploader, Remarks)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_requirement_id INTEGER NOT NULL,
            agreement_type TEXT NOT NULL, 
            -- 'client_nda', 'client_msa', 'vendor_nda', 'vendor_msa', 'consultant_nda', 'consultant_msa'
            is_signed INTEGER DEFAULT 1,
            file_name TEXT,
            original_name TEXT,
            file_path TEXT,
            file_size INTEGER,
            uploaded_by TEXT NOT NULL,
            uploaded_by_role TEXT,
            remark TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_compliance_docs_req ON compliance_documents(job_requirement_id)")

    # 8. System Settings Table (USD/INR Exchange Rate, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('usd_inr_exchange_rate', '84.00')")

    conn.commit()
    conn.close()

def save_resume_to_db(job_requirement_id, candidate_id, filename, original_name, file_bytes=None, file_path=None):
    """Saves resume metadata and binary content directly into the SQLite database."""
    conn = get_db()
    cursor = conn.cursor()

    file_size = len(file_bytes) if file_bytes else (os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0)
    file_type = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'unknown'

    cursor.execute('''
        INSERT INTO resumes (job_requirement_id, candidate_id, file_name, original_name, file_type, file_size, file_data, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (job_requirement_id, candidate_id, filename, original_name, file_type, file_size, file_bytes, file_path))

    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id

def get_database_stats():
    """Returns database overview, table counts, schemas, and file size."""
    conn = get_db()
    cursor = conn.cursor()

    tables = ['job_requirements', 'candidates', 'compliance_records', 'resumes', 'users', 'candidate_comments', 'compliance_documents']
    stats = {}

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [dict(col) for col in cursor.fetchall()]
            stats[table] = {
                'row_count': count,
                'columns': columns
            }
        except Exception as e:
            stats[table] = {'row_count': 0, 'columns': [], 'error': str(e)}

    conn.close()

    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        'database_file': os.path.basename(DB_PATH),
        'database_path': DB_PATH,
        'size_bytes': db_size,
        'size_formatted': f"{db_size / 1024:.2f} KB",
        'tables': stats
    }

def get_table_rows(table_name, limit=100):
    """Retrieves rows for a specific table."""
    allowed_tables = {'job_requirements', 'candidates', 'compliance_records', 'resumes', 'candidate_comments', 'compliance_documents'}
    if table_name not in allowed_tables:
        return []

    conn = get_db()
    cursor = conn.cursor()
    # Exclude heavy BLOB file_data in tabular views for performance
    if table_name == 'resumes':
        cursor.execute("SELECT id, job_requirement_id, candidate_id, file_name, original_name, file_type, file_size, file_path, uploaded_at FROM resumes ORDER BY id DESC LIMIT ?", (limit,))
    else:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,))
    
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def export_database_to_sql():
    """Generates a complete SQL dump of the database."""
    conn = get_db()
    dump_lines = []
    for line in conn.iterdump():
        dump_lines.append(line)
    conn.close()
    return '\n'.join(dump_lines)

def seed_sample_data(cursor, conn):
    # Dummy sample data disabled - application operates with clean real enterprise data
    pass

def verify_user(login_identifier, password):
    """Verifies username OR corporate email & password. Checks active status and returns parsed rights."""
    if not login_identifier or not password:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?))
    """, (login_identifier.strip(), login_identifier.strip()))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    user_dict = dict(row)
    if user_dict.get('status') == 'Inactive':
        return {'error': 'Account is inactive. Please contact your administrator.'}
    if check_password_hash(user_dict['password_hash'], password):
        user_dict.pop('password_hash', None)
        try:
            parsed_rights = json.loads(user_dict['rights']) if user_dict.get('rights') else get_default_rights(user_dict.get('role'))
        except Exception:
            parsed_rights = get_default_rights(user_dict.get('role'))
        user_dict['rights'] = parsed_rights
        user_dict['rights_parsed'] = parsed_rights
        return user_dict
    return None

def change_user_password(user_id, old_password, new_password):
    """Changes password for user after verifying old password. Returns (success, message)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."

    if not check_password_hash(row['password_hash'], old_password):
        conn.close()
        return False, "Current password does not match."

    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Password updated successfully."

def get_user_by_id(user_id):
    """Retrieves user by id without password hash, including parsed rights."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, full_name, rights, status, auth_provider, created_at, updated_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    u = dict(row)
    try:
        parsed_rights = json.loads(u['rights']) if u.get('rights') else get_default_rights(u.get('role'))
    except Exception:
        parsed_rights = get_default_rights(u.get('role'))
    u['rights'] = parsed_rights
    u['rights_parsed'] = parsed_rights
    return u

def get_all_users():
    """Retrieves all users with parsed rights and without password hashes."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, full_name, rights, status, auth_provider, created_at, updated_at FROM users ORDER BY id ASC")
    rows = cursor.fetchall()
    users = []
    for r in rows:
        u = dict(r)
        try:
            parsed_rights = json.loads(u['rights']) if u.get('rights') else get_default_rights(u.get('role'))
        except Exception:
            parsed_rights = get_default_rights(u.get('role'))
        u['rights'] = parsed_rights
        u['rights_parsed'] = parsed_rights
        users.append(u)
    conn.close()
    return users

def create_user(username, email, password, role='User', full_name=None, rights=None, status='Active'):
    """Creates a new user or manager account with role and rights."""
    conn = get_db()
    cursor = conn.cursor()

    # Check duplicate username
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    if cursor.fetchone():
        conn.close()
        return None, "Username already exists."

    # Check duplicate email
    if email and email.strip():
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        if cursor.fetchone():
            conn.close()
            return None, "Email address already in use."

    rights_dict = rights if isinstance(rights, dict) else get_default_rights(role)
    rights_json = json.dumps(rights_dict)
    pwd_hash = generate_password_hash(password)

    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role, full_name, rights, status, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Local')
    ''', (username.strip(), email.strip() if email else None, pwd_hash, role, full_name or username, rights_json, status))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id, "User created successfully."

def update_user(user_id, email=None, full_name=None, role=None, rights=None, status=None):
    """Updates user profile, role, rights, and status."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."

    # Check email uniqueness if changed
    if email and email.strip():
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email.strip(), user_id))
        if cursor.fetchone():
            conn.close()
            return False, "Email address is already in use by another account."

    updates = []
    params = []
    if email is not None:
        updates.append("email = ?")
        params.append(email.strip() if email else None)
    if full_name is not None:
        updates.append("full_name = ?")
        params.append(full_name.strip())
    if role is not None:
        updates.append("role = ?")
        params.append(role)
    if rights is not None:
        updates.append("rights = ?")
        params.append(json.dumps(rights) if isinstance(rights, dict) else rights)
    if status is not None:
        updates.append("status = ?")
        params.append(status)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        params.append(user_id)
        cursor.execute(query, params)
        conn.commit()

    conn.close()
    return True, "User updated successfully."

def admin_reset_user_password(user_id, new_password):
    """Allows admin to reset any user's password directly."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return False, "User not found."

    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Password reset successfully."

def delete_user(user_id):
    """Deletes a user account. Cannot delete primary administrator (id=1 or username='admin')."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
    if row['username'] == 'admin' or row['id'] == 1:
        conn.close()
        return False, "Primary administrator account cannot be deleted."

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True, "User deleted successfully."

def verify_or_create_microsoft_user(email, full_name=None, role='User'):
    """Handles Microsoft Dynamics 365 single-sign-on login."""
    if not email:
        return None, "Email is required."
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    if row:
        user_dict = dict(row)
        conn.close()
        if user_dict.get('status') == 'Inactive':
            return None, 'Account is inactive. Contact your administrator.'
        user_dict.pop('password_hash', None)
        try:
            parsed_rights = json.loads(user_dict['rights']) if user_dict.get('rights') else get_default_rights(user_dict.get('role'))
        except Exception:
            parsed_rights = get_default_rights(user_dict.get('role'))
        user_dict['rights'] = parsed_rights
        user_dict['rights_parsed'] = parsed_rights
        return user_dict, None

    # Auto-provision Key Dynamics Microsoft 365 corporate user
    uname = email.split('@')[0].lower().replace('.', '_')
    cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
    if cursor.fetchone():
        uname = f"{uname}_{int(datetime.now().timestamp()) % 1000}"

    default_rights = json.dumps(get_default_rights(role))
    random_pwd_hash = generate_password_hash('M365@' + datetime.now().strftime('%Y%m%d%H%M%S'))
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role, full_name, rights, status, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, 'Active', 'Microsoft 365')
    ''', (uname, email.strip(), random_pwd_hash, role, full_name or uname.replace('_', ' ').title(), default_rights))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
    new_user = dict(cursor.fetchone())
    conn.close()
    new_user.pop('password_hash', None)
    parsed_rights = get_default_rights(role)
    new_user['rights'] = parsed_rights
    new_user['rights_parsed'] = parsed_rights
    return new_user, None

# -------------------------------------------------------------------
# CANDIDATE PROFILE COMMENTS & MANAGER NOTIFICATIONS
# -------------------------------------------------------------------
def add_candidate_comment(candidate_id, author_name, author_role, comment_text, comment_type='Comment', is_notification=0, author_user_id=None):
    """Adds a comment or notification to a candidate profile."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT job_requirement_id FROM candidates WHERE id = ?", (candidate_id,))
    cand_row = cursor.fetchone()
    req_id = cand_row['job_requirement_id'] if cand_row else None

    cursor.execute("""
        INSERT INTO candidate_comments (
            candidate_id, job_requirement_id, author_user_id, author_name, author_role,
            comment_type, comment_text, is_notification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (candidate_id, req_id, author_user_id, author_name, author_role, comment_type, comment_text, 1 if is_notification else 0))

    comment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return comment_id

def get_candidate_comments(candidate_id):
    """Retrieves all comments/notifications for a candidate profile in chronological order."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM candidate_comments 
        WHERE candidate_id = ? 
        ORDER BY id ASC
    """, (candidate_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_recent_notifications(limit=25):
    """Retrieves recent manager notifications and comments across all candidate profiles."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cc.*, c.candidate_name, c.current_stage, r.job_title, r.client_name
        FROM candidate_comments cc
        JOIN candidates c ON cc.candidate_id = c.id
        LEFT JOIN job_requirements r ON cc.job_requirement_id = r.id
        ORDER BY cc.id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def save_compliance_document(req_id, agreement_type, is_signed=1, file_name=None, original_name=None, file_path=None, file_size=0, uploaded_by='Admin', uploaded_by_role='Admin', remark=None):
    """Saves compliance document record and keeps compliance_records flag in sync."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO compliance_documents 
        (job_requirement_id, agreement_type, is_signed, file_name, original_name, file_path, file_size, uploaded_by, uploaded_by_role, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (req_id, agreement_type, 1 if is_signed else 0, file_name, original_name, file_path, file_size, uploaded_by, uploaded_by_role, remark))
    doc_id = cursor.lastrowid

    # Synchronize corresponding flag in compliance_records
    agreement_col_map = {
        'client_nda': 'client_nda_shared',
        'client_msa': 'client_msa_shared',
        'vendor_nda': 'vendor_nda_shared',
        'vendor_msa': 'vendor_msa_shared',
        'consultant_nda': 'consultant_nda_shared',
        'consultant_msa': 'consultant_msa_shared',
    }
    col = agreement_col_map.get(agreement_type)
    if col:
        cursor.execute("SELECT id FROM compliance_records WHERE job_requirement_id = ?", (req_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(f"UPDATE compliance_records SET {col} = ?, updated_at = CURRENT_TIMESTAMP WHERE job_requirement_id = ?", (1 if is_signed else 0, req_id))
        else:
            cursor.execute(f"INSERT INTO compliance_records (job_requirement_id, {col}) VALUES (?, ?)", (req_id, 1 if is_signed else 0))

    conn.commit()
    conn.close()
    return doc_id

def get_compliance_documents(req_id=None):
    """Retrieves compliance documents, optionally filtered by job_requirement_id."""
    conn = get_db()
    cursor = conn.cursor()
    if req_id:
        cursor.execute("SELECT * FROM compliance_documents WHERE job_requirement_id = ? ORDER BY id DESC", (req_id,))
    else:
        cursor.execute("SELECT * FROM compliance_documents ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_compliance_document(doc_id, remark=None, is_signed=None, agreement_type=None, file_name=None, original_name=None, file_path=None, file_size=None):
    """Updates remark, signed status, agreement type or file for a compliance document."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM compliance_documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return False, "Document not found."

    updates = []
    params = []
    if remark is not None:
        updates.append("remark = ?")
        params.append(remark.strip())
    if is_signed is not None:
        updates.append("is_signed = ?")
        params.append(1 if is_signed else 0)
    if agreement_type is not None:
        updates.append("agreement_type = ?")
        params.append(agreement_type)
    if file_name is not None:
        updates.append("file_name = ?")
        params.append(file_name)
    if original_name is not None:
        updates.append("original_name = ?")
        params.append(original_name)
    if file_path is not None:
        updates.append("file_path = ?")
        params.append(file_path)
    if file_size is not None:
        updates.append("file_size = ?")
        params.append(file_size)

    if updates:
        query = f"UPDATE compliance_documents SET {', '.join(updates)} WHERE id = ?"
        params.append(doc_id)
        cursor.execute(query, params)

    # Sync compliance_records if is_signed or agreement_type changed
    ag_type = agreement_type or doc['agreement_type']
    agreement_col_map = {
        'client_nda': 'client_nda_shared',
        'client_msa': 'client_msa_shared',
        'vendor_nda': 'vendor_nda_shared',
        'vendor_msa': 'vendor_msa_shared',
        'consultant_nda': 'consultant_nda_shared',
        'consultant_msa': 'consultant_msa_shared',
    }
    col = agreement_col_map.get(ag_type)
    if col and is_signed is not None:
        cursor.execute(f"UPDATE compliance_records SET {col} = ?, updated_at = CURRENT_TIMESTAMP WHERE job_requirement_id = ?", (1 if is_signed else 0, doc['job_requirement_id']))

    conn.commit()
    conn.close()
    return True, "Document updated successfully."

def delete_compliance_document(doc_id):
    """Deletes a compliance document and syncs the compliance status matrix."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM compliance_documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return False, "Document not found."

    req_id = doc['job_requirement_id']
    ag_type = doc['agreement_type']
    file_p = doc['file_path']

    cursor.execute("DELETE FROM compliance_documents WHERE id = ?", (doc_id,))

    # Check if remaining docs exist for this type
    agreement_col_map = {
        'client_nda': 'client_nda_shared',
        'client_msa': 'client_msa_shared',
        'vendor_nda': 'vendor_nda_shared',
        'vendor_msa': 'vendor_msa_shared',
        'consultant_nda': 'consultant_nda_shared',
        'consultant_msa': 'consultant_msa_shared',
    }
    col = agreement_col_map.get(ag_type)
    if col:
        cursor.execute("SELECT COUNT(*) FROM compliance_documents WHERE job_requirement_id = ? AND agreement_type = ?", (req_id, ag_type))
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            cursor.execute(f"UPDATE compliance_records SET {col} = 0, updated_at = CURRENT_TIMESTAMP WHERE job_requirement_id = ?", (req_id,))

    conn.commit()
    conn.close()

    if file_p and os.path.exists(file_p):
        try:
            os.remove(file_p)
        except Exception:
            pass

    return True, "Document deleted successfully."

def get_system_setting(key, default='84.00'):
    """Retrieves a system configuration setting."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['value']
    return default

def set_system_setting(key, value):
    """Updates or sets a system configuration setting."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO system_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    ''', (key, str(value)))
    conn.commit()
    conn.close()
    return True

def get_all_system_settings():
    """Returns all system configuration settings as a dict."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value, updated_at FROM system_settings")
    rows = cursor.fetchall()
    conn.close()
    settings = {}
    for r in rows:
        settings[r['key']] = r['value']
    if 'usd_inr_exchange_rate' not in settings:
        settings['usd_inr_exchange_rate'] = '84.00'
    return settings

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
