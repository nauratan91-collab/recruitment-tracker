import os
import io
import unittest
from app import app
from database import init_db, get_db

class AuthenticatedClient:
    """Wrapper around Flask TestClient that injects and dynamically tracks active Bearer Access Token."""
    def __init__(self, raw_client):
        self.raw_client = raw_client
        self.active_token = None

    def _prepare_kwargs(self, kwargs):
        headers = dict(kwargs.get('headers') or {})
        if 'Authorization' not in headers and self.active_token:
            headers['Authorization'] = f'Bearer {self.active_token}'
        kwargs['headers'] = headers
        return kwargs

    def get(self, *args, **kwargs):
        return self.raw_client.get(*args, **self._prepare_kwargs(kwargs))

    def post(self, *args, **kwargs):
        res = self.raw_client.post(*args, **self._prepare_kwargs(kwargs))
        if args and '/api/auth/login' in args[0] and res.status_code == 200:
            data = res.get_json()
            if data and data.get('access_token'):
                self.active_token = data['access_token']
        elif args and '/api/auth/logout' in args[0]:
            self.active_token = None
        return res

    def put(self, *args, **kwargs):
        return self.raw_client.put(*args, **self._prepare_kwargs(kwargs))

    def patch(self, *args, **kwargs):
        return self.raw_client.patch(*args, **self._prepare_kwargs(kwargs))

    def delete(self, *args, **kwargs):
        return self.raw_client.delete(*args, **self._prepare_kwargs(kwargs))

    def __getattr__(self, name):
        return getattr(self.raw_client, name)


