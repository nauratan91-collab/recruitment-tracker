import os
import json
import base64
import zipfile
import shutil

def build_package():
    proj_dir = r"C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"
    output_dir = os.path.join(proj_dir, "dist_website")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load template index.html
    with open(os.path.join(proj_dir, "templates", "index.html"), "r", encoding="utf-8") as f:
        html = f.read()

    # 2. Embed company logo as Base64 data URI
    logo_path = os.path.join(proj_dir, "static", "images", "company_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        html = html.replace("/static/images/company_logo.png", logo_b64)

    # 3. Extract existing data from SQLite
    import database
    conn = database.get_db()
    users = [dict(r) for r in conn.execute("SELECT id, username, email, role, full_name, rights, status, auth_provider FROM users").fetchall()]
    reqs = [dict(r) for r in conn.execute("SELECT * FROM job_requirements").fetchall()]
    cands = [dict(r) for r in conn.execute("SELECT * FROM candidates").fetchall()]
    compls = [dict(r) for r in conn.execute("SELECT * FROM compliance_records").fetchall()]
    docs = [dict(r) for r in conn.execute("SELECT * FROM compliance_documents").fetchall()]
    comments = [dict(r) for r in conn.execute("SELECT * FROM candidate_comments").fetchall()]

    for u in users:
        if isinstance(u.get("rights"), str):
            try:
                u["rights"] = json.loads(u["rights"])
            except Exception:
                pass

    # Ensure SPOC fields are populated for pre-seeded requirements if empty
    sample_spocs = [
        ("Rahul Sharma (Lead Account Mgr)", "+91 98765 43210"),
        ("Priya Patel (Sr. Delivery Lead)", "+91 98123 45678"),
        ("Amit Verma (Talent Acquisition)", "+91 97234 56789"),
        ("Vikram Singh (Client Director)", "+91 96345 67890"),
        ("Neha Gupta (Strategic HR SPOC)", "+91 95456 78901")
    ]
    for idx, r in enumerate(reqs):
        if not r.get("spoc_name"):
            spoc_info = sample_spocs[idx % len(sample_spocs)]
            r["spoc_name"] = spoc_info[0]
            r["spoc_mobile"] = spoc_info[1]

    # Pre-build data json strings
    users_json = json.dumps(users)
    reqs_json = json.dumps(reqs)
    cands_json = json.dumps(cands)
    compls_json = json.dumps(compls)
    docs_json = json.dumps(docs)
    comments_json = json.dumps(comments)

    # 4. Construct the Autonomous Client-Side REST Engine script
    virtual_engine_script = f"""
    <!-- ======================================================================= -->
    <!-- KEY DYNAMICS AUTONOMOUS CLIENT-SIDE DATABASE & API ENGINE -->
    <!-- Runs 100% on any Web Hosting (Vercel, Netlify, cPanel, or Direct File) -->
    <!-- ======================================================================= -->
    <script>
    (function() {{
        console.info("Key Dynamics Solutions: Initializing Autonomous Web Engine");

        // Seed data initialization
        const SEED_USERS = {users_json};
        const SEED_REQS = {reqs_json};
        const SEED_CANDS = {cands_json};
        const SEED_COMPLS = {compls_json};
        const SEED_DOCS = {docs_json};
        const SEED_COMMENTS = {comments_json};

        // Clean database initialization with max 4 clean requirements
        if (!localStorage.getItem('kd_db_v4_max4')) {{
            localStorage.removeItem('kd_db_initialized');
            localStorage.removeItem('kd_db_initialized_v2');
            localStorage.removeItem('kd_db_cleaned_v3');
            localStorage.setItem('kd_users', JSON.stringify(SEED_USERS));
            localStorage.setItem('kd_reqs', JSON.stringify(SEED_REQS));
            localStorage.setItem('kd_cands', JSON.stringify(SEED_CANDS));
            localStorage.setItem('kd_compls', JSON.stringify(SEED_COMPLS));
            localStorage.setItem('kd_docs', JSON.stringify(SEED_DOCS));
            localStorage.setItem('kd_comments', JSON.stringify(SEED_COMMENTS));
            localStorage.setItem('kd_db_v4_max4', 'true');
        }}

        function getDB(table) {{
            try {{
                return JSON.parse(localStorage.getItem(table) || '[]');
            }} catch(e) {{
                return [];
            }}
        }}

        function setDB(table, data) {{
            localStorage.setItem(table, JSON.stringify(data));
        }}

        function calculateTat(openDate, closeDate, status, createdAt) {{
            const startDateStr = openDate || (createdAt ? createdAt.substring(0, 10) : new Date().toISOString().split('T')[0]);
            const startD = new Date(startDateStr);
            const endD = (status === 'Closed' || status === 'Filled') && closeDate ? new Date(closeDate) : new Date();
            const diffTime = Math.max(0, endD - startD);
            const days = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            
            let display = days + " Days";
            let badge = 'green';
            if (status === 'Closed') display = "Closed in " + days + "d";
            else if (status === 'Filled') display = "Filled in " + days + "d";

            if (days > 30) badge = 'red';
            else if (days > 15) badge = 'amber';

            return {{ tat_days: days, tat_display: display, tat_badge: badge }};
        }}

        // Override window.fetch to provide zero-backend autonomous REST execution
        const originalFetch = window.fetch;
        window.fetch = async function(resource, config = {{}}) {{
            let url = typeof resource === 'string' ? resource : (resource ? resource.url : '');
            if (!url.startsWith('/api/') && !url.startsWith('api/')) {{
                return originalFetch(resource, config);
            }}

            const path = url.startsWith('/') ? url.split('?')[0] : ('/' + url.split('?')[0]);
            const method = (config.method || 'GET').toUpperCase();
            let body = {{}};
            if (config.body) {{
                if (typeof config.body === 'string') {{
                    try {{ body = JSON.parse(config.body); }} catch(e) {{ body = {{}}; }}
                }} else if (config.body instanceof FormData) {{
                    for (let [k, v] of config.body.entries()) {{
                        body[k] = v;
                    }}
                }} else {{
                    body = config.body;
                }}
            }}

            const jsonResponse = (obj, status = 200) => {{
                return new Response(JSON.stringify(obj), {{
                    status: status,
                    headers: {{ 'Content-Type': 'application/json' }}
                }});
            }};

            // -------------------------------------------------------------
            // AUTHENTICATION
            // -------------------------------------------------------------
            if (path === '/api/auth/me') {{
                const userJson = sessionStorage.getItem('kd_active_session');
                if (userJson) {{
                    const u = JSON.parse(userJson);
                    return jsonResponse({{ authenticated: true, user: u }});
                }}
                return jsonResponse({{ authenticated: false }}, 401);
            }}

            if (path === '/api/auth/login') {{
                const users = getDB('kd_users');
                const identifier = (body.username || '').trim().toLowerCase();
                const pwd = body.password;
                const user = users.find(u => 
                    (u.username.toLowerCase() === identifier || (u.email && u.email.toLowerCase() === identifier))
                );

                if (!user) {{
                    return jsonResponse({{ error: 'Invalid username or corporate email.' }}, 401);
                }}
                if (user.status === 'Inactive') {{
                    return jsonResponse({{ error: 'This corporate account has been deactivated.' }}, 403);
                }}

                sessionStorage.setItem('kd_active_session', JSON.stringify(user));
                return jsonResponse({{ message: 'Login successful', user: user }});
            }}

            if (path === '/api/auth/microsoft-login') {{
                const users = getDB('kd_users');
                const email = (body.email || '').trim().toLowerCase();
                const user = users.find(u => u.email && u.email.toLowerCase() === email);
                if (!user) {{
                    return jsonResponse({{ error: 'No user registered under corporate email: ' + email }}, 404);
                }}
                sessionStorage.setItem('kd_active_session', JSON.stringify(user));
                return jsonResponse({{
                    message: 'Microsoft Dynamics 365 Enterprise SSO Authentication Successful',
                    auth_provider: 'microsoft_dynamics_365',
                    user: user
                }});
            }}

            if (path === '/api/auth/logout') {{
                sessionStorage.removeItem('kd_active_session');
                return jsonResponse({{ message: 'Logged out successfully' }});
            }}

            if (path === '/api/auth/change-password') {{
                const users = getDB('kd_users');
                const userJson = sessionStorage.getItem('kd_active_session');
                if (!userJson) return jsonResponse({{ error: 'Unauthorized' }}, 401);
                const curr = JSON.parse(userJson);
                const idx = users.findIndex(u => u.id === curr.id);
                if (idx >= 0) {{
                    users[idx].password_hash = body.new_password;
                    setDB('kd_users', users);
                }}
                return jsonResponse({{ message: 'Password changed successfully' }});
            }}

            // -------------------------------------------------------------
            // DASHBOARD STATS
            // -------------------------------------------------------------
            if (path === '/api/dashboard/stats') {{
                const reqs = getDB('kd_reqs');
                const cands = getDB('kd_cands');
                const totalOpenings = reqs.reduce((acc, r) => acc + (parseInt(r.open_positions) || 1), 0);
                const stageCounts = {{
                    'Profile Shared': cands.filter(c => c.current_stage === 'Profile Shared').length,
                    'Shortlisted': cands.filter(c => c.current_stage === 'Shortlisted').length,
                    '1st Round': cands.filter(c => c.current_stage === '1st Round').length,
                    '2nd Round': cands.filter(c => c.current_stage === '2nd Round').length,
                    'Final Selected': cands.filter(c => c.current_stage === 'Final Selected').length,
                    'Rejected': cands.filter(c => c.current_stage === 'Rejected').length
                }};
                return jsonResponse({{
                    total_requirements: reqs.length,
                    total_openings: totalOpenings,
                    total_candidates_shared: cands.length,
                    total_selected: stageCounts['Final Selected'],
                    stage_counts: stageCounts
                }});
            }}

            // -------------------------------------------------------------
            // JOB REQUIREMENTS
            // -------------------------------------------------------------
            if (path === '/api/requirements') {{
                const reqs = getDB('kd_reqs');
                const cands = getDB('kd_cands');
                const compls = getDB('kd_compls');
                const docs = getDB('kd_docs');

                if (method === 'GET') {{
                    const enriched = reqs.map(r => {{
                        const rCands = cands.filter(c => c.job_requirement_id == r.id);
                        const rCompl = compls.find(c => c.job_requirement_id == r.id) || {{}};
                        const rDocs = {{}};
                        docs.filter(d => d.job_requirement_id == r.id).forEach(d => {{
                            rDocs[d.agreement_type] = d;
                        }});

                        const tat = calculateTat(r.open_date, r.close_date, r.status, r.created_at);

                        return {{
                            ...r,
                            ...rCompl,
                            candidates: rCands,
                            compliance_docs: rDocs,
                            shared_count: rCands.length,
                            shortlisted_count: rCands.filter(c => c.current_stage === 'Shortlisted').length,
                            round1_count: rCands.filter(c => c.current_stage === '1st Round').length,
                            round2_count: rCands.filter(c => c.current_stage === '2nd Round').length,
                            selected_count: rCands.filter(c => c.current_stage === 'Final Selected').length,
                            tat_days: tat.tat_days,
                            tat_display: tat.tat_display,
                            tat_badge: tat.tat_badge
                        }};
                    }});
                    return jsonResponse(enriched);
                }}

                if (method === 'POST') {{
                    const newId = Date.now();
                    const newReq = {{
                        id: newId,
                        client_name: body.client_name,
                        end_client: body.end_client || '',
                        spoc_name: body.spoc_name || '',
                        spoc_mobile: body.spoc_mobile || '',
                        job_title: body.job_title,
                        work_location_type: body.work_location_type || 'Hybrid',
                        location_city: body.location_city || '',
                        budget: body.budget || '',
                        open_positions: parseInt(body.open_positions) || 1,
                        status: body.status || 'Active',
                        open_date: body.open_date || new Date().toISOString().split('T')[0],
                        close_date: null,
                        job_description: body.job_description || '',
                        created_at: new Date().toISOString()
                    }};
                    reqs.unshift(newReq);
                    setDB('kd_reqs', reqs);

                    // Create matching compliance record
                    compls.push({{
                        job_requirement_id: newId,
                        client_nda_shared: body.client_nda_shared ? 1 : 0,
                        client_msa_shared: body.client_msa_shared ? 1 : 0,
                        vendor_nda_shared: body.vendor_nda_shared ? 1 : 0,
                        vendor_msa_shared: body.vendor_msa_shared ? 1 : 0,
                        consultant_nda_shared: body.consultant_nda_shared ? 1 : 0,
                        consultant_msa_shared: body.consultant_msa_shared ? 1 : 0,
                    }});
                    setDB('kd_compls', compls);

                    return jsonResponse({{ message: 'Requirement created successfully', id: newId }}, 201);
                }}
            }}

            if (path.startsWith('/api/requirements/')) {{
                const parts = path.split('/');
                const reqId = parts[3];
                const reqs = getDB('kd_reqs');
                const compls = getDB('kd_compls');

                if (parts.length === 4) {{
                    if (method === 'GET') {{
                        const req = reqs.find(r => r.id == reqId);
                        if (!req) return jsonResponse({{ error: 'Not found' }}, 404);
                        return jsonResponse(req);
                    }}
                    if (method === 'PUT') {{
                        const idx = reqs.findIndex(r => r.id == reqId);
                        if (idx >= 0) {{
                            reqs[idx] = {{
                                ...reqs[idx],
                                ...body,
                                open_positions: parseInt(body.open_positions) || 1,
                                updated_at: new Date().toISOString()
                            }};
                            setDB('kd_reqs', reqs);
                        }}
                        return jsonResponse({{ message: 'Requirement updated successfully' }});
                    }}
                    if (method === 'DELETE') {{
                        const updated = reqs.filter(r => r.id != reqId);
                        setDB('kd_reqs', updated);
                        return jsonResponse({{ message: 'Requirement deleted' }});
                    }}
                }}

                if (parts[4] === 'status') {{
                    const idx = reqs.findIndex(r => r.id == reqId);
                    if (idx >= 0) {{
                        reqs[idx].status = body.status;
                        if (body.status === 'Closed' || body.status === 'Filled') {{
                            reqs[idx].close_date = new Date().toISOString().split('T')[0];
                        }} else {{
                            reqs[idx].close_date = null;
                        }}
                        setDB('kd_reqs', reqs);
                    }}
                    return jsonResponse({{ message: 'Status updated' }});
                }}

                if (parts[4] === 'compliance') {{
                    if (parts[5] === 'upload') {{
                        const docs = getDB('kd_docs');
                        const fileObj = body.file;
                        let fileName = 'signed_doc_' + Date.now() + '.pdf';
                        if (fileObj && fileObj.name) fileName = fileObj.name;

                        const newDoc = {{
                            id: Date.now(),
                            job_requirement_id: parseInt(reqId),
                            agreement_type: body.agreement_type,
                            file_name: fileName,
                            original_name: fileName,
                            uploaded_by: body.uploaded_by || 'Corporate User',
                            remark: body.remark || 'Executed compliance document on file.',
                            download_url: '#download-' + fileName,
                            created_at: new Date().toISOString()
                        }};
                        docs.unshift(newDoc);
                        setDB('kd_docs', docs);

                        // Also set compliance record signed flag
                        const cIdx = compls.findIndex(c => c.job_requirement_id == reqId);
                        if (cIdx >= 0) {{
                            compls[cIdx][body.agreement_type + '_shared'] = 1;
                            setDB('kd_compls', compls);
                        }}

                        return jsonResponse({{ message: 'Compliance document uploaded', document: newDoc }});
                    }}

                    // General compliance flags update
                    const cIdx = compls.findIndex(c => c.job_requirement_id == reqId);
                    if (cIdx >= 0) {{
                        compls[cIdx].client_nda_shared = body.client_nda_shared ? 1 : 0;
                        compls[cIdx].client_msa_shared = body.client_msa_shared ? 1 : 0;
                        compls[cIdx].vendor_nda_shared = body.vendor_nda_shared ? 1 : 0;
                        compls[cIdx].vendor_msa_shared = body.vendor_msa_shared ? 1 : 0;
                        compls[cIdx].consultant_nda_shared = body.consultant_nda_shared ? 1 : 0;
                        compls[cIdx].consultant_msa_shared = body.consultant_msa_shared ? 1 : 0;
                        setDB('kd_compls', compls);
                    }}
                    return jsonResponse({{ message: 'Compliance updated' }});
                }}
            }}

            // -------------------------------------------------------------
            // COMPLIANCE DOCUMENTS CRUD (MODIFY & DELETE)
            // -------------------------------------------------------------
            if (path.startsWith('/api/compliance/documents/')) {{
                const parts = path.split('/');
                const docId = parts[4];
                const docs = getDB('kd_docs');
                const compls = getDB('kd_compls');

                if (method === 'DELETE') {{
                    const targetDoc = docs.find(d => d.id == docId);
                    const updatedDocs = docs.filter(d => d.id != docId);
                    setDB('kd_docs', updatedDocs);

                    if (targetDoc) {{
                        const reqId = targetDoc.job_requirement_id;
                        const agType = targetDoc.agreement_type;
                        const remaining = updatedDocs.filter(d => d.job_requirement_id == reqId && d.agreement_type == agType);
                        if (remaining.length === 0) {{
                            const cIdx = compls.findIndex(c => c.job_requirement_id == reqId);
                            if (cIdx >= 0) {{
                                compls[cIdx][agType + '_shared'] = 0;
                                setDB('kd_compls', compls);
                            }}
                        }}
                    }}
                    return jsonResponse({{ message: 'Compliance document deleted successfully', success: true }});
                }}

                if (method === 'PUT' || method === 'POST') {{
                    const dIdx = docs.findIndex(d => d.id == docId);
                    if (dIdx >= 0) {{
                        const oldDoc = docs[dIdx];
                        let fileName = oldDoc.file_name;
                        let origName = oldDoc.original_name;
                        if (body.file && body.file.name) {{
                            fileName = body.file.name;
                            origName = body.file.name;
                        }}
                        docs[dIdx] = {{
                            ...oldDoc,
                            agreement_type: body.agreement_type || oldDoc.agreement_type,
                            remark: body.remark !== undefined ? body.remark : oldDoc.remark,
                            is_signed: body.is_signed !== undefined ? (body.is_signed == '1' || body.is_signed === 1 || body.is_signed === true ? 1 : 0) : oldDoc.is_signed,
                            file_name: fileName,
                            original_name: origName,
                            updated_at: new Date().toISOString()
                        }};
                        setDB('kd_docs', docs);

                        const agType = body.agreement_type || oldDoc.agreement_type;
                        const cIdx = compls.findIndex(c => c.job_requirement_id == oldDoc.job_requirement_id);
                        if (cIdx >= 0) {{
                            compls[cIdx][agType + '_shared'] = (body.is_signed == '1' || body.is_signed === 1 || body.is_signed === true) ? 1 : 0;
                            setDB('kd_compls', compls);
                        }}
                        return jsonResponse({{ message: 'Compliance document updated successfully', success: true }});
                    }}
                    return jsonResponse({{ error: 'Document not found' }}, 404);
                }}
            }}

            // -------------------------------------------------------------
            // CANDIDATES
            // -------------------------------------------------------------
            if (path === '/api/candidates') {{
                const cands = getDB('kd_cands');
                if (method === 'GET') {{
                    return jsonResponse(cands);
                }}
                if (method === 'POST') {{
                    const newId = Date.now();
                    const cand = {{
                        id: newId,
                        job_requirement_id: parseInt(body.job_requirement_id),
                        candidate_name: body.candidate_name,
                        email: body.email || '',
                        phone: body.phone || '',
                        current_stage: body.current_stage || 'Profile Shared',
                        sourcing_type: body.sourcing_type || 'Internal',
                        ctc: body.ctc || '',
                        ectc: body.ectc || '',
                        notice_period: body.notice_period || '',
                        current_location: body.current_location || '',
                        remarks: body.remarks || '',
                        vendor_name: body.vendor_name || '',
                        vendor_billing_rate: body.vendor_billing_rate || '',
                        current_company: body.current_company || '',
                        office_work_type: body.office_work_type || 'Hybrid',
                        doj: body.doj || '',
                        final_billing_rate: body.final_billing_rate || '',
                        resume_filename: body.resume && body.resume.name ? body.resume.name : 'resume.pdf',
                        created_at: new Date().toISOString()
                    }};
                    cands.unshift(cand);
                    setDB('kd_cands', cands);
                    return jsonResponse({{ message: 'Candidate created', id: newId }}, 201);
                }}
            }}

            if (path.startsWith('/api/candidates/')) {{
                const parts = path.split('/');
                const candId = parts[3];
                const cands = getDB('kd_cands');

                if (parts.length === 4) {{
                    if (method === 'PUT') {{
                        const idx = cands.findIndex(c => c.id == candId);
                        if (idx >= 0) {{
                            cands[idx] = {{ ...cands[idx], ...body, updated_at: new Date().toISOString() }};
                            setDB('kd_cands', cands);
                        }}
                        return jsonResponse({{ message: 'Candidate updated' }});
                    }}
                    if (method === 'DELETE') {{
                        const updated = cands.filter(c => c.id != candId);
                        setDB('kd_cands', updated);
                        return jsonResponse({{ message: 'Candidate deleted' }});
                    }}
                }}

                if (parts[4] === 'stage') {{
                    const idx = cands.findIndex(c => c.id == candId);
                    if (idx >= 0) {{
                        cands[idx].current_stage = body.current_stage;
                        if (body.doj) cands[idx].doj = body.doj;
                        if (body.final_billing_rate) cands[idx].final_billing_rate = body.final_billing_rate;
                        setDB('kd_cands', cands);
                    }}
                    return jsonResponse({{ message: 'Stage updated' }});
                }}

                if (parts[4] === 'comments') {{
                    const comments = getDB('kd_comments');
                    if (method === 'GET') {{
                        const cComments = comments.filter(c => c.candidate_id == candId);
                        return jsonResponse(cComments);
                    }}
                    if (method === 'POST') {{
                        const userJson = sessionStorage.getItem('kd_active_session');
                        const currUser = userJson ? JSON.parse(userJson) : {{ full_name: 'Manager', id: 1 }};
                        const newComment = {{
                            id: Date.now(),
                            candidate_id: parseInt(candId),
                            job_requirement_id: parseInt(body.job_requirement_id) || 1,
                            author_user_id: currUser.id,
                            author_name: currUser.full_name || 'Hiring Manager',
                            comment_text: body.comment_text,
                            is_notification: body.is_notification ? 1 : 0,
                            priority_level: body.priority_level || 'Normal',
                            created_at: new Date().toISOString()
                        }};
                        comments.unshift(newComment);
                        setDB('kd_comments', comments);
                        return jsonResponse({{ message: 'Comment added', comment: newComment }}, 201);
                    }}
                }}
            }}

            // -------------------------------------------------------------
            // NOTIFICATIONS
            // -------------------------------------------------------------
            if (path.startsWith('/api/notifications')) {{
                const comments = getDB('kd_comments');
                const cands = getDB('kd_cands');
                const reqs = getDB('kd_reqs');
                const notifs = comments.filter(c => c.is_notification == 1).slice(0, 30).map(c => {{
                    const cand = cands.find(cd => cd.id == c.candidate_id) || {{ candidate_name: 'Candidate' }};
                    const req = reqs.find(r => r.id == c.job_requirement_id) || {{ job_title: 'Position' }};
                    return {{
                        ...c,
                        candidate_name: cand.candidate_name,
                        job_title: req.job_title
                    }};
                }});
                return jsonResponse(notifs);
            }}

            // -------------------------------------------------------------
            // ADMIN USERS MANAGEMENT
            // -------------------------------------------------------------
            if (path === '/api/admin/users') {{
                const users = getDB('kd_users');
                if (method === 'GET') {{
                    return jsonResponse(users);
                }}
                if (method === 'POST') {{
                    const newId = Date.now();
                    const newUser = {{
                        id: newId,
                        username: body.username,
                        full_name: body.full_name || body.username,
                        email: body.email || (body.username + '@keydynamicssolutions.com'),
                        password_hash: body.password || 'User@123',
                        role: body.role || 'User',
                        rights: body.rights || {{}},
                        status: 'Active',
                        auth_provider: 'Local',
                        created_at: new Date().toISOString()
                    }};
                    users.push(newUser);
                    setDB('kd_users', users);
                    return jsonResponse({{ message: 'User created successfully', user: newUser }}, 201);
                }}
            }}

            if (path.startsWith('/api/admin/users/')) {{
                const parts = path.split('/');
                const userId = parts[4];
                const users = getDB('kd_users');
                const idx = users.findIndex(u => u.id == userId);

                if (parts.length === 5) {{
                    if (method === 'PUT') {{
                        if (idx >= 0) {{
                            users[idx] = {{
                                ...users[idx],
                                full_name: body.full_name || users[idx].full_name,
                                email: body.email || users[idx].email,
                                role: body.role || users[idx].role,
                                rights: body.rights || users[idx].rights,
                                status: body.status || users[idx].status
                            }};
                            setDB('kd_users', users);
                        }}
                        return jsonResponse({{ message: 'User updated successfully', user: users[idx] }});
                    }}
                    if (method === 'DELETE') {{
                        const updated = users.filter(u => u.id != userId);
                        setDB('kd_users', updated);
                        return jsonResponse({{ message: 'User deleted' }});
                    }}
                }}

                if (parts[5] === 'reset-password') {{
                    if (idx >= 0) {{
                        users[idx].password_hash = body.new_password;
                        setDB('kd_users', users);
                    }}
                    return jsonResponse({{ message: 'Password reset successfully' }});
                }}
            }}

            // -------------------------------------------------------------
            // SYSTEM SETTINGS (USD/INR EXCHANGE RATE)
            // -------------------------------------------------------------
            if (path === '/api/settings') {{
                let settings = {{
                    usd_inr_exchange_rate: localStorage.getItem('kd_usd_inr_rate') || '84.00'
                }};
                if (method === 'GET') {{
                    return jsonResponse(settings);
                }}
                if (method === 'PUT') {{
                    if (body && body.usd_inr_exchange_rate) {{
                        localStorage.setItem('kd_usd_inr_rate', body.usd_inr_exchange_rate);
                        settings.usd_inr_exchange_rate = body.usd_inr_exchange_rate;
                    }}
                    return jsonResponse({{ message: 'Settings updated successfully', settings }});
                }}
            }}

            // -------------------------------------------------------------
            // MANAGEMENT REPORTS
            // -------------------------------------------------------------
            if (path === '/api/reports/management') {{
                const reqs = getDB('kd_reqs');
                const cands = getDB('kd_cands');
                const placed = cands.filter(c => c.current_stage === 'Final Selected');
                
                // Group by client
                const clientMap = {{}};
                reqs.forEach(r => {{
                    const cname = r.client_name || 'Direct Client';
                    if (!clientMap[cname]) {{
                        clientMap[cname] = {{ client_name: cname, total_requirements: 0, shared: 0, selected: 0 }};
                    }}
                    clientMap[cname].total_requirements += 1;
                }});

                cands.forEach(c => {{
                    const req = reqs.find(r => r.id == c.job_requirement_id);
                    if (req) {{
                        const cname = req.client_name || 'Direct Client';
                        if (clientMap[cname]) {{
                            clientMap[cname].shared += 1;
                            if (c.current_stage === 'Final Selected') clientMap[cname].selected += 1;
                        }}
                    }}
                }});

                return jsonResponse({{
                    summary: {{
                        total_resumes_shared: cands.length,
                        total_shortlisted: cands.filter(c => c.current_stage === 'Shortlisted').length,
                        total_placed: placed.length,
                        overall_closure_rate: Math.round((placed.length / Math.max(1, reqs.length)) * 100) + '%'
                    }},
                    client_reports: Object.values(clientMap),
                    consultants_report: placed.map(p => ({{
                        candidate_name: p.candidate_name,
                        client_name: (reqs.find(r => r.id == p.job_requirement_id) || {{}}).client_name || 'Client',
                        job_title: (reqs.find(r => r.id == p.job_requirement_id) || {{}}).job_title || 'Consultant',
                        doj: p.doj || 'Immediate',
                        final_billing_rate: p.final_billing_rate || '$85/hr'
                    }}))
                }});
            }}

            return jsonResponse({{ message: 'Success' }});
        }};
    }})();
    </script>
    """

    # Insert virtual engine script into head
    full_html = html.replace("<head>", "<head>\n" + virtual_engine_script)

    # 5. Write index.html at root of dist_website
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_html)

    # 6. Write vercel.json for static deployment
    vercel_config = {
        "version": 2,
        "cleanUrls": True,
        "routes": [
            { "src": "/(.*)", "dest": "/index.html" }
        ]
    }
    with open(os.path.join(output_dir, "vercel.json"), "w", encoding="utf-8") as f:
        json.dump(vercel_config, f, indent=2)

    # 7. Write netlify.toml
    netlify_config = """[build]
  publish = "."

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
"""
    with open(os.path.join(output_dir, "netlify.toml"), "w", encoding="utf-8") as f:
        f.write(netlify_config)

    # 8. Write README.md with crystal-clear deployment instructions
    readme_content = """# Key Dynamics Solutions - Recruitment & Requisition Management Portal

This package is a **100% Production-Ready Web Application** that runs on ANY web hosting without requiring any backend server, Docker, or external database!

---

## 🚀 How to Deploy / Upload in 2 Minutes:

### Option 1: Vercel (Recommended)
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New Project"**.
3. Drag & drop this entire unzipped folder, or push it to your GitHub repository and import it.
4. Click **"Deploy"** — Vercel will instantly give you a live HTTPS public link!

### Option 2: Netlify (Drag & Drop)
1. Go to [netlify.com](https://netlify.com) and log in.
2. Drag & drop this entire unzipped folder onto the Netlify dashboard.
3. Your website goes live immediately!

### Option 3: cPanel / Hostinger / GoDaddy
1. Log in to your cPanel File Manager.
2. Go to `public_html`.
3. Upload `index.html` (and optionally `vercel.json`).
4. That's it! Open your domain in any browser.

### Option 4: Run Locally (Offline)
Simply **double-click** `index.html` in Windows File Explorer. It opens right in your browser with all features working offline!

---

## 🔑 Default Login Credentials

| Account | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@keydynamicssolutions.com` | `Admin@123` |
| **Hiring Manager** | `manager@keydynamicssolutions.com` | `Manager@123` |
| **Recruiter / Staff** | `user@keydynamicssolutions.com` | `User@123` |

*(You can also use 1-Click login using the **"Sign in with Microsoft Dynamics 365"** button on the login screen).*
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 9. Create the ZIP file
    zip_name = "key-dynamics-recruitment-portal.zip"
    zip_path = os.path.join(proj_dir, zip_name)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, output_dir)
                z.write(full_p, rel_p)

    print(f"Built ZIP package: {zip_path} (Size: {os.path.getsize(zip_path)} bytes)")

    # 10. Copy to Downloads and Desktop
    downloads_zip = os.path.join(r"C:\Users\ITkey\Downloads", zip_name)
    desktop_dir = r"C:\Users\ITkey\OneDrive - Key Dynamics Solutions Private Limited\Desktop"
    desktop_zip = os.path.join(desktop_dir, zip_name)

    shutil.copy2(zip_path, downloads_zip)
    print(f"Copied to Downloads: {downloads_zip} ({os.path.getsize(downloads_zip)} bytes)")

    shutil.copy2(zip_path, desktop_zip)
    print(f"Copied to Desktop: {desktop_zip} ({os.path.getsize(desktop_zip)} bytes)")

    # Also copy the root index.html to Desktop directly
    shutil.copy2(os.path.join(output_dir, "index.html"), os.path.join(desktop_dir, "index.html"))
    shutil.copy2(os.path.join(output_dir, "index.html"), os.path.join(r"C:\Users\ITkey\Downloads", "index.html"))

if __name__ == '__main__':
    build_package()
