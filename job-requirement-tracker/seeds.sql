-- =============================================================================
-- RECRUITPULSE: Sample Seed Data
-- =============================================================================

-- Insert Job Requirements
INSERT INTO job_requirements (id, client_name, end_client, job_title, job_description, work_location_type, location_city, budget, open_positions, status, open_date, close_date) VALUES
(1, 'Apex Tech Solutions', 'FinTech Global Inc.', 'Senior Full Stack Engineer (Python/React)', 'Looking for a Senior Full Stack Engineer to lead microservices development and modern React dashboard UI.', 'Hybrid', 'New York, NY', '$140,000 - $160,000 / year', 3, 'Active', '2026-09-01', NULL),
(2, 'CloudScale Systems', 'Healthcare Alliance', 'DevOps & Cloud Architect (AWS/Kubernetes)', 'Managing Multi-region AWS Cloud Infrastructure, CI/CD pipelines, and Kubernetes deployments.', 'Remote', 'Austin, TX', '$90 - $110 / hour', 2, 'Active', '2026-08-25', NULL),
(3, 'OmniCorp Consulting', 'Retail Dynamics', 'Data Engineer (Snowflake / PySpark)', 'Building ETL data pipelines and enterprise data warehouse solutions.', 'Work From Office', 'Chicago, IL', '$120,000 / year', 1, 'Active', '2026-09-10', NULL);

-- Insert Compliance Records (NDA & MSA)
INSERT INTO compliance_records (id, job_requirement_id, client_nda_shared, client_msa_shared, vendor_nda_shared, vendor_msa_shared, consultant_nda_shared, consultant_msa_shared) VALUES
(1, 1, 1, 1, 1, 0, 1, 1),
(2, 2, 1, 1, 1, 1, 1, 0),
(3, 3, 1, 0, 0, 0, 1, 0);

-- Insert Candidates
INSERT INTO candidates (id, job_requirement_id, candidate_name, email, phone, current_stage, doj, final_billing_rate, resume_filename, resume_original_name, source_type, current_ctc, expected_ctc, notice_period, current_location, remarks, vendor_name, vendor_billing_rate, current_company, office_work_type) VALUES
(1, 1, 'Alex Morgan', 'alex.morgan@email.com', '+1 555-0192', 'Final Selected', '2026-10-15', '$85/hr', 'sample_alex_morgan_resume.pdf', 'Alex_Morgan_Resume.pdf', 'Internal', '$120,000', '$145,000', '15 Days', 'New York, NY', 'Excellent Python/React hands-on assessment.', NULL, NULL, 'FinTech Labs', 'Hybrid'),
(2, 1, 'Brenda Vance', 'brenda.v@email.com', '+1 555-0183', '2nd Round', NULL, NULL, NULL, NULL, 'Vendor', NULL, NULL, '30 Days', 'Chicago, IL', NULL, 'Apex Talent Partners', '$75/hr', 'Cognizant', 'Remote'),
(3, 1, 'Carlos Diaz', 'carlos.d@email.com', '+1 555-0174', '1st Round', NULL, NULL, NULL, NULL, 'Internal', '$110,000', '$135,000', 'Immediate', 'Boston, MA', 'Strong system design skills.', NULL, NULL, 'TechNova', 'Hybrid'),
(4, 1, 'David Miller', 'david.m@email.com', '+1 555-0165', 'Shortlisted', NULL, NULL, NULL, NULL, 'Internal', '$105,000', '$125,000', '30 Days', 'Austin, TX', 'Solid profile, screened by recruiter.', NULL, NULL, 'InnoTech', 'Remote'),
(5, 1, 'Emily Watson', 'emily.w@email.com', '+1 555-0156', 'Profile Shared', NULL, NULL, NULL, NULL, 'Vendor', NULL, NULL, '60 Days', 'San Jose, CA', NULL, 'Global Staffing Inc.', '$80/hr', 'Wipro', 'Work From Office'),
(6, 2, 'Frank Wright', 'frank.w@email.com', '+1 555-0147', 'Final Selected', '2026-10-01', '$105/hr', 'sample_frank_wright_resume.pdf', 'Frank_Wright_DevOps.pdf', 'Internal', '$130,000', '$155,000', 'Immediate', 'Austin, TX', 'Top tier AWS & Kubernetes architect.', NULL, NULL, 'CloudScale Inc', 'Remote'),
(7, 2, 'Grace Hopper', 'grace.h@email.com', '+1 555-0138', '1st Round', NULL, NULL, NULL, NULL, 'Vendor', NULL, NULL, '15 Days', 'Seattle, WA', NULL, 'DevOps Force LLC', '$95/hr', 'Accenture', 'Remote');

-- Insert Default Users (Admin: Admin@123, Manager: Manager@123, User: User@123)
INSERT INTO users (id, username, password_hash, role, full_name) VALUES
(1, 'admin', 'scrypt:32768:8:1$oYyzG0Bxhyq3wVBR$538090afe92f152cf89222f22b95b17b67f1298e6c185e7b51b0fc1c71dc8372517a1968c138a3ff0ce4a08d2acb641829ace82caa7e5b81a0407966e2734164', 'Admin', 'System Administrator'),
(2, 'manager', 'scrypt:32768:8:1$9qQe5W0c02l4kR8o$1335bcfba1f94d936bb483c662e5da1e7655060ee46462c1ba5bbd2a8aebc5f87bc6e2ef307a508fa5ef1fecb7bbd944e8bc1a4a4b3d7a8ceef1dcaae73142da', 'Manager', 'Hiring Manager'),
(3, 'user', 'scrypt:32768:8:1$pnAIRgry81vqDD9C$a8077df06cacf991e793ae9583dee0faef1b5504372475d2df3745f4a492c424713595444434479c939bae8d03e86c287316d6562f2b4853c03418fdba9db83f', 'User', 'Recruiter User');

-- Insert Candidate Comments & Manager Notifications
INSERT INTO candidate_comments (id, candidate_id, job_requirement_id, author_name, author_role, comment_type, comment_text, is_notification) VALUES
(1, 1, 1, 'Hiring Manager', 'Manager', 'Notification', 'Shared profile for Alex Morgan looks exceptional. Please expedite final client interview.', 1),
(2, 2, 1, 'Hiring Manager', 'Manager', 'Feedback', 'Brenda cleared 1st round well. Please verify vendor markup and remote workstation setup.', 0);
