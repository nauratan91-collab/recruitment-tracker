BEGIN TRANSACTION;
CREATE TABLE candidate_comments (
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
        );
INSERT INTO "candidate_comments" VALUES(1,1,1,NULL,'Hiring Manager','Manager','Notification','Candidate Alex Morgan profile is shortlisted for Apex Tech Solutions.',1,'2026-09-23 15:36:32');
INSERT INTO "candidate_comments" VALUES(2,3,2,NULL,'Hiring Manager','Manager','Notification','Candidate Frank Wright profile is shortlisted for CloudScale Systems.',1,'2026-09-23 15:36:32');
INSERT INTO "candidate_comments" VALUES(3,1,1,3,'Hiring Manager','Manager','Feedback','Candidate assessed well in system architecture and Python microservices.',0,'2026-09-23 16:15:38');
INSERT INTO "candidate_comments" VALUES(4,1,1,3,'Hiring Manager','Manager','Notification','ACTION REQUIRED: Please arrange 2nd technical panel interview with client lead.',1,'2026-09-23 16:15:38');
INSERT INTO "candidate_comments" VALUES(5,1,1,3,'Hiring Manager','Manager','Feedback','Candidate assessed well in system architecture and Python microservices.',0,'2026-09-23 16:51:09');
INSERT INTO "candidate_comments" VALUES(6,1,1,3,'Hiring Manager','Manager','Notification','ACTION REQUIRED: Please arrange 2nd technical panel interview with client lead.',1,'2026-09-23 16:51:09');
INSERT INTO "candidate_comments" VALUES(7,1,1,3,'Hiring Manager','Manager','Feedback','Candidate assessed well in system architecture and Python microservices.',0,'2026-09-23 17:05:23');
INSERT INTO "candidate_comments" VALUES(8,1,1,3,'Hiring Manager','Manager','Notification','ACTION REQUIRED: Please arrange 2nd technical panel interview with client lead.',1,'2026-09-23 17:05:23');
CREATE TABLE candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_requirement_id INTEGER NOT NULL,
            candidate_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            current_stage TEXT NOT NULL DEFAULT 'Profile Shared', 
            -- Stages: 'Profile Shared', 'Shortlisted', '1st Round', '2nd Round', 'Final Selected', 'Rejected'
            doj TEXT, -- Date of Joining / Project Start Date
            final_billing_rate TEXT,
            resume_filename TEXT,
            resume_original_name TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, consultant_pay_rate TEXT, source_type TEXT DEFAULT 'Internal', current_ctc TEXT, expected_ctc TEXT, notice_period TEXT, current_location TEXT, remarks TEXT, vendor_name TEXT, vendor_billing_rate TEXT, current_company TEXT, office_work_type TEXT,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
        );
