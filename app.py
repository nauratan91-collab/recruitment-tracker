import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response, session
from werkzeug.utils import secure_filename
from database import (
    get_db, init_db, get_database_stats, get_table_rows, 
    export_database_to_sql, save_resume_to_db, DB_PATH,
    verify_user, change_user_password, get_user_by_id,
    add_candidate_comment, get_candidate_comments, get_recent_notifications,
    save_compliance_document, get_compliance_documents,
    update_compliance_document, delete_compliance_document,
    get_all_users, create_user, update_user, admin_reset_user_password,
    delete_user, verify_or_create_microsoft_user, get_default_rights,
    get_system_setting, set_system_setting, get_all_system_settings
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'key-dynamics-solutions-secure-secret-2026')

# Configure upload folders (Serverless /tmp fallback for Vercel)
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')

if IS_VERCEL:
    UPLOAD_FOLDER = '/tmp/uploads/resumes'
    COMPLIANCE_UPLOAD_FOLDER = '/tmp/uploads/compliance_docs'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'resumes')
    COMPLIANCE_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'compliance_docs')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit

ALLOWED_COMPLIANCE_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
app.config['COMPLIANCE_UPLOAD_FOLDER'] = COMPLIANCE_UPLOAD_FOLDER

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(COMPLIANCE_UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print("Notice: Error creating upload directories:", e)

# On Vercel, copy any existing sample uploads into /tmp
if IS_VERCEL:
    import shutil
    src_resumes = os.path.join(os.path.dirname(__file__), 'uploads', 'resumes')
    src_comp = os.path.join(os.path.dirname(__file__), 'uploads', 'compliance_docs')
    if os.path.exists(src_resumes):
        for f in os.listdir(src_resumes):
            s = os.path.join(src_resumes, f)
            d = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(s) and not os.path.exists(d):
                try:
                    shutil.copy2(s, d)
                except Exception:
                    pass
    if os.path.exists(src_comp):
        for f in os.listdir(src_comp):
            s = os.path.join(src_comp, f)
            d = os.path.join(COMPLIANCE_UPLOAD_FOLDER, f)
            if os.path.isfile(s) and not os.path.exists(d):
                try:
                    shutil.copy2(s, d)
                except Exception:
                    pass

# Initialize database on start
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_compliance_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_COMPLIANCE_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

# -------------------------------------------------------------------
# AUTHENTICATION API (USERNAME OR KEY DYNAMICS / MICROSOFT 365 EMAIL)
# -------------------------------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    identifier = data.get('username') or data.get('email') or ''
    identifier = identifier.strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'Username/corporate email and password are required.'}), 400

    user = verify_user(identifier, password)
    if not user:
        return jsonify({'error': 'Invalid credentials. Please verify your username or Key Dynamics corporate email and password.'}), 401

    if isinstance(user, dict) and user.get('error'):
        return jsonify({'error': user['error']}), 403

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['email'] = user.get('email')
    session['role'] = user['role']
    session['full_name'] = user.get('full_name')
    session['rights'] = user.get('rights_parsed', get_default_rights(user['role']))

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user.get('email'),
            'role': user['role'],
            'full_name': user['full_name'],
            'rights': session['rights'],
            'status': user.get('status', 'Active'),
            'auth_provider': user.get('auth_provider', 'Local')
        }
    })

@app.route('/api/auth/microsoft-login', methods=['POST'])
def microsoft_login():
    """Enterprise Microsoft Dynamics 365 / Office 365 Single-Sign-On."""
    data = request.json or {}
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip() or None
    role = data.get('role', 'User')

    if not email:
        return jsonify({'error': 'Microsoft Dynamics 365 corporate email is required.'}), 400

    user, err = verify_or_create_microsoft_user(email, full_name, role)
    if err:
        return jsonify({'error': err}), 403

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['email'] = user.get('email')
    session['role'] = user['role']
    session['full_name'] = user.get('full_name')
    session['rights'] = user.get('rights_parsed', get_default_rights(user['role']))

    return jsonify({
        'success': True,
        'auth_provider': 'microsoft_dynamics_365',
        'message': 'Microsoft Dynamics 365 authentication successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user.get('email'),
            'role': user['role'],
            'full_name': user['full_name'],
            'rights': session['rights'],
            'status': user.get('status', 'Active'),
            'auth_provider': 'microsoft_dynamics_365'
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 200

    return jsonify({
        'authenticated': True,
        'user': user
    })

@app.route('/api/auth/change-password', methods=['POST'])
def change_password():
    user_id = session.get('user_id')
    data = request.json or {}

    # Support changing password while logged in or specifying username
    username = data.get('username')
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not old_password or not new_password:
        return jsonify({'error': 'Current password and new password are required.'}), 400

    if confirm_password and new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400

    target_user_id = user_id
    if not target_user_id and username:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            target_user_id = row['id']

    if not target_user_id:
        return jsonify({'error': 'Please login first or provide valid username.'}), 401

    success, msg = change_user_password(target_user_id, old_password, new_password)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'success': True, 'message': msg})

