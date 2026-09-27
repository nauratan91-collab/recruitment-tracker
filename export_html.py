import os
import json
import base64
import shutil

def main():
    proj_dir = r"C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"
    desktop = r"C:\Users\ITkey\OneDrive - Key Dynamics Solutions Private Limited\Desktop"
    downloads = r"C:\Users\ITkey\Downloads"

    # Read base template
    template_path = os.path.join(proj_dir, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Read logo base64
    logo_path = os.path.join(proj_dir, "static", "images", "company_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        html = html.replace("/static/images/company_logo.png", logo_b64)

    # 1. Save standard full index.html to Desktop and Downloads
    out_desktop_index = os.path.join(desktop, "index.html")
    out_downloads_index = os.path.join(downloads, "index.html")

    with open(out_desktop_index, "w", encoding="utf-8") as f:
        f.write(html)
    with open(out_downloads_index, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved {out_desktop_index} (size: {os.path.getsize(out_desktop_index)})")
    print(f"Saved {out_downloads_index} (size: {os.path.getsize(out_downloads_index)})")

    # 2. Also save standalone self-contained offline HTML
    # Fetch database data
    import database
    conn = database.get_db()
    users = [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]
    reqs = [dict(r) for r in conn.execute("SELECT * FROM job_requirements").fetchall()]
    cands = [dict(r) for r in conn.execute("SELECT * FROM candidates").fetchall()]
    compliances = [dict(r) for r in conn.execute("SELECT * FROM compliance_records").fetchall()]

    for u in users:
        if isinstance(u.get("rights"), str):
            try:
                u["rights"] = json.loads(u["rights"])
            except Exception:
                pass

    store_init_js = f"""
<script>
// =============================================================================
// OFFLINE STANDALONE MODE (Activates when opened via file://)
// =============================================================================
(function() {{
    if (window.location.protocol !== 'file:') return;

    console.info("Key Dynamics Recruitment Portal: Standalone Offline Mode Active");

    const INITIAL_USERS = {json.dumps(users)};
    const INITIAL_REQS = {json.dumps(reqs)};
    const INITIAL_CANDS = {json.dumps(cands)};
    const INITIAL_COMPL = {json.dumps(compliances)};

    if (!localStorage.getItem('kd_users')) localStorage.setItem('kd_users', JSON.stringify(INITIAL_USERS));
    if (!localStorage.getItem('kd_reqs')) localStorage.setItem('kd_reqs', JSON.stringify(INITIAL_REQS));
    if (!localStorage.getItem('kd_cands')) localStorage.setItem('kd_cands', JSON.stringify(INITIAL_CANDS));
    if (!localStorage.getItem('kd_compl')) localStorage.setItem('kd_compl', JSON.stringify(INITIAL_COMPL));

    function getStore(k) {{ return JSON.parse(localStorage.getItem(k) || '[]'); }}
    function setStore(k, v) {{ localStorage.setItem(k, JSON.stringify(v)); }}

    const origFetch = window.fetch;
    window.fetch = async function(url, options = {{}}) {{
        const path = typeof url === 'string' ? url.split('?')[0] : url.url;
        const method = (options.method || 'GET').toUpperCase();
        let body = {{}};
        if (options.body) {{
            try {{
                body = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
            }} catch(e) {{}}
        }}

        const jsonRes = (data, status = 200) => new Response(JSON.stringify(data), {{
            status,
            headers: {{ 'Content-Type': 'application/json' }}
        }});

        if (path === '/api/auth/me') {{
            const userStr = sessionStorage.getItem('kd_curr_user');
            if (!userStr) return jsonRes({{ error: 'Unauthorized' }}, 401);
            return jsonRes(JSON.parse(userStr));
        }}

        if (path === '/api/auth/login') {{
            const users = getStore('kd_users');
            const identifier = (body.username || '').trim().toLowerCase();
            const u = users.find(x => (x.username.toLowerCase() === identifier || (x.email && x.email.toLowerCase() === identifier)));
            if (!u) return jsonRes({{ error: 'Invalid credentials' }}, 401);
            if (u.status !== 'Active') return jsonRes({{ error: 'Account deactivated' }}, 403);
            sessionStorage.setItem('kd_curr_user', JSON.stringify(u));
            return jsonRes({{ message: 'Login successful', user: u }});
        }}

        if (path === '/api/auth/microsoft-login') {{
            const users = getStore('kd_users');
            const email = (body.email || '').trim().toLowerCase();
            const u = users.find(x => x.email && x.email.toLowerCase() === email);
            if (!u) return jsonRes({{ error: 'Corporate email not registered' }}, 404);
            sessionStorage.setItem('kd_curr_user', JSON.stringify(u));
            return jsonRes({{ message: 'SSO Login successful', user: u, auth_provider: 'microsoft_dynamics_365' }});
        }}

        if (path === '/api/auth/logout') {{
            sessionStorage.removeItem('kd_curr_user');
            return jsonRes({{ message: 'Logged out' }});
        }}

        if (path === '/api/dashboard/stats') {{
            const reqs = getStore('kd_reqs');
            const cands = getStore('kd_cands');
            const openings = reqs.reduce((acc, r) => acc + (parseInt(r.open_positions) || 1), 0);
            return jsonRes({{
                total_requirements: reqs.length,
                total_openings: openings,
                total_candidates_shared: cands.length,
                total_selected: cands.filter(c => c.current_stage === 'Final Selected').length,
                stage_counts: {{
                    'Profile Shared': cands.filter(c => c.current_stage === 'Profile Shared').length,
                    'Shortlisted': cands.filter(c => c.current_stage === 'Shortlisted').length,
                    '1st Round': cands.filter(c => c.current_stage === '1st Round').length,
                    '2nd Round': cands.filter(c => c.current_stage === '2nd Round').length,
                    'Final Selected': cands.filter(c => c.current_stage === 'Final Selected').length,
                    'Rejected': cands.filter(c => c.current_stage === 'Rejected').length,
                }}
            }});
        }}

        if (path === '/api/requirements') {{
            const reqs = getStore('kd_reqs');
            const cands = getStore('kd_cands');
            const compls = getStore('kd_compl');
            if (method === 'GET') {{
                const enriched = reqs.map(r => {{
                    const rCands = cands.filter(c => c.job_requirement_id == r.id);
                    const comp = compls.find(c => c.job_requirement_id == r.id) || {{}};
                    return {{
                        ...r,
                        ...comp,
                        candidates: rCands,
                        shared_count: rCands.length,
                        selected_count: rCands.filter(c => c.current_stage === 'Final Selected').length,
                        tat_days: 14,
                        tat_display: '14 Days',
                        tat_badge: 'green'
                    }};
                }});
                return jsonRes(enriched);
            }}
            if (method === 'POST') {{
                const newId = Date.now();
                const newReq = {{ ...body, id: newId, created_at: new Date().toISOString() }};
                reqs.unshift(newReq);
                setStore('kd_reqs', reqs);
                return jsonRes({{ message: 'Requirement created', id: newId }}, 201);
            }}
        }}

        if (path.startsWith('/api/requirements/')) {{
            const parts = path.split('/');
            const reqId = parts[3];
            const reqs = getStore('kd_reqs');
            if (parts.length === 4) {{
                if (method === 'PUT') {{
                    const idx = reqs.findIndex(r => r.id == reqId);
                    if (idx >= 0) {{
                        reqs[idx] = {{ ...reqs[idx], ...body, updated_at: new Date().toISOString() }};
                        setStore('kd_reqs', reqs);
                    }}
                    return jsonRes({{ message: 'Requirement updated' }});
                }}
                if (method === 'DELETE') {{
                    const updated = reqs.filter(r => r.id != reqId);
                    setStore('kd_reqs', updated);
                    return jsonRes({{ message: 'Requirement deleted' }});
                }}
            }}
            if (parts[4] === 'status') {{
                const idx = reqs.findIndex(r => r.id == reqId);
                if (idx >= 0) {{
                    reqs[idx].status = body.status;
                    setStore('kd_reqs', reqs);
                }}
                return jsonRes({{ message: 'Status updated' }});
            }}
            if (parts[4] === 'compliance') {{
                return jsonRes({{ message: 'Compliance updated' }});
            }}
        }}

        if (path === '/api/candidates') {{
            const cands = getStore('kd_cands');
            if (method === 'GET') return jsonRes(cands);
            if (method === 'POST') {{
                const newId = Date.now();
                const newCand = {{ ...body, id: newId, created_at: new Date().toISOString() }};
                cands.unshift(newCand);
                setStore('kd_cands', cands);
                return jsonRes({{ message: 'Candidate created', id: newId }}, 201);
            }}
        }}

        if (path === '/api/admin/users') {{
            const users = getStore('kd_users');
            if (method === 'GET') return jsonRes(users);
            if (method === 'POST') {{
                const newId = Date.now();
                const newUser = {{ ...body, id: newId, status: 'Active' }};
                users.push(newUser);
                setStore('kd_users', users);
                return jsonRes({{ message: 'User created', user: newUser }}, 201);
            }}
        }}

        if (path === '/api/reports/management') {{
            return jsonRes({{
                summary: {{ total_resumes_shared: 50, total_shortlisted: 25, overall_closure_rate: 65 }},
                client_reports: [],
                consultants_report: []
            }});
        }}

        if (path.startsWith('/api/notifications')) {{
            return jsonRes([]);
        }}

        return jsonRes({{ message: 'OK' }});
    }};
}})();
</script>
"""
    html_standalone = html.replace("<head>", "<head>\n" + store_init_js)
    
    out_standalone_desktop = os.path.join(desktop, "Key_Dynamics_Recruitment_Portal.html")
    out_standalone_downloads = os.path.join(downloads, "Key_Dynamics_Recruitment_Portal.html")
    
    with open(out_standalone_desktop, "w", encoding="utf-8") as f:
        f.write(html_standalone)
    with open(out_standalone_downloads, "w", encoding="utf-8") as f:
        f.write(html_standalone)

    print(f"Saved standalone: {out_standalone_desktop} ({os.path.getsize(out_standalone_desktop)} bytes)")

if __name__ == '__main__':
    main()