class TestRecruitmentTracker(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.raw_client = app.test_client()
        self.client = AuthenticatedClient(self.raw_client)
        # Login as Admin by default so all management and setup tests run with full privileges
        login_res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
        self.admin_token = self.client.active_token

    def test_01_dashboard_stats(self):
        response = self.client.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_requirements', data)
        self.assertIn('total_openings', data)
        self.assertIn('stage_counts', data)
        print("[OK] Dashboard Stats API Test Passed!")

    def test_02_requirements(self):
        response = self.client.get('/api/requirements')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        print(f"[OK] Requirements API Test Passed! Found {len(data)} requirements.")

    def test_03_create_requirement(self):
        new_req = {
            'client_name': 'Test Global Corp',
            'end_client': 'Test Sub-Client',
            'spoc_name': 'Rajesh Kumar',
            'spoc_mobile': '+91 98765 43210',
            'job_title': 'Senior Python Developer',
            'work_location_type': 'Remote',
            'location_city': 'San Francisco, CA',
            'budget': '$150,000 / year',
            'open_positions': 2,
            'job_description': 'Building AI API integration services.',
            'client_nda_shared': True,
            'client_msa_shared': True,
            'vendor_nda_shared': True,
            'vendor_msa_shared': False,
            'consultant_nda_shared': True,
            'consultant_msa_shared': True
        }
        response = self.client.post('/api/requirements', json=new_req)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

        # Verify SPOC fields are returned
        get_res = self.client.get(f"/api/requirements/{data['id']}")
        self.assertEqual(get_res.status_code, 200)
        req_obj = get_res.get_json()
        self.assertEqual(req_obj.get('spoc_name'), 'Rajesh Kumar')
        self.assertEqual(req_obj.get('spoc_mobile'), '+91 98765 43210')

        # Test updating SPOC details
        update_res = self.client.put(f"/api/requirements/{data['id']}", json={
            'client_name': 'Test Global Corp',
            'job_title': 'Senior Python Developer',
            'spoc_name': 'Rajesh Kumar (Senior Director)',
            'spoc_mobile': '+91 99999 88888',
            'work_location_type': 'Remote',
            'open_positions': 2,
            'status': 'Active'
        })
        self.assertEqual(update_res.status_code, 200)
        updated_req = self.client.get(f"/api/requirements/{data['id']}").get_json()
        self.assertEqual(updated_req.get('spoc_name'), 'Rajesh Kumar (Senior Director)')
        self.assertEqual(updated_req.get('spoc_mobile'), '+91 99999 88888')

        print(f"[OK] Create & Update Requirement with SPOC API Test Passed! Created requirement ID: {data['id']}")

    def test_04_create_candidate_with_resume(self):
        data = {
            'job_requirement_id': 1,
            'candidate_name': 'Samantha Reed',
            'email': 'samantha.r@email.com',
            'phone': '+1 555-9876',
            'current_stage': 'Final Selected',
            'doj': '2026-11-01',
            'final_billing_rate': '$90/hr',
            'resume': (io.BytesIO(b"Dummy Samantha Reed Resume Content"), 'samantha_resume.pdf')
        }
        response = self.client.post('/api/candidates', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 201)
        cand_data = response.get_json()
        self.assertIn('id', cand_data)
        print(f"[OK] Create Candidate & Resume Upload API Test Passed! Candidate ID: {cand_data['id']}")

    def test_05_resume_download(self):
        response = self.client.get('/api/resumes/sample_alex_morgan_resume.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex Morgan", response.data)
        print("[OK] Resume File Serving Test Passed!")

    def test_06_database_stats_and_tables(self):
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('tables', data)
        self.assertIn('job_requirements', data['tables'])
        self.assertIn('candidates', data['tables'])
        self.assertIn('compliance_records', data['tables'])
        self.assertIn('resumes', data['tables'])

        # Query table rows
        tbl_res = self.client.get('/api/database/table/job_requirements')
        self.assertEqual(tbl_res.status_code, 200)
        rows = tbl_res.get_json()
        self.assertIsInstance(rows, list)
        print(f"[OK] Database Stats & Table Explorer Test Passed! Found {len(rows)} requirements in DB.")

    def test_07_database_export_sql(self):
        response = self.client.get('/api/database/export-sql')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CREATE TABLE", response.data)
        print("[OK] Database Full SQL Export Test Passed!")

    def test_08_management_report(self):
        response = self.client.get('/api/reports/management')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('summary', data)
        self.assertIn('total_resumes_shared', data['summary'])
        self.assertIn('total_shortlisted', data['summary'])
        self.assertIn('overall_closure_rate', data['summary'])
        self.assertIn('client_reports', data)
        self.assertIn('consultants_report', data)
        self.assertGreaterEqual(len(data['client_reports']), 1)
        print(f"[OK] Management Report API Test Passed! Found {len(data['client_reports'])} clients and {len(data['consultants_report'])} placed consultants.")

    def test_09_update_requirement_status(self):
        # Update requirement #1 to 'On Hold'
        res = self.client.patch('/api/requirements/1/status', json={'status': 'On Hold'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'On Hold')

        # Check that GET /api/requirements reflects 'On Hold'
        reqs_res = self.client.get('/api/requirements')
        reqs = reqs_res.get_json()
        req1 = next(r for r in reqs if r['id'] == 1)
        self.assertEqual(req1['status'], 'On Hold')

        # Reset back to 'Active'
        res_reset = self.client.patch('/api/requirements/1/status', json={'status': 'Active'})
        self.assertEqual(res_reset.status_code, 200)
        print("[OK] Requirement Status Update API Test Passed!")

    def test_10_update_candidate_stage(self):
        # Update candidate #1 to 'Shortlisted'
        res = self.client.patch('/api/candidates/1/stage', json={'current_stage': 'Shortlisted'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['current_stage'], 'Shortlisted')

        # Update candidate #1 to '1st Round'
        res = self.client.patch('/api/candidates/1/stage', json={'current_stage': '1st Round'})
        self.assertEqual(res.status_code, 200)

        # Update candidate #1 to '2nd Round'
        res = self.client.patch('/api/candidates/1/stage', json={'current_stage': '2nd Round'})
        self.assertEqual(res.status_code, 200)

        # Verify candidate list inside GET /api/requirements
        reqs_res = self.client.get('/api/requirements')
        reqs = reqs_res.get_json()
        self.assertTrue(any('candidates' in r and len(r['candidates']) > 0 for r in reqs))
        print("[OK] Candidate Stage Update API (Shortlisted, 1st Round, 2nd Round) Test Passed!")

    def test_11_login_user(self):
        # Test User (Recruiter) login
        res = self.client.post('/api/auth/login', json={'username': 'user', 'password': 'User@123'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'User')
        self.assertEqual(data['user']['username'], 'user')
        print("[OK] User Login (user / User@123) Test Passed!")

    def test_12_login_admin(self):
        # Test Admin login
        res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'Admin')
        self.assertEqual(data['user']['username'], 'admin')
        print("[OK] Admin Login (admin / Admin@123) Test Passed!")

    def test_13_login_invalid_password(self):
        # Test wrong password
        res = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'WrongPassword!'})
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn('error', data)
        print("[OK] Invalid Password Rejection Test Passed!")

    def test_14_change_password_workflow(self):
        # Login as user
        login_res = self.client.post('/api/auth/login', json={'username': 'user', 'password': 'User@123'})
        self.assertEqual(login_res.status_code, 200)

        # Attempt change password with wrong old password
        res_fail = self.client.post('/api/auth/change-password', json={
            'old_password': 'IncorrectPassword',
            'new_password': 'NewUser@123'
        })
        self.assertEqual(res_fail.status_code, 400)

        # Successfully change password
        res_success = self.client.post('/api/auth/change-password', json={
            'old_password': 'User@123',
            'new_password': 'NewUser@123'
        })
        self.assertEqual(res_success.status_code, 200)
        self.assertTrue(res_success.get_json()['success'])

        # Verify old password no longer works
        fail_old = self.client.post('/api/auth/login', json={'username': 'user', 'password': 'User@123'})
        self.assertEqual(fail_old.status_code, 401)

        # Verify new password works
        ok_new = self.client.post('/api/auth/login', json={'username': 'user', 'password': 'NewUser@123'})
        self.assertEqual(ok_new.status_code, 200)

        # Revert back to original password 'User@123' so standard credentials remain intact
        revert = self.client.post('/api/auth/change-password', json={
            'old_password': 'NewUser@123',
            'new_password': 'User@123'
        })
        self.assertEqual(revert.status_code, 200)
        print("[OK] Change Password Workflow (Verification & Reversion) Test Passed!")

    def test_15_auth_me_and_logout(self):
        # Login as admin
        self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})

        # Check /api/auth/me
        me_res = self.client.get('/api/auth/me')
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertTrue(me_data['authenticated'])
        self.assertEqual(me_data['user']['username'], 'admin')

        # Logout
        logout_res = self.client.post('/api/auth/logout')
        self.assertEqual(logout_res.status_code, 200)

        # Check /api/auth/me again
        me_after = self.client.get('/api/auth/me')
        self.assertEqual(me_after.status_code, 200)
        self.assertFalse(me_after.get_json()['authenticated'])
        print("[OK] Auth Session Check & Logout Test Passed!")

    def test_16_create_internal_candidate_with_sourcing_details(self):
        # Test creating candidate sourced internally with CTC, ECTC, NP period, Current location, Remark
        data = {
            'job_requirement_id': 1,
            'candidate_name': 'Rohan Sharma',
            'email': 'rohan.sharma@email.com',
            'phone': '+91 9876543210',
            'current_stage': 'Profile Shared',
            'source_type': 'Internal',
            'current_ctc': '₹18 LPA',
            'expected_ctc': '₹24 LPA',
            'notice_period': '30 Days',
            'current_location': 'Bangalore, India',
            'remarks': 'Strong background in Python backend, cleared initial technical screening.'
        }
        res = self.client.post('/api/candidates', json=data)
        self.assertEqual(res.status_code, 201)
        cand_id = res.get_json()['id']

        # Fetch candidate and verify fields
        cands_res = self.client.get('/api/candidates')
        cands = cands_res.get_json()
        saved = next((c for c in cands if c['id'] == cand_id), None)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['source_type'], 'Internal')
        self.assertEqual(saved['current_ctc'], '₹18 LPA')
        self.assertEqual(saved['expected_ctc'], '₹24 LPA')
        self.assertEqual(saved['notice_period'], '30 Days')
        self.assertEqual(saved['current_location'], 'Bangalore, India')
        self.assertEqual(saved['remarks'], 'Strong background in Python backend, cleared initial technical screening.')
        print("[OK] Internal Candidate Sourcing Fields (CTC, ECTC, NP, Location, Remark) Test Passed!")

    def test_17_create_vendor_candidate_with_sourcing_details(self):
        # Test creating candidate sourced by vendor with Vendor name, Billing, Current company, Office type
        data = {
            'job_requirement_id': 1,
            'candidate_name': 'Vikram Mehra',
            'email': 'vikram.m@email.com',
            'phone': '+1 408-555-0199',
            'current_stage': 'Shortlisted',
            'source_type': 'Vendor',
            'vendor_name': 'Apex Talent Partners',
            'vendor_billing_rate': '$85/hr',
            'current_company': 'Infosys Technologies',
            'office_work_type': 'Hybrid'
        }
        res = self.client.post('/api/candidates', json=data)
        self.assertEqual(res.status_code, 201)
        cand_id = res.get_json()['id']

        # Fetch candidate and verify fields
        cands_res = self.client.get('/api/candidates')
        cands = cands_res.get_json()
        saved = next((c for c in cands if c['id'] == cand_id), None)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['source_type'], 'Vendor')
        self.assertEqual(saved['vendor_name'], 'Apex Talent Partners')
        self.assertEqual(saved['vendor_billing_rate'], '$85/hr')
        self.assertEqual(saved['current_company'], 'Infosys Technologies')
        self.assertEqual(saved['office_work_type'], 'Hybrid')
        print("[OK] Vendor Candidate Sourcing Fields (Vendor Name, Billing, Company, Office Type) Test Passed!")

    def test_18_update_candidate_sourcing_fields(self):
        # Update existing candidate #1 with sourcing fields
        update_data = {
            'candidate_name': 'Alex Morgan',
            'current_stage': 'Final Selected',
            'doj': '2026-10-15',
            'final_billing_rate': '$85/hr',
            'consultant_pay_rate': '$65/hr',
            'email': 'alex.morgan@email.com',
            'phone': '+1 555-0192',
            'source_type': 'Internal',
            'current_ctc': '$115,000',
            'expected_ctc': '$140,000',
            'notice_period': '15 Days',
            'current_location': 'New York, NY',
            'remarks': 'Exceptional fit for Lead Engineer.'
        }
        res = self.client.put('/api/candidates/1', json=update_data)
        self.assertEqual(res.status_code, 200)

        # Verify in candidate list
        cands_res = self.client.get('/api/candidates')
        cands = cands_res.get_json()
        cand1 = next(c for c in cands if c['id'] == 1)
        self.assertEqual(cand1['source_type'], 'Internal')
        self.assertEqual(cand1['current_ctc'], '$115,000')
        self.assertEqual(cand1['expected_ctc'], '$140,000')
        self.assertEqual(cand1['notice_period'], '15 Days')
        self.assertEqual(cand1['current_location'], 'New York, NY')
        self.assertEqual(cand1['remarks'], 'Exceptional fit for Lead Engineer.')
        print("[OK] Candidate Sourcing Fields Update & Persistence Test Passed!")

    def test_19_create_requirement_with_open_date_and_tat(self):
        from datetime import date, timedelta
        past_date = (date.today() - timedelta(days=20)).isoformat()
        req_data = {
            'job_title': 'Senior DevOps Engineer',
            'client_name': 'CloudScale Global',
            'end_client': 'FinTech Alliance',
            'job_description': 'CI/CD and Kubernetes setup',
            'work_location_type': 'Remote',
            'location_city': 'San Jose, CA',
            'budget': '$90 - $110/hr',
            'open_positions': 2,
            'status': 'Active',
            'open_date': past_date
        }
        res = self.client.post('/api/requirements', json=req_data)
        self.assertEqual(res.status_code, 201)
        req_id = res.get_json()['id']

        # Verify open_date and TAT in GET /api/requirements
        get_res = self.client.get('/api/requirements')
        reqs = get_res.get_json()
        devops_req = next((r for r in reqs if r['id'] == req_id), None)
        self.assertIsNotNone(devops_req)
        self.assertEqual(devops_req['open_date'], past_date)
        self.assertGreaterEqual(devops_req['tat_days'], 20)
        self.assertEqual(devops_req['tat_badge'], 'amber')
        self.assertIn('20 Days Open', devops_req['tat_display'])
        print("[OK] Requirement Open Date & Active TAT Calculation Test Passed!")

    def test_20_requirement_status_closure_tat(self):
        from datetime import date, timedelta
        # Create a requirement opened 45 days ago
        past_date = (date.today() - timedelta(days=45)).isoformat()
        req_data = {
            'job_title': 'Lead AI Architect',
            'client_name': 'Nexus Innovations',
            'end_client': 'Global Health Corp',
            'job_description': 'LLM deployment architecture',
            'work_location_type': 'Hybrid',
            'location_city': 'Boston, MA',
            'budget': '$130/hr',
            'open_positions': 1,
            'status': 'Active',
            'open_date': past_date
        }
        create_res = self.client.post('/api/requirements', json=req_data)
        self.assertEqual(create_res.status_code, 201)
        req_id = create_res.get_json()['id']

        # Close/Fill requirement
        patch_res = self.client.patch(f'/api/requirements/{req_id}/status', json={'status': 'Filled'})
        self.assertEqual(patch_res.status_code, 200)

        # Verify close_date and closed TAT calculation
        get_res = self.client.get('/api/requirements')
        reqs = get_res.get_json()
        ai_req = next((r for r in reqs if r['id'] == req_id), None)
        self.assertIsNotNone(ai_req)
        self.assertEqual(ai_req['status'], 'Filled')
        self.assertEqual(ai_req['close_date'], date.today().isoformat())
        self.assertGreaterEqual(ai_req['tat_days'], 45)
        self.assertEqual(ai_req['tat_badge'], 'red')  # > 30 days is red
        self.assertIn('Closed in 45 Days', ai_req['tat_display'])

        # Test reopening requirement
        reopen_res = self.client.patch(f'/api/requirements/{req_id}/status', json={'status': 'Active'})
        self.assertEqual(reopen_res.status_code, 200)
        get_reopened = self.client.get('/api/requirements')
        reopened_req = next((r for r in get_reopened.get_json() if r['id'] == req_id), None)
        self.assertEqual(reopened_req['status'], 'Active')
        self.assertIsNone(reopened_req['close_date'])
        self.assertIn('Days Open', reopened_req['tat_display'])
        print("[OK] Requirement Status Closure Date & Closed TAT Test Passed!")

    def test_21_manager_login_and_role(self):
        # Test Manager Login (manager / Manager@123)
        res = self.client.post('/api/auth/login', json={
            'username': 'manager',
            'password': 'Manager@123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'Manager')
        self.assertEqual(data['user']['username'], 'manager')

        # Test auth session check for Manager
        me_res = self.client.get('/api/auth/me')
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertTrue(me_data['authenticated'])
        self.assertEqual(me_data['user']['role'], 'Manager')
        print("[OK] Manager Login & Role Verification (manager / Manager@123) Test Passed!")

    def test_22_manager_add_profile_comment_and_notification(self):
        # 1. Login as manager
        self.client.post('/api/auth/login', json={
            'username': 'manager',
            'password': 'Manager@123'
        })

        # 2. Add feedback comment on candidate #1
        comment_res = self.client.post('/api/candidates/1/comments', json={
            'comment_text': 'Candidate assessed well in system architecture and Python microservices.',
            'comment_type': 'Feedback'
        })
        self.assertEqual(comment_res.status_code, 201)
        c_data = comment_res.get_json()
        self.assertTrue(c_data['success'])
        self.assertEqual(c_data['comment']['author_role'], 'Manager')
        self.assertEqual(c_data['comment']['comment_type'], 'Feedback')

        # 3. Add high priority notification on candidate #1
        notif_res = self.client.post('/api/candidates/1/comments', json={
            'comment_text': 'ACTION REQUIRED: Please arrange 2nd technical panel interview with client lead.',
            'comment_type': 'Notification',
            'is_notification': 1
        })
        self.assertEqual(notif_res.status_code, 201)
        n_data = notif_res.get_json()
        self.assertTrue(n_data['success'])
        self.assertEqual(n_data['comment']['is_notification'], 1)
        print("[OK] Manager Profile Comment & Priority Notification Creation Test Passed!")

    def test_23_fetch_candidate_comments_and_notifications_feed(self):
        # 1. Fetch candidate comments
        res = self.client.get('/api/candidates/1/comments')
        self.assertEqual(res.status_code, 200)
        comments = res.get_json()
        self.assertIsInstance(comments, list)
        self.assertGreaterEqual(len(comments), 2)
        
        # Verify comment contents
        has_manager_comment = any(c['author_role'] == 'Manager' for c in comments)
        has_notif = any(c['is_notification'] == 1 for c in comments)
        self.assertTrue(has_manager_comment)
        self.assertTrue(has_notif)

        # 2. Fetch global notifications feed
        feed_res = self.client.get('/api/notifications')
        self.assertEqual(feed_res.status_code, 200)
        feed = feed_res.get_json()
        self.assertIsInstance(feed, list)
        self.assertGreaterEqual(len(feed), 1)
        self.assertIn('candidate_name', feed[0])

        # 3. Check candidate list contains comment counters
        cands_res = self.client.get('/api/candidates')
        self.assertEqual(cands_res.status_code, 200)
        cands = cands_res.get_json()
        cand1 = next((c for c in cands if c['id'] == 1), None)
        self.assertIsNotNone(cand1)
        self.assertGreaterEqual(cand1['comments_count'], 2)
        print("[OK] Candidate Comments & Manager Notification Feed API Test Passed!")

    def test_24_compliance_document_upload_and_metadata(self):
        import io
        # 1. Login as manager
        self.client.post('/api/auth/login', json={'username': 'manager', 'password': 'Manager@123'})

        # 2. Upload signed client NDA with document file and remark
        test_file_content = b"%PDF-1.4 Mock Signed NDA Document Content"
        data = {
            'agreement_type': 'client_nda',
            'is_signed': '1',
            'remark': 'Client NDA executed and signed by Legal Counsel on 18-Sep-2026.',
            'file': (io.BytesIO(test_file_content), 'Executed_Client_NDA_2026.pdf')
        }

        res = self.client.post('/api/requirements/1/compliance/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 201)
        res_json = res.get_json()
        self.assertIn('document', res_json)
        doc = res_json['document']
        self.assertEqual(doc['agreement_type'], 'client_nda')
        self.assertEqual(doc['is_signed'], 1)
        self.assertEqual(doc['uploaded_by'], 'Hiring Manager')
        self.assertEqual(doc['uploaded_by_role'], 'Manager')
        self.assertEqual(doc['remark'], 'Client NDA executed and signed by Legal Counsel on 18-Sep-2026.')
        self.assertIn('Executed_Client_NDA_2026.pdf', doc['original_name'])
        self.assertIsNotNone(doc['download_url'])
        print("[OK] Compliance Document Upload & Uploader Metadata Test Passed!")

    def test_25_compliance_document_file_serving(self):
        # 1. Fetch compliance documents for requirement 1
        docs_res = self.client.get('/api/requirements/1/compliance/documents')
        self.assertEqual(docs_res.status_code, 200)
        docs = docs_res.get_json()
        self.assertGreaterEqual(len(docs), 1)
        first_doc = docs[0]
        self.assertIsNotNone(first_doc.get('download_url'))

        # 2. Download the file via download_url
        download_res = self.client.get(first_doc['download_url'])
        self.assertEqual(download_res.status_code, 200)
        self.assertIn(b'%PDF-1.4', download_res.data)
        print("[OK] Compliance Document File Download & Serving Test Passed!")

    def test_26_compliance_requirements_enrichment_and_signed_state(self):
        # Fetch requirements and check compliance_docs structure
        res = self.client.get('/api/requirements')
        self.assertEqual(res.status_code, 200)
        reqs = res.get_json()
        req1 = next(r for r in reqs if r['id'] == 1)
        self.assertIn('compliance_docs', req1)
        self.assertIn('client_nda', req1['compliance_docs'])
        client_nda_doc = req1['compliance_docs']['client_nda']
        self.assertEqual(client_nda_doc['is_signed'], 1)
        self.assertIsNotNone(client_nda_doc.get('uploaded_by'))
        self.assertIsNotNone(client_nda_doc.get('remark'))
        self.assertEqual(req1['client_nda_shared'], 1)
        print("[OK] Requirements Compliance Enrichment & Signed State Test Passed!")

    def test_27_compliance_database_center_table(self):
        # Test Database Explorer endpoint for compliance_documents table
        res = self.client.get('/api/database/table/compliance_documents')
        self.assertEqual(res.status_code, 200)
        rows = res.get_json()
        self.assertIsInstance(rows, list)
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn('uploaded_by', rows[0])
        self.assertIn('remark', rows[0])
        print("[OK] Compliance Documents Database Explorer Table Test Passed!")

    def test_28_login_via_corporate_email(self):
        # 1. Login with Admin corporate email
        res1 = self.client.post('/api/auth/login', json={
            'username': 'admin@keydynamicssolutions.com',
            'password': 'Admin@123'
        })
        self.assertEqual(res1.status_code, 200)
        user1 = res1.get_json()['user']
        self.assertEqual(user1['role'], 'Admin')
        self.assertEqual(user1['email'], 'admin@keydynamicssolutions.com')
        self.assertTrue(user1['rights']['can_access_admin'])

        # 2. Login with Manager corporate email
        res2 = self.client.post('/api/auth/login', json={
            'username': 'manager@keydynamicssolutions.com',
            'password': 'Manager@123'
        })
        self.assertEqual(res2.status_code, 200)
        user2 = res2.get_json()['user']
        self.assertEqual(user2['role'], 'Manager')
        self.assertEqual(user2['email'], 'manager@keydynamicssolutions.com')
        self.assertTrue(user2['rights']['can_post_comments'])
        self.assertFalse(user2['rights']['can_access_admin'])

        # 3. Login with User corporate email
        res3 = self.client.post('/api/auth/login', json={
            'username': 'user@keydynamicssolutions.com',
            'password': 'User@123'
        })
        self.assertEqual(res3.status_code, 200)
        user3 = res3.get_json()['user']
        self.assertEqual(user3['role'], 'User')
        self.assertEqual(user3['email'], 'user@keydynamicssolutions.com')
        print("[OK] Corporate Email Login Test Passed!")

    def test_29_microsoft_dynamics_sso_login(self):
        # Authenticate via Microsoft Dynamics 365 Enterprise SSO endpoint
        res = self.client.post('/api/auth/microsoft-login', json={
            'email': 'admin@keydynamicssolutions.com'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['auth_provider'], 'microsoft_dynamics_365')
        self.assertEqual(data['user']['email'], 'admin@keydynamicssolutions.com')
        self.assertEqual(data['user']['role'], 'Admin')
        print("[OK] Microsoft Dynamics 365 Enterprise SSO Login Test Passed!")

    def test_30_admin_create_user_and_manager_with_rights(self):
        # 1. Login as Admin
        self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'Admin@123'
        })

        # Ensure test user is not already present from a previous run
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = 'priya.nair' OR email = 'priya.nair@keydynamicssolutions.com'")
        conn.commit()
        conn.close()

        # 2. Admin creates a Manager with custom rights
        manager_data = {
            'username': 'priya.nair',
            'full_name': 'Priya Nair',
            'email': 'priya.nair@keydynamicssolutions.com',
            'password': 'Priya@123',
            'role': 'Manager',
            'rights': {
                'can_manage_requirements': True,
                'can_manage_candidates': True,
                'can_post_comments': True,
                'can_manage_compliance': True,
                'can_view_reports': True,
                'can_access_database': False,
                'can_access_admin': False
            }
        }
        res_mgr = self.client.post('/api/admin/users', json=manager_data)
        self.assertEqual(res_mgr.status_code, 201)
        created_mgr = res_mgr.get_json()['user']
        self.assertEqual(created_mgr['username'], 'priya.nair')
        self.assertEqual(created_mgr['role'], 'Manager')
        self.assertEqual(created_mgr['rights']['can_post_comments'], True)
        self.assertEqual(created_mgr['rights']['can_access_admin'], False)

        # 3. Verify the newly created Manager can log in with corporate email
        res_login = self.client.post('/api/auth/login', json={
            'username': 'priya.nair@keydynamicssolutions.com',
            'password': 'Priya@123'
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.get_json()['user']['role'], 'Manager')
        print("[OK] Admin Create Manager with Custom Rights Test Passed!")

    def test_31_admin_update_user_role_rights_and_password_reset(self):
        # 1. Login as Admin
        self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'Admin@123'
        })

        # 2. Fetch all users to find priya.nair
        users_res = self.client.get('/api/admin/users')
        self.assertEqual(users_res.status_code, 200)
        users = users_res.get_json()
        target = next(u for u in users if u['username'] == 'priya.nair')

        # 3. Update Priya's role to Admin and grant can_access_admin
        new_rights = target['rights'].copy()
        new_rights['can_access_admin'] = True
        update_res = self.client.put(f'/api/admin/users/{target["id"]}', json={
            'full_name': 'Priya Nair (Lead)',
            'role': 'Admin',
            'rights': new_rights,
            'status': 'Active'
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['user']['role'], 'Admin')

        # 4. Admin resets Priya's password
        reset_res = self.client.post(f'/api/admin/users/{target["id"]}/reset-password', json={
            'new_password': 'NewPassword@456',
            'confirm_password': 'NewPassword@456'
        })
        self.assertEqual(reset_res.status_code, 200)

        # 5. Login with new reset password
        login_res = self.client.post('/api/auth/login', json={
            'username': 'priya.nair@keydynamicssolutions.com',
            'password': 'NewPassword@456'
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.get_json()['user']['role'], 'Admin')
        print("[OK] Admin Update User, Rights & Password Reset Test Passed!")

    def test_32_admin_panel_access_control(self):
        # 1. Login as regular User
        login_res = self.raw_client.post('/api/auth/login', json={
            'username': 'user',
            'password': 'User@123'
        })
        user_token = login_res.get_json().get('access_token')

        # 2. Try to access Admin Users API with regular user token -> Must return 403 Forbidden
        res_forbidden = self.raw_client.get('/api/admin/users', headers={'Authorization': f'Bearer {user_token}'})
        self.assertEqual(res_forbidden.status_code, 403)
        self.assertIn('error', res_forbidden.get_json())
        print("[OK] Admin Panel RBAC Access Control Test Passed!")

    def test_33_exchange_rate_settings(self):
        # 1. Login as admin
        self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'Admin@123'
        })

        # 2. Get settings
        res = self.client.get('/api/settings')
        self.assertEqual(res.status_code, 200)
        settings = res.get_json()
        self.assertIn('usd_inr_exchange_rate', settings)

        # 3. Update settings
        update_res = self.client.put('/api/settings', json={
            'usd_inr_exchange_rate': '85.50'
        })
        self.assertEqual(update_res.status_code, 200)
        updated = self.client.get('/api/settings').get_json()
        self.assertEqual(updated.get('usd_inr_exchange_rate'), '85.50')

        # Revert back to 84.00 default
        self.client.put('/api/settings', json={'usd_inr_exchange_rate': '84.00'})
        print("[OK] System Settings Exchange Rate API Test Passed!")

    def test_34_user_manual_removal_verification(self):
        # Verify index.html template and dist_website/index.html have no User Manual & Guide tab or section
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            template_html = f.read()
        self.assertNotIn('id="tab-documentation"', template_html)
        self.assertNotIn('id="sec-documentation"', template_html)
        self.assertNotIn('User Manual & Guide', template_html)

        with open('dist_website/index.html', 'r', encoding='utf-8') as f:
            dist_html = f.read()
        self.assertNotIn('id="tab-documentation"', dist_html)
        self.assertNotIn('id="sec-documentation"', dist_html)
        self.assertNotIn('User Manual & Guide', dist_html)
        print("[OK] User Manual Complete Removal Verification Test Passed!")

    def test_35_unauthenticated_api_rejection(self):
        # Protected endpoints must strictly return 401 Unauthorized without Bearer token
        endpoints = [
            ('/api/dashboard/stats', 'GET'),
            ('/api/requirements', 'GET'),
            ('/api/requirements', 'POST'),
            ('/api/candidates', 'GET'),
            ('/api/database/stats', 'GET'),
            ('/api/admin/users', 'GET'),
            ('/api/settings', 'GET')
        ]
        for url, method in endpoints:
            if method == 'GET':
                res = self.raw_client.get(url)
            else:
                res = self.raw_client.post(url, json={})
            self.assertEqual(res.status_code, 401, f"Endpoint {url} was not blocked without token!")
            err_data = res.get_json()
            self.assertEqual(err_data.get('code'), 'AUTH_REQUIRED')
        print("[OK] Backend Unauthenticated API Lockdown (401 Verification) Test Passed!")

    def test_36_invalid_token_rejection(self):
        res = self.raw_client.get('/api/dashboard/stats', headers={'Authorization': 'Bearer invalid.tampered.token'})
        self.assertEqual(res.status_code, 401)
        err_data = res.get_json()
        self.assertEqual(err_data.get('code'), 'INVALID_TOKEN')
        print("[OK] Invalid/Tampered Token Rejection Test Passed!")

if __name__ == '__main__':
    unittest.main()