INSERT INTO "candidates" VALUES(1,1,'Alex Morgan','alex.morgan@email.com','+1 555-0192','Final Selected','2026-10-15','$85/hr','sample_alex_morgan.pdf','Alex_Morgan_Resume.pdf',NULL,'2026-09-23 15:36:32','2026-09-23 17:05:22','$65/hr','Internal','$115,000','$140,000','15 Days','New York, NY','Exceptional fit for Lead Engineer.','','','','');
INSERT INTO "candidates" VALUES(2,1,'Brenda Vance','brenda.v@email.com','+1 555-0183','2nd Round','','','','',NULL,'2026-09-23 15:36:32','2026-09-23 15:36:32',NULL,'Internal','$115,000','$135,000','30 Days','Jersey City, NJ',NULL,NULL,NULL,NULL,NULL);
INSERT INTO "candidates" VALUES(3,2,'Frank Wright','frank.w@email.com','+1 555-0147','Shortlisted','','$105/hr','sample_frank_wright.pdf','Frank_Wright_DevOps.pdf',NULL,'2026-09-23 15:36:32','2026-09-23 15:36:32',NULL,'Vendor','$90/hr','$105/hr','Immediate','Dallas, TX',NULL,'CloudTalent Inc.',NULL,NULL,NULL);
INSERT INTO "candidates" VALUES(4,3,'Carlos Diaz','carlos.d@email.com','+1 555-0174','1st Round','','','','',NULL,'2026-09-23 15:36:32','2026-09-23 15:36:32',NULL,'Internal','$105,000','$120,000','30 Days','Chicago, IL',NULL,NULL,NULL,NULL,NULL);
INSERT INTO "candidates" VALUES(5,4,'Neha Gupta','neha.gupta@example.com','+91 95456 78901','Profile Shared','','₹26,00,000/yr','','',NULL,'2026-09-23 15:36:32','2026-09-23 15:36:32',NULL,'Internal','₹21,00,000','₹26,00,000','30 Days','Bangalore, India',NULL,NULL,NULL,NULL,NULL);
INSERT INTO "candidates" VALUES(6,1,'Samantha Reed','samantha.r@email.com','+1 555-9876','Final Selected','2026-11-01','$90/hr','20260923214535_samantha_resume.pdf','samantha_resume.pdf',NULL,'2026-09-23 16:15:35','2026-09-23 16:15:35','','Internal','','','','','','','','','');
INSERT INTO "candidates" VALUES(7,1,'Rohan Sharma','rohan.sharma@email.com','+91 9876543210','Profile Shared','','','','',NULL,'2026-09-23 16:15:38','2026-09-23 16:15:38','','Internal','₹18 LPA','₹24 LPA','30 Days','Bangalore, India','Strong background in Python backend, cleared initial technical screening.','','','','');
INSERT INTO "candidates" VALUES(8,1,'Vikram Mehra','vikram.m@email.com','+1 408-555-0199','Shortlisted','','','','',NULL,'2026-09-23 16:15:38','2026-09-23 16:15:38','','Vendor','','','','','','Apex Talent Partners','$85/hr','Infosys Technologies','Hybrid');
INSERT INTO "candidates" VALUES(9,1,'Samantha Reed','samantha.r@email.com','+1 555-9876','Final Selected','2026-11-01','$90/hr','20260923222107_samantha_resume.pdf','samantha_resume.pdf',NULL,'2026-09-23 16:51:07','2026-09-23 16:51:07','','Internal','','','','','','','','','');
INSERT INTO "candidates" VALUES(10,1,'Rohan Sharma','rohan.sharma@email.com','+91 9876543210','Profile Shared','','','','',NULL,'2026-09-23 16:51:09','2026-09-23 16:51:09','','Internal','₹18 LPA','₹24 LPA','30 Days','Bangalore, India','Strong background in Python backend, cleared initial technical screening.','','','','');
CREATE TABLE compliance_documents (
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
        );
INSERT INTO "compliance_documents" VALUES(1,1,'client_nda',1,'signed_client_nda_apex.pdf','Apex_Client_NDA_Executed.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\signed_client_nda_apex.pdf',1024,'Hiring Manager','Manager','Signed bilateral NDA executed with Legal VP on Sep 02, 2026.','2026-09-23 15:36:32');
INSERT INTO "compliance_documents" VALUES(2,1,'client_msa',1,'signed_client_msa_apex.pdf','Apex_Master_Services_Agreement_Signed.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\signed_client_msa_apex.pdf',1024,'System Administrator','Admin','Master Services Agreement approved for FY 2026-2027.','2026-09-23 15:36:32');
INSERT INTO "compliance_documents" VALUES(3,2,'vendor_nda',1,'signed_vendor_nda_cloudscale.pdf','CloudScale_Vendor_Subcontractor_NDA.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\signed_vendor_nda_cloudscale.pdf',1024,'Recruiter User','User','Vendor NDA signed on partner onboarding.','2026-09-23 15:36:32');
INSERT INTO "compliance_documents" VALUES(4,3,'consultant_nda',1,'signed_consultant_nda_omnicorp.pdf','Consultant_Confidentiality_NDA.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\signed_consultant_nda_omnicorp.pdf',1024,'Hiring Manager','Manager','Consultant signed NDA prior to client interview.','2026-09-23 15:36:32');
INSERT INTO "compliance_documents" VALUES(5,4,'client_nda',1,'signed_client_nda_fintech.pdf','FinTech_Bilateral_NDA_Executed.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\signed_client_nda_fintech.pdf',1024,'System Administrator','Admin','Executed NDA valid for all APAC regional delivery operations.','2026-09-23 15:36:32');
INSERT INTO "compliance_documents" VALUES(6,3,'vendor_msa',1,'doc_6_20260923_211544_Vikalp_Singh_KDS_Updated_12.docx','Vikalp_Singh_KDS_Updated_12.docx','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\doc_6_20260923_211544_Vikalp_Singh_KDS_Updated_12.docx',61709,'System Administrator','Admin','','2026-09-23 15:45:29');
INSERT INTO "compliance_documents" VALUES(7,1,'client_nda',1,'client_nda_req_1_20260923_214538_Executed_Client_NDA_2026.pdf','Executed_Client_NDA_2026.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\client_nda_req_1_20260923_214538_Executed_Client_NDA_2026.pdf',41,'Hiring Manager','Manager','Client NDA executed and signed by Legal Counsel on 18-Sep-2026.','2026-09-23 16:15:38');
INSERT INTO "compliance_documents" VALUES(8,1,'client_nda',1,'client_nda_req_1_20260923_222110_Executed_Client_NDA_2026.pdf','Executed_Client_NDA_2026.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\client_nda_req_1_20260923_222110_Executed_Client_NDA_2026.pdf',41,'Hiring Manager','Manager','Client NDA executed and signed by Legal Counsel on 18-Sep-2026.','2026-09-23 16:51:10');
INSERT INTO "compliance_documents" VALUES(9,1,'client_nda',1,'client_nda_req_1_20260923_223524_Executed_Client_NDA_2026.pdf','Executed_Client_NDA_2026.pdf','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\compliance_docs\client_nda_req_1_20260923_223524_Executed_Client_NDA_2026.pdf',41,'Hiring Manager','Manager','Client NDA executed and signed by Legal Counsel on 18-Sep-2026.','2026-09-23 17:05:24');
CREATE TABLE compliance_records (
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
        );
