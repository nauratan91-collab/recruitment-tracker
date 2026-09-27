BEGIN TRANSACTION;
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
        );
INSERT INTO "candidates" VALUES(1,1,'Alex Morgan','alex.morgan@email.com','+1 555-0192','Final Selected','2026-10-15','$85/hr','sample_alex_morgan_resume.pdf','Alex_Morgan_Resume.pdf',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(2,1,'Brenda Vance','brenda.v@email.com','+1 555-0183','2nd Round','','','','',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(3,1,'Carlos Diaz','carlos.d@email.com','+1 555-0174','1st Round','','','','',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(4,1,'David Miller','david.m@email.com','+1 555-0165','Shortlisted','','','','',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(5,1,'Emily Watson','emily.w@email.com','+1 555-0156','Profile Shared','','','','',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(6,2,'Frank Wright','frank.w@email.com','+1 555-0147','Final Selected','2026-10-01','$105/hr','sample_frank_wright_resume.pdf','Frank_Wright_DevOps.pdf',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(7,2,'Grace Hopper','grace.h@email.com','+1 555-0138','1st Round','','','','',NULL,'2026-09-17 06:58:28','2026-09-17 06:58:28');
INSERT INTO "candidates" VALUES(8,1,'Samantha Reed','samantha.r@email.com','+1 555-9876','Final Selected','2026-11-01','$90/hr','20260917122933_samantha_resume.pdf','samantha_resume.pdf',NULL,'2026-09-17 06:59:33','2026-09-17 06:59:33');
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
INSERT INTO "compliance_records" VALUES(1,1,1,1,1,0,1,1,'2026-09-17 06:58:28');
INSERT INTO "compliance_records" VALUES(2,2,1,1,1,1,1,0,'2026-09-17 06:58:28');
INSERT INTO "compliance_records" VALUES(3,3,1,0,0,0,1,0,'2026-09-17 06:58:28');
INSERT INTO "compliance_records" VALUES(4,4,1,1,1,0,1,1,'2026-09-17 06:59:16');
INSERT INTO "compliance_records" VALUES(5,5,1,1,1,0,1,1,'2026-09-17 06:59:33');
INSERT INTO "compliance_records" VALUES(6,6,1,0,0,0,0,0,'2026-09-17 08:42:02');
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
        );
INSERT INTO "job_requirements" VALUES(1,'Apex Tech Solutions','FinTech Global Inc.','Senior Full Stack Engineer (Python/React)','Looking for a Senior Full Stack Engineer to lead microservices development and modern React dashboard UI.','Hybrid','New York, NY','$140,000 - $160,000 / year',3,'Active','2026-09-17 06:58:28');
INSERT INTO "job_requirements" VALUES(2,'CloudScale Systems','Healthcare Alliance','DevOps & Cloud Architect (AWS/Kubernetes)','Managing Multi-region AWS Cloud Infrastructure, CI/CD pipelines, and Kubernetes deployments.','Remote','Austin, TX','$90 - $110 / hour',2,'Active','2026-09-17 06:58:28');
INSERT INTO "job_requirements" VALUES(3,'OmniCorp Consulting','Retail Dynamics','Data Engineer (Snowflake / PySpark)','Building ETL data pipelines and enterprise data warehouse solutions.','Work From Office','Chicago, IL','$120,000 / year',1,'Active','2026-09-17 06:58:28');
INSERT INTO "job_requirements" VALUES(4,'Test Global Corp','Test Sub-Client','Senior Python Developer','Building AI API integration services.','Remote','San Francisco, CA','$150,000 / year',2,'Active','2026-09-17 06:59:16');
INSERT INTO "job_requirements" VALUES(5,'Test Global Corp','Test Sub-Client','Senior Python Developer','Building AI API integration services.','Remote','San Francisco, CA','$150,000 / year',2,'Active','2026-09-17 06:59:33');
INSERT INTO "job_requirements" VALUES(6,'NSquare ','xyz','Data & BI','Lead II – Data Engineering (Data Architecture) Experience: 8-14 Years Role Summary Lead the design, implementation, and governance of enterprise data architecture to support scalable, secure, and high-performing data platforms. Drive data modeling, integration, governance, and analytics initiatives while enabling business intelligence and data-driven decision-making across the organization. Key Responsibilities Design and implement enterprise-wide data architecture, data models, and integration frameworks. Define data standards, data governance policies, metadata management, and data quality processes. Architect and optimize modern data platforms, data lakes, data warehouses, and analytical solutions. Collaborate with business and technology stakeholders to translate business requirements into scalable data solutions. Lead the design of batch, real-time, and event-driven data integration patterns. Establish data lineage, master data management, and reference data strategies. Ensure compliance with data security, privacy, regulatory, and audit requirements. Provide technical leadership, architecture reviews, and mentoring to data engineering teams. Create and maintain architecture documentation, design standards, and best practices. Mandatory Skills Strong experience in Data Architecture, Data Modeling, and Data Governance. Expertise in designing enterprise data platforms, data warehouses, and data lakes. Hands-on experience with Azure Data Services (Azure Data Lake, Synapse Analytics, Databricks, Azure SQL). Strong SQL and data integration experience with large-scale enterprise datasets. Experience with ETL/ELT frameworks and modern data engineering practices. Knowledge of master data management, metadata management, and data quality frameworks. Experience supporting analytics and reporting solutions using Power BI or similar BI platforms. Strong stakeholder management, solution design, and technical leadership skills. Preferred Skills Experience with cloud-native data architectures and event-driven platforms. Exposure to AI/ML data platforms and advanced analytics environments. Azure Data Engineering/Data Architecture certifications. Experience in enterprise transformation and modernization programs. Skill Group: Data Architecture Role: Lead II – Data Engineering Employment Type: Full-Time Provide your feedback on BizChat','Remote','','open',1,'Active','2026-09-17 08:25:12');
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
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('job_requirements',6);
INSERT INTO "sqlite_sequence" VALUES('compliance_records',7);
INSERT INTO "sqlite_sequence" VALUES('candidates',8);
COMMIT;