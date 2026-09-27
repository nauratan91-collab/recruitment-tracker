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

    # Seed initial manager comments/notifications if table is empty
    cursor.execute('SELECT COUNT(*) FROM candidate_comments')
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, job_requirement_id, candidate_name FROM candidates LIMIT 3")
        sample_cands = cursor.fetchall()
        if sample_cands:
            c1 = sample_cands[0]
            cursor.execute('''
                INSERT INTO candidate_comments (candidate_id, job_requirement_id, author_name, author_role, comment_type, comment_text, is_notification)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (c1['id'], c1['job_requirement_id'], 'Hiring Manager', 'Manager', 'Notification', f"Shared profile for {c1['candidate_name']} looks strong. Please expedite 1st round interview scheduling.", 1))
            if len(sample_cands) > 1:
                c2 = sample_cands[1]
                cursor.execute('''
                    INSERT INTO candidate_comments (candidate_id, job_requirement_id, author_name, author_role, comment_type, comment_text, is_notification)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (c2['id'], c2['job_requirement_id'], 'Hiring Manager', 'Manager', 'Feedback', f"Technical stack matches well with client requirements. Expected compensation is within approved budget.", 0))

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

    # Seed initial compliance documents if table is empty
    cursor.execute('SELECT COUNT(*) FROM compliance_documents')
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, client_name FROM job_requirements LIMIT 2")
        sample_reqs = cursor.fetchall()
        compliance_upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'compliance_docs')
        os.makedirs(compliance_upload_dir, exist_ok=True)

        if sample_reqs:
            r1 = sample_reqs[0]
            # Create sample dummy agreement file
            sample1_name = f"signed_client_nda_req_{r1['id']}.pdf"
            sample1_path = os.path.join(compliance_upload_dir, sample1_name)
            if not os.path.exists(sample1_path):
                with open(sample1_path, 'w', encoding='utf-8') as f:
                    f.write(f"%PDF-1.4 Mock Executed & Signed Client NDA Document for {r1['client_name']}")

            cursor.execute('''
                INSERT INTO compliance_documents 
                (job_requirement_id, agreement_type, is_signed, file_name, original_name, file_path, file_size, uploaded_by, uploaded_by_role, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r1['id'], 'client_nda', 1, sample1_name, 'Client_NDA_Executed_Signed.pdf', sample1_path, 1024, 'Hiring Manager', 'Manager', 'Bilateral Client NDA signed by authorized signatory.'))

            sample2_name = f"signed_client_msa_req_{r1['id']}.pdf"
            sample2_path = os.path.join(compliance_upload_dir, sample2_name)
            if not os.path.exists(sample2_path):
                with open(sample2_path, 'w', encoding='utf-8') as f:
                    f.write(f"%PDF-1.4 Mock Executed & Signed Client MSA Master Services Agreement for {r1['client_name']}")

            cursor.execute('''
                INSERT INTO compliance_documents 
                (job_requirement_id, agreement_type, is_signed, file_name, original_name, file_path, file_size, uploaded_by, uploaded_by_role, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r1['id'], 'client_msa', 1, sample2_name, 'Client_Master_Services_Agreement_Signed.pdf', sample2_path, 2048, 'System Administrator', 'Admin', 'Master Services Agreement valid for 2026-2027 fiscal period.'))

            if len(sample_reqs) > 1:
                r2 = sample_reqs[1]
                sample3_name = f"signed_vendor_nda_req_{r2['id']}.pdf"
                sample3_path = os.path.join(compliance_upload_dir, sample3_name)
                if not os.path.exists(sample3_path):
                    with open(sample3_path, 'w', encoding='utf-8') as f:
                        f.write(f"%PDF-1.4 Mock Executed Vendor NDA Agreement for {r2['client_name']}")

                cursor.execute('''
                    INSERT INTO compliance_documents 
                    (job_requirement_id, agreement_type, is_signed, file_name, original_name, file_path, file_size, uploaded_by, uploaded_by_role, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (r2['id'], 'vendor_nda', 1, sample3_name, 'Vendor_Staffing_NDA_Signed.pdf', sample3_path, 1536, 'Recruiter User', 'User', 'Executed vendor sub-contractor NDA signed on onboarding.'))

    conn.commit()

    # Seed data if empty
    cursor.execute('SELECT COUNT(*) FROM job_requirements')
    if cursor.fetchone()[0] == 0:
        seed_sample_data(cursor, conn)

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
    # Sample Requirement 1
    cursor.execute('''
        INSERT INTO job_requirements (client_name, end_client, job_title, job_description, work_location_type, location_city, budget, open_positions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Apex Tech Solutions',
        'FinTech Global Inc.',
        'Senior Full Stack Engineer (Python/React)',
        'Looking for a Senior Full Stack Engineer to lead microservices development and modern React dashboard UI.',
        'Hybrid',
        'New York, NY',
        '$140,000 - $160,000 / year',
        3,
        'Active'
    ))
    req1_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO compliance_records (job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared)
        VALUES (?, 1, 1, 1, 0, 1, 1)
    ''', (req1_id,))

    candidates_req1 = [
        ('Alex Morgan', 'alex.morgan@email.com', '+1 555-0192', 'Final Selected', '2026-10-15', '$85/hr', 'sample_alex_morgan_resume.pdf', 'Alex_Morgan_Resume.pdf'),
        ('Brenda Vance', 'brenda.v@email.com', '+1 555-0183', '2nd Round', '', '', '', ''),
        ('Carlos Diaz', 'carlos.d@email.com', '+1 555-0174', '1st Round', '', '', '', ''),
        ('David Miller', 'david.m@email.com', '+1 555-0165', 'Shortlisted', '', '', '', ''),
        ('Emily Watson', 'emily.w@email.com', '+1 555-0156', 'Profile Shared', '', '', '', '')
    ]
    for cand in candidates_req1:
        cursor.execute('''
            INSERT INTO candidates (job_requirement_id, candidate_name, email, phone, current_stage, doj, final_billing_rate, resume_filename, resume_original_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req1_id, cand[0], cand[1], cand[2], cand[3], cand[4], cand[5], cand[6], cand[7]))
        cand_id = cursor.lastrowid
        if cand[6]:
            # Save into resumes table as well
            cursor.execute('''
                INSERT INTO resumes (job_requirement_id, candidate_id, file_name, original_name, file_type, file_size)
                VALUES (?, ?, ?, ?, 'pdf', 1024)
            ''', (req1_id, cand_id, cand[6], cand[7]))

    # Sample Requirement 2
    cursor.execute('''
        INSERT INTO job_requirements (client_name, end_client, job_title, job_description, work_location_type, location_city, budget, open_positions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'CloudScale Systems',
        'Healthcare Alliance',
        'DevOps & Cloud Architect (AWS/Kubernetes)',
        'Managing Multi-region AWS Cloud Infrastructure, CI/CD pipelines, and Kubernetes deployments.',
        'Remote',
        'Austin, TX',
        '$90 - $110 / hour',
        2,
        'Active'
    ))
    req2_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO compliance_records (job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared)
        VALUES (?, 1, 1, 1, 1, 1, 0)
    ''', (req2_id,))

    candidates_req2 = [
        ('Frank Wright', 'frank.w@email.com', '+1 555-0147', 'Final Selected', '2026-10-01', '$105/hr', 'sample_frank_wright_resume.pdf', 'Frank_Wright_DevOps.pdf'),
        ('Grace Hopper', 'grace.h@email.com', '+1 555-0138', '1st Round', '', '', '', '')
    ]
    for cand in candidates_req2:
        cursor.execute('''
            INSERT INTO candidates (job_requirement_id, candidate_name, email, phone, current_stage, doj, final_billing_rate, resume_filename, resume_original_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req2_id, cand[0], cand[1], cand[2], cand[3], cand[4], cand[5], cand[6], cand[7]))
        cand_id = cursor.lastrowid
        if cand[6]:
            cursor.execute('''
                INSERT INTO resumes (job_requirement_id, candidate_id, file_name, original_name, file_type, file_size)
                VALUES (?, ?, ?, ?, 'pdf', 1024)
            ''', (req2_id, cand_id, cand[6], cand[7]))

    # Sample Requirement 3
    cursor.execute('''
        INSERT INTO job_requirements (client_name, end_client, job_title, job_description, work_location_type, location_city, budget, open_positions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'OmniCorp Consulting',
        'Retail Dynamics',
        'Data Engineer (Snowflake / PySpark)',
        'Building ETL data pipelines and enterprise data warehouse solutions.',
        'Work From Office',
        'Chicago, IL',
        '$120,000 / year',
        1,
        'Active'
    ))
    req3_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO compliance_records (job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared)
        VALUES (?, 1, 0, 0, 0, 1, 0)
    ''', (req3_id,))

    conn.commit()

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

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