# -------------------------------------------------------------------
# DASHBOARD STATS API
# -------------------------------------------------------------------
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()

    # Total requirements & positions
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(open_positions), 0) FROM job_requirements WHERE status = 'Active'")
    total_reqs, total_openings = cursor.fetchone()

    # Total candidates shared
    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_candidates = cursor.fetchone()[0]

    # Candidate Stage Breakdown
    stages = ['Profile Shared', 'Shortlisted', '1st Round', '2nd Round', 'Final Selected', 'Rejected']
    stage_counts = {stage: 0 for stage in stages}
    
    cursor.execute("SELECT current_stage, COUNT(*) FROM candidates GROUP BY current_stage")
    for row in cursor.fetchall():
        if row['current_stage'] in stage_counts:
            stage_counts[row['current_stage']] = row[1]

    # Location distribution
    location_counts = {'Remote': 0, 'Work From Office': 0, 'Hybrid': 0}
    cursor.execute("SELECT work_location_type, COUNT(*) FROM job_requirements GROUP BY work_location_type")
    for row in cursor.fetchall():
        if row['work_location_type'] in location_counts:
            location_counts[row['work_location_type']] = row[1]

    # Compliance Health Summary
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN client_nda_shared=1 AND client_msa_shared=1 AND vendor_nda_shared=1 AND vendor_msa_shared=1 AND consultant_nda_shared=1 AND consultant_msa_shared=1 THEN 1 ELSE 0 END) as fully_compliant,
            COUNT(*) as total
        FROM compliance_records
    """)
    comp_row = cursor.fetchone()
    fully_compliant = comp_row['fully_compliant'] or 0
    total_compliance_records = comp_row['total'] or 0

    conn.close()

    return jsonify({
        'total_requirements': total_reqs,
        'total_openings': total_openings,
        'total_candidates_shared': total_candidates,
        'stage_counts': stage_counts,
        'location_counts': location_counts,
        'compliance_summary': {
            'fully_compliant': fully_compliant,
            'total': total_compliance_records,
            'pending': total_compliance_records - fully_compliant
        }
    })

# -------------------------------------------------------------------
# JOB REQUIREMENTS API & TAT (TURNAROUND TIME) CALCULATION
# -------------------------------------------------------------------
def calculate_tat(open_date_str, close_date_str=None, status='Active', created_at=None):
    """
    Calculates TAT (Turnaround Time / Aging in days).
    - If status is 'Filled' or 'Closed': TAT = Days from open_date to close_date.
    - If status is 'Active' or 'On Hold': TAT = Days from open_date to current date.
    Returns: (tat_days, tat_display, tat_badge_type)
    """
    if not open_date_str:
        if created_at:
            open_date_str = str(created_at)[:10]
        else:
            open_date_str = date.today().isoformat()

    try:
        open_dt = datetime.strptime(str(open_date_str).strip()[:10], '%Y-%m-%d').date()
    except Exception:
        open_dt = date.today()

    is_closed = (status in ['Filled', 'Closed'])
    if is_closed and close_date_str:
        try:
            end_dt = datetime.strptime(str(close_date_str).strip()[:10], '%Y-%m-%d').date()
        except Exception:
            end_dt = date.today()
    else:
        end_dt = date.today()

    tat_days = max(0, (end_dt - open_dt).days)
    if is_closed:
        tat_display = f"Closed in {tat_days} Days"
    else:
        tat_display = f"{tat_days} Days Open"

    if tat_days < 15:
        badge_type = 'green'  # Fresh / Normal (<15 days)
    elif tat_days <= 30:
        badge_type = 'amber'  # Moderate (15-30 days)
    else:
        badge_type = 'red'  # Aging (>30 days)

    return tat_days, tat_display, badge_type

@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            r.*,
            c.client_nda_shared, c.client_msa_shared,
            c.vendor_nda_shared, c.vendor_msa_shared,
            c.consultant_nda_shared, c.consultant_msa_shared,
            (SELECT COUNT(*) FROM candidates WHERE job_requirement_id = r.id) as shared_count,
            (SELECT COUNT(*) FROM candidates WHERE job_requirement_id = r.id AND current_stage = 'Shortlisted') as shortlisted_count,
            (SELECT COUNT(*) FROM candidates WHERE job_requirement_id = r.id AND current_stage = '1st Round') as round1_count,
            (SELECT COUNT(*) FROM candidates WHERE job_requirement_id = r.id AND current_stage = '2nd Round') as round2_count,
            (SELECT COUNT(*) FROM candidates WHERE job_requirement_id = r.id AND current_stage = 'Final Selected') as selected_count
        FROM job_requirements r
        LEFT JOIN compliance_records c ON r.id = c.job_requirement_id
        ORDER BY r.id DESC
    """)
    rows = cursor.fetchall()

    cursor.execute("""
        SELECT c.*,
            (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id) as comments_count,
            (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id AND is_notification = 1) as notification_count
        FROM candidates c
        ORDER BY c.id ASC
    """)
    cand_rows = cursor.fetchall()
    cands_by_req = {}
    for cr in cand_rows:
        req_id = cr['job_requirement_id']
        if req_id not in cands_by_req:
            cands_by_req[req_id] = []
        cands_by_req[req_id].append(dict(cr))

    cursor.execute("""
        SELECT * FROM compliance_documents ORDER BY id DESC
    """)
    doc_rows = cursor.fetchall()
    docs_by_req = {}
    for dr in doc_rows:
        req_id = dr['job_requirement_id']
        if req_id not in docs_by_req:
            docs_by_req[req_id] = {}
        ag_type = dr['agreement_type']
        if ag_type not in docs_by_req[req_id]:
            d = dict(dr)
            if d.get('file_name'):
                d['download_url'] = f"/api/compliance/documents/{d['file_name']}"
            docs_by_req[req_id][ag_type] = d

    conn.close()

    result = []
    for row in rows:
        r_dict = dict(row)
        r_dict['candidates'] = cands_by_req.get(r_dict['id'], [])
        r_dict['compliance_docs'] = docs_by_req.get(r_dict['id'], {})
        
        # Calculate TAT
        tat_days, tat_display, tat_badge = calculate_tat(
            r_dict.get('open_date'),
            r_dict.get('close_date'),
            r_dict.get('status', 'Active'),
            r_dict.get('created_at')
        )
        r_dict['tat_days'] = tat_days
        r_dict['tat_display'] = tat_display
        r_dict['tat_badge'] = tat_badge
        if not r_dict.get('open_date'):
            r_dict['open_date'] = str(r_dict.get('created_at'))[:10] if r_dict.get('created_at') else date.today().isoformat()

        result.append(r_dict)

    return jsonify(result)