INSERT INTO "compliance_records" VALUES(1,1,1,1,1,0,1,1,'2026-09-23 17:05:24');
INSERT INTO "compliance_records" VALUES(2,2,1,1,1,1,1,0,'2026-09-23 15:36:32');
INSERT INTO "compliance_records" VALUES(3,3,1,0,0,1,1,0,'2026-09-23 15:45:44');
INSERT INTO "compliance_records" VALUES(4,4,1,1,0,0,0,0,'2026-09-23 15:36:32');
CREATE TABLE job_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            end_client TEXT,
            job_title TEXT NOT NULL,
            job_description TEXT,
            work_location_type TEXT NOT NULL, -- Remote, Work From Office, Hybrid
            location_city TEXT,
            budget TEXT,
            open_positions INTEGER NOT NULL DEFAULT 1,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , open_date TEXT, close_date TEXT, spoc_name TEXT, spoc_mobile TEXT, updated_at TIMESTAMP);
INSERT INTO "job_requirements" VALUES(1,'Apex Tech Solutions','FinTech Global Inc.','Senior Full Stack Engineer (Python/React)','Lead microservices development and modern React dashboard UI for enterprise financial services platform.','Hybrid','New York, NY','$140,000 - $160,000 / year',3,'Active','2026-09-23 15:36:32','2026-09-01',NULL,'Rahul Sharma (Lead Account Mgr)','+91 98765 43210',NULL);
INSERT INTO "job_requirements" VALUES(2,'CloudScale Systems','Healthcare Alliance','DevOps & Cloud Architect (AWS/Kubernetes)','Managing multi-region AWS cloud infrastructure, automated CI/CD pipelines, and high-availability Kubernetes deployments.','Remote','Austin, TX','$90 - $110 / hour',2,'Active','2026-09-23 15:36:32','2026-09-05',NULL,'Priya Patel (Sr. Delivery Lead)','+91 98123 45678',NULL);
INSERT INTO "job_requirements" VALUES(3,'OmniCorp Consulting','Retail Dynamics','Data Engineer (Snowflake / PySpark)','Building real-time ETL pipelines and scalable modern data lakehouse architectures.','Work From Office','Chicago, IL','$120,000 / year',1,'Active','2026-09-23 15:36:32','2026-09-10',NULL,'Amit Verma (Talent Acquisition)','+91 97234 56789',NULL);
INSERT INTO "job_requirements" VALUES(4,'FinTech Innovations Pvt Ltd','Key Dynamics Enterprise Group','Dynamics 365 & Power Platform Consultant','Implementing Dynamics 365 CRM/ERP modules and custom automated business workflows.','Hybrid','Bangalore, India','₹24,00,000 - ₹30,00,000 / annum',2,'Active','2026-09-23 15:36:32','2026-09-15',NULL,'Vikram Singh (Client Director)','+91 96345 67890',NULL);
CREATE TABLE resumes (
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
        );