@app.route('/api/requirements', methods=['POST'])
def create_requirement():
    data = request.json or {}
    client_name = data.get('client_name')
    job_title = data.get('job_title')
    work_location_type = data.get('work_location_type', 'Hybrid')

    if not client_name or not job_title:
        return jsonify({'error': 'Client Name and Job Title are required.'}), 400

    open_date = data.get('open_date') or date.today().isoformat()
    close_date = data.get('close_date')
    status = data.get('status', 'Active')
    if status in ['Filled', 'Closed'] and not close_date:
        close_date = date.today().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    spoc_name = data.get('spoc_name', '').strip() if data.get('spoc_name') else ''
    spoc_mobile = data.get('spoc_mobile', '').strip() if data.get('spoc_mobile') else ''

    cursor.execute("""
        INSERT INTO job_requirements (client_name, end_client, spoc_name, spoc_mobile, job_title, job_description, work_location_type, location_city, budget, open_positions, status, open_date, close_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_name,
        data.get('end_client', ''),
        spoc_name,
        spoc_mobile,
        job_title,
        data.get('job_description', ''),
        work_location_type,
        data.get('location_city', ''),
        data.get('budget', ''),
        int(data.get('open_positions', 1)),
        status,
        open_date,
        close_date
    ))
    req_id = cursor.lastrowid

    # Create matching compliance record
    cursor.execute("""
        INSERT INTO compliance_records (job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        req_id,
        1 if data.get('client_nda_shared') else 0,
        1 if data.get('client_msa_shared') else 0,
        1 if data.get('vendor_nda_shared') else 0,
        1 if data.get('vendor_msa_shared') else 0,
        1 if data.get('consultant_nda_shared') else 0,
        1 if data.get('consultant_msa_shared') else 0
    ))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Requirement created successfully', 'id': req_id}), 201

@app.route('/api/requirements/<int:req_id>', methods=['GET'])
def get_single_requirement(req_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, c.client_nda_shared, c.client_msa_shared, c.vendor_nda_shared, c.vendor_msa_shared, c.consultant_nda_shared, c.consultant_msa_shared
        FROM job_requirements r
        LEFT JOIN compliance_records c ON r.id = c.job_requirement_id
        WHERE r.id = ?
    """, (req_id,))
    req_row = cursor.fetchone()

    if not req_row:
        conn.close()
        return jsonify({'error': 'Requirement not found'}), 404

    # Fetch candidates for this requirement
    cursor.execute("SELECT * FROM candidates WHERE job_requirement_id = ? ORDER BY id DESC", (req_id,))
    candidates = [dict(c) for c in cursor.fetchall()]

    conn.close()
    
    result = dict(req_row)
    result['candidates'] = candidates
    
    tat_days, tat_display, tat_badge = calculate_tat(
        result.get('open_date'),
        result.get('close_date'),
        result.get('status', 'Active'),
        result.get('created_at')
    )
    result['tat_days'] = tat_days
    result['tat_display'] = tat_display
    result['tat_badge'] = tat_badge
    if not result.get('open_date'):
        result['open_date'] = str(result.get('created_at'))[:10] if result.get('created_at') else date.today().isoformat()

    return jsonify(result)

@app.route('/api/requirements/<int:req_id>', methods=['PUT'])
def update_requirement(req_id):
    data = request.json or {}
    conn = get_db()
    try:
        cursor = conn.cursor()

        status = data.get('status', 'Active')
        open_date = data.get('open_date') or date.today().isoformat()
        close_date = data.get('close_date')
        if status in ['Filled', 'Closed'] and not close_date:
            close_date = date.today().isoformat()
        elif status in ['Active', 'On Hold']:
            close_date = None

        spoc_name = data.get('spoc_name', '').strip() if data.get('spoc_name') is not None else ''
        spoc_mobile = data.get('spoc_mobile', '').strip() if data.get('spoc_mobile') is not None else ''

        open_positions = data.get('open_positions')
        if open_positions is None or open_positions == '':
            open_positions = 1
        else:
            try:
                open_positions = int(open_positions)
            except (ValueError, TypeError):
                open_positions = 1

        cursor.execute("""
            UPDATE job_requirements
            SET client_name = ?, end_client = ?, spoc_name = ?, spoc_mobile = ?, job_title = ?, job_description = ?,
                work_location_type = ?, location_city = ?, budget = ?, open_positions = ?, 
                status = ?, open_date = ?, close_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('client_name'),
            data.get('end_client'),
            spoc_name,
            spoc_mobile,
            data.get('job_title'),
            data.get('job_description'),
            data.get('work_location_type', 'Hybrid'),
            data.get('location_city'),
            data.get('budget'),
            open_positions,
            status,
            open_date,
            close_date,
            req_id
        ))

        conn.commit()
        return jsonify({'message': 'Requirement updated successfully'})
    finally:
        conn.close()

@app.route('/api/requirements/<int:req_id>/status', methods=['PATCH', 'PUT'])
def update_requirement_status(req_id):
    data = request.json or {}
    new_status = data.get('status', 'Active')
    conn = get_db()
    cursor = conn.cursor()

    if new_status in ['Filled', 'Closed']:
        today_iso = date.today().isoformat()
        cursor.execute("UPDATE job_requirements SET status = ?, close_date = COALESCE(close_date, ?) WHERE id = ?", (new_status, today_iso, req_id))
    else:
        cursor.execute("UPDATE job_requirements SET status = ?, close_date = NULL WHERE id = ?", (new_status, req_id))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Requirement status updated successfully', 'status': new_status})

@app.route('/api/requirements/<int:req_id>/compliance', methods=['PUT'])
def update_compliance(req_id):
    data = request.json or {}
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO compliance_records (job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_requirement_id) DO UPDATE SET
            client_nda_shared = excluded.client_nda_shared,
            client_msa_shared = excluded.client_msa_shared,
            vendor_nda_shared = excluded.vendor_nda_shared,
            vendor_msa_shared = excluded.vendor_msa_shared,
            consultant_nda_shared = excluded.consultant_nda_shared,
            consultant_msa_shared = excluded.consultant_msa_shared,
            updated_at = CURRENT_TIMESTAMP
    """, (
        req_id,
        1 if data.get('client_nda_shared') else 0,
        1 if data.get('client_msa_shared') else 0,
        1 if data.get('vendor_nda_shared') else 0,
        1 if data.get('vendor_msa_shared') else 0,
        1 if data.get('consultant_nda_shared') else 0,
        1 if data.get('consultant_msa_shared') else 0
    ))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Compliance updated successfully'})

@app.route('/api/requirements/<int:req_id>/compliance/upload', methods=['POST'])
def upload_compliance_document(req_id):
    """Uploads a signed agreement document, captures uploader details and remark."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_name FROM job_requirements WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Requirement not found'}), 404
    conn.close()

    agreement_type = request.form.get('agreement_type', '').strip().lower()
    is_signed = request.form.get('is_signed', '1')
    is_signed = 1 if str(is_signed).lower() in ('1', 'true', 'yes', 'on') else 0
    remark = request.form.get('remark', '').strip()

    valid_types = {'client_nda', 'client_msa', 'vendor_nda', 'vendor_msa', 'consultant_nda', 'consultant_msa'}
    if agreement_type not in valid_types:
        return jsonify({'error': f'Invalid agreement type. Must be one of: {", ".join(sorted(valid_types))}'}), 400

    # Capture uploader identity from active session (or defaults)
    uploaded_by = session.get('full_name') or session.get('username') or 'System Administrator'
    uploaded_by_role = session.get('role') or 'Admin'

    file_name = None
    original_name = None
    file_path = None
    file_size = 0

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_COMPLIANCE_EXTENSIONS:
            return jsonify({'error': f'File type .{ext} not allowed. Supported formats: PDF, DOC, DOCX, TXT, PNG, JPG'}), 400

        original_name = secure_filename(file.filename) or file.filename
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = f"{agreement_type}_req_{req_id}_{timestamp_str}_{original_name}"
        file_path = os.path.join(COMPLIANCE_UPLOAD_FOLDER, safe_name)
        file.save(file_path)
        file_name = safe_name
        file_size = os.path.getsize(file_path)

    doc_id = save_compliance_document(
        req_id=req_id,
        agreement_type=agreement_type,
        is_signed=is_signed,
        file_name=file_name,
        original_name=original_name,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=uploaded_by,
        uploaded_by_role=uploaded_by_role,
        remark=remark
    )

    doc_record = {
        'id': doc_id,
        'job_requirement_id': req_id,
        'agreement_type': agreement_type,
        'is_signed': is_signed,
        'file_name': file_name,
        'original_name': original_name,
        'file_size': file_size,
        'download_url': f"/api/compliance/documents/{file_name}" if file_name else None,
        'uploaded_by': uploaded_by,
        'uploaded_by_role': uploaded_by_role,
        'remark': remark,
        'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify({
        'message': 'Compliance document and status saved successfully',
        'document': doc_record
    }), 201

@app.route('/api/compliance/documents/<path:filename>')
def serve_compliance_document(filename):
    """Serves uploaded compliance agreement files securely."""
    return send_from_directory(COMPLIANCE_UPLOAD_FOLDER, filename)

@app.route('/api/requirements/<int:req_id>/compliance/documents', methods=['GET'])
def get_req_compliance_documents(req_id):
    """Returns all compliance documents, uploaders, and remarks for a requirement."""
    docs = get_compliance_documents(req_id)
    for d in docs:
        if d.get('file_name'):
            d['download_url'] = f"/api/compliance/documents/{d['file_name']}"
    return jsonify(docs)

@app.route('/api/compliance/documents/<int:doc_id>', methods=['PUT', 'POST'])
def update_compliance_doc_endpoint(doc_id):
    """Updates remark, is_signed status, or replaces file for an existing compliance document."""
    remark = request.form.get('remark') if request.form else (request.json.get('remark') if request.is_json else None)
    is_signed_raw = request.form.get('is_signed') if request.form else (request.json.get('is_signed') if request.is_json else None)
    is_signed = None
    if is_signed_raw is not None:
        is_signed = 1 if str(is_signed_raw).lower() in ('1', 'true', 'yes', 'on') else 0

    agreement_type = request.form.get('agreement_type') if request.form else (request.json.get('agreement_type') if request.is_json else None)

    file_name = None
    original_name = None
    file_path = None
    file_size = None

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_COMPLIANCE_EXTENSIONS:
            return jsonify({'error': f'File type .{ext} not allowed.'}), 400
        original_name = secure_filename(file.filename) or file.filename
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = f"doc_{doc_id}_{timestamp_str}_{original_name}"
        file_path = os.path.join(COMPLIANCE_UPLOAD_FOLDER, safe_name)
        file.save(file_path)
        file_name = safe_name
        file_size = os.path.getsize(file_path)

    ok, msg = update_compliance_document(
        doc_id=doc_id,
        remark=remark,
        is_signed=is_signed,
        agreement_type=agreement_type,
        file_name=file_name,
        original_name=original_name,
        file_path=file_path,
        file_size=file_size
    )
    if not ok:
        return jsonify({'error': msg}), 404
    return jsonify({'message': 'Compliance document updated successfully', 'success': True})