INSERT INTO "resumes" VALUES(1,1,6,'20260923214535_samantha_resume.pdf','samantha_resume.pdf','pdf',34,X'44756D6D792053616D616E746861205265656420526573756D6520436F6E74656E74','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\resumes\20260923214535_samantha_resume.pdf','2026-09-23 16:15:35');
INSERT INTO "resumes" VALUES(2,1,9,'20260923222107_samantha_resume.pdf','samantha_resume.pdf','pdf',34,X'44756D6D792053616D616E746861205265656420526573756D6520436F6E74656E74','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\resumes\20260923222107_samantha_resume.pdf','2026-09-23 16:51:07');
INSERT INTO "resumes" VALUES(3,1,NULL,'20260923223517_samantha_resume.pdf','samantha_resume.pdf','pdf',34,X'44756D6D792053616D616E746861205265656420526573756D6520436F6E74656E74','C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker\uploads\resumes\20260923223517_samantha_resume.pdf','2026-09-23 17:05:17');
CREATE TABLE system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
INSERT INTO "system_settings" VALUES('usd_inr_exchange_rate','98.00','2026-09-23 17:17:59');
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User', -- 'Admin' or 'User'
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , email TEXT, rights TEXT, status TEXT DEFAULT 'Active', auth_provider TEXT DEFAULT 'Local');
INSERT INTO "users" VALUES(1,'admin','scrypt:32768:8:1$eR20ArcmNQpes9ax$a3c9b1fffbb1e662a31d2daf4bf1d70fd36bcda84ae3651751e890c153eeb99ecfac05d0004177b7e5b446e34f26c82eefdf12c80a938053478bf55624c15fce','Admin','System Administrator','2026-09-17 11:07:15','2026-09-17 11:07:15','admin@keydynamicssolutions.com','{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": true, "can_manage_compliance": true, "can_view_reports": true, "can_access_database": true, "can_access_admin": true}','Active','Local');
INSERT INTO "users" VALUES(2,'user','scrypt:32768:8:1$gh3XVc8VXJLfhPDS$26e218cf5f42e2bdd05bbdf14903799757cd5f71da16df82c788183098ffa48b0534a767cee5932283c1410a91026a9332fc29f017d674cdece94f82cc296bbe','User','Recruiter User','2026-09-17 11:07:15','2026-09-23 17:05:22','user@keydynamicssolutions.com','{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": false, "can_manage_compliance": true, "can_view_reports": false, "can_access_database": false, "can_access_admin": false}','Active','Local');
INSERT INTO "users" VALUES(3,'manager','scrypt:32768:8:1$6Fl2kkA5QWp9KZjI$f27fc99dd3d557c8955873dd1f513b68cf17bc07a3cab33317ee7496fdaec93daaeb9e10bb199a33c3adf65d319f42493497e993514e2dc91960d10bf8cb59ca','Manager','Hiring Manager','2026-09-18 05:31:38','2026-09-18 05:31:38','manager@keydynamicssolutions.com','{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": true, "can_manage_compliance": true, "can_view_reports": true, "can_access_database": false, "can_access_admin": false}','Active','Local');
INSERT INTO "users" VALUES(4,'Shivam','scrypt:32768:8:1$5eQMuBTxpSqGmIRt$d76f6382cba3d3996d3363f048e4c9201cfccf36f5fa2f215e57096aa784b9e6c7719a6362e3fd82b56b49806fc6e9990cb5edd6498abd8a8fa72f80f8a75624','User','Kumar','2026-09-23 15:39:49','2026-09-23 15:39:49','styagi@keydynamicssolutions.com','{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": false, "can_manage_compliance": true, "can_view_reports": false, "can_access_database": false, "can_access_admin": false}','Active','Local');
INSERT INTO "users" VALUES(7,'priya.nair','scrypt:32768:8:1$v6yu26pgCVmLLA2k$00e06305146b81486a2b86d673104080b7bdc7dc5682007f63cfc2dc991dac10b48807c85df82fb1a862fedf637a1b748d4af4e875595a2bd497660ae4d0bfb5','Admin','Priya Nair (Lead)','2026-09-23 17:05:26','2026-09-23 17:05:27','priya.nair@keydynamicssolutions.com','{"can_access_admin": true, "can_access_database": false, "can_manage_candidates": true, "can_manage_compliance": true, "can_manage_requirements": true, "can_post_comments": true, "can_view_reports": true}','Active','Local');
CREATE INDEX idx_compliance_docs_req ON compliance_documents(job_requirement_id);
CREATE UNIQUE INDEX idx_users_email ON users(email);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('job_requirements',13);
INSERT INTO "sqlite_sequence" VALUES('compliance_records',13);
INSERT INTO "sqlite_sequence" VALUES('compliance_documents',9);
INSERT INTO "sqlite_sequence" VALUES('candidates',14);
INSERT INTO "sqlite_sequence" VALUES('candidate_comments',8);
INSERT INTO "sqlite_sequence" VALUES('users',7);
INSERT INTO "sqlite_sequence" VALUES('resumes',3);
COMMIT;