@app.route('/api/compliance/documents/<int:doc_id>', methods=['DELETE'])
def delete_compliance_doc_endpoint(doc_id):
    """Deletes an existing compliance document."""
    ok, msg = delete_compliance_document(doc_id)
    if not ok:
        return jsonify({'error': msg}), 404
    return jsonify({'message': 'Compliance document deleted successfully', 'success': True})

@app.route('/api/requirements/<int:req_id>', methods=['DELETE'])
def delete_requirement(req_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM job_requirements WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Requirement deleted successfully'})

# -------------------------------------------------------------------
# CANDIDATES & RESUME API
# -------------------------------------------------------------------
@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    req_id = request.args.get('job_requirement_id')
    conn = get_db()
    cursor = conn.cursor()

    if req_id:
        cursor.execute("""
            SELECT c.*, r.job_title, r.client_name,
                (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id) as comments_count,
                (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id AND is_notification = 1) as notification_count,
                (SELECT comment_text FROM candidate_comments WHERE candidate_id = c.id ORDER BY id DESC LIMIT 1) as latest_comment
            FROM candidates c
            JOIN job_requirements r ON c.job_requirement_id = r.id
            WHERE c.job_requirement_id = ?
            ORDER BY c.id DESC
        """, (req_id,))
    else:
        cursor.execute("""
            SELECT c.*, r.job_title, r.client_name,
                (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id) as comments_count,
                (SELECT COUNT(*) FROM candidate_comments WHERE candidate_id = c.id AND is_notification = 1) as notification_count,
                (SELECT comment_text FROM candidate_comments WHERE candidate_id = c.id ORDER BY id DESC LIMIT 1) as latest_comment
            FROM candidates c
            JOIN job_requirements r ON c.job_requirement_id = r.id
            ORDER BY c.id DESC
        """)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/candidates', methods=['POST'])
def create_candidate():
    is_json = request.is_json
    data = request.get_json(silent=True) or {}
    get_val = (lambda k, default='': data.get(k, default)) if is_json else (lambda k, default='': request.form.get(k, default))

    candidate_name = get_val('candidate_name')
    job_requirement_id = get_val('job_requirement_id')

    if not candidate_name or not job_requirement_id:
        return jsonify({'error': 'Candidate Name and Job Requirement ID are required'}), 400

    email = get_val('email', '')
    phone = get_val('phone', '')
    current_stage = get_val('current_stage', 'Profile Shared')
    doj = get_val('doj', '')
    final_billing_rate = get_val('final_billing_rate', '')
    consultant_pay_rate = get_val('consultant_pay_rate', '')

    # Sourcing fields
    source_type = get_val('source_type', 'Internal')
    current_ctc = get_val('current_ctc', '')
    expected_ctc = get_val('expected_ctc', '')
    notice_period = get_val('notice_period', '')
    current_location = get_val('current_location', '')
    remarks = get_val('remarks', '')
    vendor_name = get_val('vendor_name', '')
    vendor_billing_rate = get_val('vendor_billing_rate', '')
    current_company = get_val('current_company', '')
    office_work_type = get_val('office_work_type', '')

    resume_filename = ''
    resume_original_name = ''
    file_bytes = None

    if not is_json and 'resume' in request.files:
        file = request.files['resume']
        if file and allowed_file(file.filename):
            orig_name = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            saved_filename = f"{timestamp}_{orig_name}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
            file_bytes = file.read()
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            resume_filename = saved_filename
            resume_original_name = file.filename

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO candidates (
            job_requirement_id, candidate_name, email, phone, current_stage, doj, 
            final_billing_rate, consultant_pay_rate, resume_filename, resume_original_name,
            source_type, current_ctc, expected_ctc, notice_period, current_location, 
            remarks, vendor_name, vendor_billing_rate, current_company, office_work_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_requirement_id, candidate_name, email, phone, current_stage, doj, 
        final_billing_rate, consultant_pay_rate, resume_filename, resume_original_name,
        source_type, current_ctc, expected_ctc, notice_period, current_location, 
        remarks, vendor_name, vendor_billing_rate, current_company, office_work_type
    ))

    cand_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Also store directly in database 'resumes' table
    if resume_filename:
        save_resume_to_db(job_requirement_id, cand_id, resume_filename, resume_original_name, file_bytes, os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))

    return jsonify({'message': 'Candidate profile created successfully', 'id': cand_id}), 201

@app.route('/api/candidates/<int:cand_id>', methods=['PUT'])
def update_candidate(cand_id):
    conn = get_db()
    cursor = conn.cursor()

    is_json = request.is_json
    data = request.get_json(silent=True) or {}
    get_val = (lambda k, default='': data.get(k, default)) if is_json else (lambda k, default='': request.form.get(k, default))

    candidate_name = get_val('candidate_name')
    current_stage = get_val('current_stage')
    doj = get_val('doj', '')
    final_billing_rate = get_val('final_billing_rate', '')
    consultant_pay_rate = get_val('consultant_pay_rate', '')
    email = get_val('email', '')
    phone = get_val('phone', '')

    source_type = get_val('source_type', 'Internal')
    current_ctc = get_val('current_ctc', '')
    expected_ctc = get_val('expected_ctc', '')
    notice_period = get_val('notice_period', '')
    current_location = get_val('current_location', '')
    remarks = get_val('remarks', '')
    vendor_name = get_val('vendor_name', '')
    vendor_billing_rate = get_val('vendor_billing_rate', '')
    current_company = get_val('current_company', '')
    office_work_type = get_val('office_work_type', '')

    saved_filename = None
    orig_filename = None
    file_bytes = None

    if not is_json and 'resume' in request.files:
        file = request.files['resume']
        if file and allowed_file(file.filename):
            orig_name = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            saved_filename = f"{timestamp}_{orig_name}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
            file_bytes = file.read()
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            orig_filename = file.filename

    if saved_filename:
        cursor.execute("""
            UPDATE candidates
            SET candidate_name = ?, current_stage = ?, doj = ?, final_billing_rate = ?, consultant_pay_rate = ?, email = ?, phone = ?,
                source_type = ?, current_ctc = ?, expected_ctc = ?, notice_period = ?, current_location = ?,
                remarks = ?, vendor_name = ?, vendor_billing_rate = ?, current_company = ?, office_work_type = ?,
                resume_filename = ?, resume_original_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            candidate_name, current_stage, doj, final_billing_rate, consultant_pay_rate, email, phone,
            source_type, current_ctc, expected_ctc, notice_period, current_location,
            remarks, vendor_name, vendor_billing_rate, current_company, office_work_type,
            saved_filename, orig_filename, cand_id
        ))
        cursor.execute("SELECT job_requirement_id FROM candidates WHERE id = ?", (cand_id,))
        req_row = cursor.fetchone()
        req_id = req_row[0] if req_row else 1
        save_resume_to_db(req_id, cand_id, saved_filename, orig_filename, file_bytes, os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))
    else:
        cursor.execute("""
            UPDATE candidates
            SET candidate_name = ?, current_stage = ?, doj = ?, final_billing_rate = ?, consultant_pay_rate = ?, email = ?, phone = ?,
                source_type = ?, current_ctc = ?, expected_ctc = ?, notice_period = ?, current_location = ?,
                remarks = ?, vendor_name = ?, vendor_billing_rate = ?, current_company = ?, office_work_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            candidate_name, current_stage, doj, final_billing_rate, consultant_pay_rate, email, phone,
            source_type, current_ctc, expected_ctc, notice_period, current_location,
            remarks, vendor_name, vendor_billing_rate, current_company, office_work_type,
            cand_id
        ))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Candidate updated successfully'})

@app.route('/api/candidates/<int:cand_id>/stage', methods=['PATCH', 'PUT'])
def update_candidate_stage(cand_id):
    data = request.json or {}
    new_stage = data.get('current_stage') or data.get('stage')
    if not new_stage:
        return jsonify({'error': 'current_stage is required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE candidates
        SET current_stage = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_stage, cand_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Candidate stage updated successfully', 'current_stage': new_stage})

@app.route('/api/candidates/<int:cand_id>/resume', methods=['POST'])
def upload_resume(cand_id):
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        orig_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_filename = f"{timestamp}_{orig_name}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file_bytes = file.read()
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE candidates
            SET resume_filename = ?, resume_original_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (saved_filename, file.filename, cand_id))

        cursor.execute("SELECT job_requirement_id FROM candidates WHERE id = ?", (cand_id,))
        req_row = cursor.fetchone()
        req_id = req_row[0] if req_row else 1
        conn.commit()
        conn.close()

        # Save to database resumes table
        save_resume_to_db(req_id, cand_id, saved_filename, file.filename, file_bytes, file_path)

        return jsonify({'message': 'Resume uploaded successfully', 'resume_filename': saved_filename})
    
    return jsonify({'error': 'Invalid file format. Allowed: pdf, doc, docx, txt'}), 400

@app.route('/api/resumes/<filename>', methods=['GET'])
def get_resume_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

@app.route('/api/candidates/<int:cand_id>', methods=['DELETE'])
def delete_candidate(cand_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id = ?", (cand_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Candidate deleted successfully'})

# -------------------------------------------------------------------
# CANDIDATE PROFILE COMMENTS & MANAGER NOTIFICATIONS API
# -------------------------------------------------------------------
@app.route('/api/candidates/<int:cand_id>/comments', methods=['GET'])
def get_comments_for_candidate(cand_id):
    comments = get_candidate_comments(cand_id)
    return jsonify(comments)

@app.route('/api/candidates/<int:cand_id>/comments', methods=['POST'])
def create_comment_for_candidate(cand_id):
    data = request.json or {}
    comment_text = data.get('comment_text', '').strip()
    if not comment_text:
        return jsonify({'error': 'Comment or notification text is required.'}), 400

    session_user_id = session.get('user_id')
    author_name = session.get('full_name') or session.get('username') or data.get('author_name', 'Hiring Manager')
    author_role = session.get('role') or data.get('author_role', 'Manager')
    comment_type = data.get('comment_type', 'Comment')
    is_notification = 1 if data.get('is_notification') or comment_type in ['Notification', 'Action Required'] else 0

    comment_id = add_candidate_comment(
        candidate_id=cand_id,
        author_name=author_name,
        author_role=author_role,
        comment_text=comment_text,
        comment_type=comment_type,
        is_notification=is_notification,
        author_user_id=session_user_id
    )

    return jsonify({
        'success': True,
        'message': 'Comment / notification posted successfully',
        'id': comment_id,
        'comment': {
            'id': comment_id,
            'candidate_id': cand_id,
            'author_name': author_name,
            'author_role': author_role,
            'comment_type': comment_type,
            'comment_text': comment_text,
            'is_notification': is_notification,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201

@app.route('/api/notifications', methods=['GET'])
def list_notifications():
    limit = request.args.get('limit', 30, type=int)
    notifications = get_recent_notifications(limit)
    return jsonify(notifications)

# -------------------------------------------------------------------
# DATABASE MANAGEMENT & EXPORT APIs
# -------------------------------------------------------------------
@app.route('/api/database/stats', methods=['GET'])
def api_database_stats():
    stats = get_database_stats()
    return jsonify(stats)

@app.route('/api/database/table/<table_name>', methods=['GET'])
def api_database_table(table_name):
    limit = request.args.get('limit', 100, type=int)
    rows = get_table_rows(table_name, limit)
    return jsonify(rows)

@app.route('/api/database/download-db', methods=['GET'])
def api_download_db():
    if not os.path.exists(DB_PATH):
        return jsonify({'error': 'Database file not found'}), 404
    return send_file(DB_PATH, as_attachment=True, download_name='recruitment_tracker.db')

@app.route('/api/download/project-zip', methods=['GET'])
def api_download_project_zip():
    zip_path = os.path.join(os.path.dirname(__file__), 'job-requirement-tracker.zip')
    if not os.path.exists(zip_path):
        return jsonify({'error': 'Project ZIP file not found'}), 404
    return send_file(zip_path, as_attachment=True, download_name='job-requirement-tracker.zip')

@app.route('/api/database/export-sql', methods=['GET'])
def api_export_sql():
    sql_content = export_database_to_sql()
    return Response(
        sql_content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=recruitment_tracker_backup.sql"}
    )

@app.route('/api/database/schema/<schema_type>', methods=['GET'])
def api_get_schema_file(schema_type):
    file_map = {
        'sqlite': 'schema.sql',
        'mysql': 'schema_mysql.sql',
        'postgres': 'schema_postgres.sql',
        'seeds': 'seeds.sql'
    }
    target = file_map.get(schema_type.lower())
    if not target:
        return jsonify({'error': 'Invalid schema type'}), 400
    
    file_path = os.path.join(os.path.dirname(__file__), target)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return jsonify({'filename': target, 'content': content})

# -------------------------------------------------------------------
# MANAGEMENT REPORTS API
# -------------------------------------------------------------------
def extract_number(val):
    if not val:
        return 0.0
    cleaned = ''.join(c for c in str(val) if c.isdigit() or c == '.')
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

@app.route('/api/reports/management', methods=['GET'])
def get_management_report():
    conn = get_db()
    cursor = conn.cursor()

    # 1. High-level Summary Metrics
    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_resumes_shared = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates WHERE current_stage = 'Shortlisted'")
    total_shortlisted = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates WHERE current_stage IN ('1st Round', '2nd Round')")
    total_in_interviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates WHERE current_stage = 'Final Selected'")
    total_selected = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(open_positions), 0) FROM job_requirements")
    total_requirements, total_positions = cursor.fetchone()

    # 2. Client-by-Client Performance & Billing Breakdown
    cursor.execute("""
        SELECT 
            r.client_name,
            COUNT(DISTINCT r.id) as req_count,
            COALESCE(SUM(r.open_positions), 0) as total_openings,
            (SELECT COUNT(*) FROM candidates c JOIN job_requirements r2 ON c.job_requirement_id = r2.id WHERE r2.client_name = r.client_name) as resumes_shared,
            (SELECT COUNT(*) FROM candidates c JOIN job_requirements r2 ON c.job_requirement_id = r2.id WHERE r2.client_name = r.client_name AND c.current_stage = 'Shortlisted') as shortlisted_count,
            (SELECT COUNT(*) FROM candidates c JOIN job_requirements r2 ON c.job_requirement_id = r2.id WHERE r2.client_name = r.client_name AND c.current_stage = 'Final Selected') as closed_positions,
            GROUP_CONCAT(DISTINCT r.end_client) as end_clients
        FROM job_requirements r
        GROUP BY r.client_name
        ORDER BY req_count DESC, closed_positions DESC
    """)
    client_rows = cursor.fetchall()
    client_reports = []

    total_billed_numeric = 0.0
    total_paid_numeric = 0.0

    for crow in client_rows:
        cname = crow['client_name']
        cursor.execute("""
            SELECT c.final_billing_rate, c.consultant_pay_rate 
            FROM candidates c 
            JOIN job_requirements r ON c.job_requirement_id = r.id 
            WHERE r.client_name = ? AND c.current_stage = 'Final Selected'
        """, (cname,))
        placed_cands = cursor.fetchall()
        
        client_billing_list = [p['final_billing_rate'] for p in placed_cands if p['final_billing_rate']]
        client_billing_summary = ", ".join(client_billing_list) if client_billing_list else "None yet"

        client_billing_sum = 0.0
        client_pay_sum = 0.0
        for p in placed_cands:
            b_val = extract_number(p['final_billing_rate'])
            p_val = extract_number(p['consultant_pay_rate'])
            client_billing_sum += b_val
            client_pay_sum += p_val
            total_billed_numeric += b_val
            total_paid_numeric += p_val

        total_openings = crow['total_openings']
        closed_positions = crow['closed_positions']
        closure_rate = round((closed_positions / total_openings * 100), 1) if total_openings > 0 else 0

        client_reports.append({
            'client_name': cname,
            'end_clients': crow['end_clients'] or 'Direct',
            'requirements_count': crow['req_count'],
            'total_openings': total_openings,
            'resumes_shared': crow['resumes_shared'],
            'shortlisted_count': crow['shortlisted_count'],
            'closed_positions': closed_positions,
            'closure_rate_percent': closure_rate,
            'billing_rates': client_billing_list,
            'billing_summary': client_billing_summary,
            'billing_sum': client_billing_sum,
            'pay_sum': client_pay_sum,
            'margin_sum': round(client_billing_sum - client_pay_sum, 2)
        })

    # 3. Consultant Placement & Compensation Report (which consultant what we pay)
    cursor.execute("""
        SELECT 
            c.id, c.candidate_name, c.email, c.phone, c.doj, 
            c.final_billing_rate, c.consultant_pay_rate,
            r.job_title, r.client_name, r.end_client
        FROM candidates c
        JOIN job_requirements r ON c.job_requirement_id = r.id
        WHERE c.current_stage = 'Final Selected'
        ORDER BY c.doj DESC, c.id DESC
    """)
    consultant_rows = cursor.fetchall()
    consultants_report = []

    for cr in consultant_rows:
        bill_val = extract_number(cr['final_billing_rate'])
        pay_val = extract_number(cr['consultant_pay_rate'])
        margin_val = round(bill_val - pay_val, 2) if (bill_val and pay_val) else 0.0
        consultants_report.append({
            'candidate_id': cr['id'],
            'consultant_name': cr['candidate_name'],
            'email': cr['email'],
            'phone': cr['phone'],
            'job_title': cr['job_title'],
            'client_name': cr['client_name'],
            'end_client': cr['end_client'] or 'N/A',
            'doj': cr['doj'] or 'TBD',
            'client_billing_rate': cr['final_billing_rate'] or 'N/A',
            'consultant_pay_rate': cr['consultant_pay_rate'] or 'N/A',
            'margin_estimated': f"${margin_val}/hr" if margin_val > 0 else "N/A"
        })

    overall_closure_rate = round((total_selected / total_positions * 100), 1) if total_positions > 0 else 0

    conn.close()

    return jsonify({
        'summary': {
            'total_resumes_shared': total_resumes_shared,
            'total_shortlisted': total_shortlisted,
            'total_in_interviews': total_in_interviews,
            'total_selected': total_selected,
            'total_requirements': total_requirements,
            'total_positions': total_positions,
            'overall_closure_rate': overall_closure_rate,
            'total_billed_hourly': round(total_billed_numeric, 2),
            'total_paid_hourly': round(total_paid_numeric, 2),
            'total_margin_hourly': round(total_billed_numeric - total_paid_numeric, 2)
        },
        'client_reports': client_reports,
        'consultants_report': consultants_report
    })

# -------------------------------------------------------------------
# ADMIN PANEL: USER & MANAGER MANAGEMENT & ROLE/RIGHTS
# -------------------------------------------------------------------
def is_admin_authorized():
    """Checks if the current session has administrative authorization."""
    role = session.get('role')
    rights = session.get('rights') or {}
    return role == 'Admin' or bool(rights.get('can_access_admin'))

@app.route('/api/admin/users', methods=['GET'])
def admin_list_users():
    """Lists all registered users with their roles, emails, and rights."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    users = get_all_users()
    return jsonify(users)

@app.route('/api/admin/users', methods=['POST'])
def admin_create_user():
    """Creates a new User or Manager account with assigned rights."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'User')
    full_name = data.get('full_name', '').strip() or None
    rights = data.get('rights')
    status = data.get('status', 'Active')

    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    if not password:
        return jsonify({'error': 'Password is required.'}), 400

    # Auto-assign default rights if not provided
    if not rights or not isinstance(rights, dict):
        rights = get_default_rights(role)

    user_id, msg = create_user(username, email, password, role, full_name, rights, status)
    if not user_id:
        return jsonify({'error': msg}), 400

    new_user = get_user_by_id(user_id)
    return jsonify({
        'message': msg,
        'user': new_user
    }), 201

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def admin_update_user_endpoint(user_id):
    """Updates user roles, corporate email, full name, rights, and status."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    data = request.json or {}
    email = data.get('email')
    full_name = data.get('full_name')
    role = data.get('role')
    rights = data.get('rights')
    status = data.get('status')

    success, msg = update_user(user_id, email, full_name, role, rights, status)
    if not success:
        return jsonify({'error': msg}), 400

    updated_user = get_user_by_id(user_id)
    if session.get('user_id') == user_id and updated_user:
        session['role'] = updated_user.get('role', session.get('role'))
        session['full_name'] = updated_user.get('full_name', session.get('full_name'))
        session['rights'] = updated_user.get('rights', session.get('rights'))

    return jsonify({
        'message': msg,
        'user': updated_user
    })

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
def admin_reset_password_endpoint(user_id):
    """Resets user password directly from admin panel."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    data = request.json or {}
    new_password = data.get('new_password', '').strip()
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400

    success, msg = admin_reset_user_password(user_id, new_password)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user_endpoint(user_id):
    """Deletes a user account (with protection for primary admin)."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    if session.get('user_id') == user_id:
        return jsonify({'error': 'You cannot delete your own active administrator account.'}), 400

    success, msg = delete_user(user_id)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg})

# ==========================================
# SYSTEM SETTINGS API (CURRENCY / EXCHANGE RATE)
# ==========================================
@app.route('/api/settings', methods=['GET'])
def get_settings_endpoint():
    """Returns system settings including USD/INR exchange rate."""
    return jsonify(get_all_system_settings())

@app.route('/api/settings', methods=['PUT'])
def update_settings_endpoint():
    """Updates system settings like usd_inr_exchange_rate (Admin only)."""
    if not is_admin_authorized():
        return jsonify({'error': 'Unauthorized. Administrator privileges required.'}), 403

    data = request.json or {}
    for key, value in data.items():
        set_system_setting(key, value)

    return jsonify({
        'message': 'System settings updated successfully.',
        'settings': get_all_system_settings()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Job Requirement Tracker server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)

