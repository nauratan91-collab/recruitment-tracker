-- =============================================================================
-- RECRUITPULSE: Job Requirement & Recruitment Pipeline Database Schema (SQLite)
-- Database Name: recruitment_tracker.db
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Table: job_requirements
-- Stores all job requirement details received from clients.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,                     -- Name of the hiring client
    end_client TEXT,                              -- Name of the end client (if subcontracting)
    job_title TEXT NOT NULL,                      -- Designation / Title of the open role
    job_description TEXT,                         -- Full Job Description (JD) text
    work_location_type TEXT NOT NULL DEFAULT 'Hybrid', -- 'Remote', 'Work From Office', 'Hybrid'
    location_city TEXT,                           -- City / State / Region
    budget TEXT,                                  -- Budget or target pay rate (e.g. '$140k/yr' or '$85/hr')
    open_positions INTEGER NOT NULL DEFAULT 1,    -- Total count of open vacancies
    status TEXT DEFAULT 'Active',                 -- 'Active', 'On Hold', 'Filled', 'Closed'
    open_date TEXT,                               -- Requirement Opening Date (YYYY-MM-DD)
    close_date TEXT,                              -- Requirement Closure Date (YYYY-MM-DD)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_req_client ON job_requirements(client_name);
CREATE INDEX IF NOT EXISTS idx_job_req_status ON job_requirements(status);
CREATE INDEX IF NOT EXISTS idx_job_req_location ON job_requirements(work_location_type);

-- -----------------------------------------------------------------------------
-- 2. Table: compliance_records
-- Tracks NDA and MSA legal compliance status across Client, Vendor, and Consultant.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS compliance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_requirement_id INTEGER NOT NULL UNIQUE,   -- Associated Job Requirement
    client_nda_shared INTEGER DEFAULT 0,          -- 1 = Shared/Signed, 0 = Pending
    client_msa_shared INTEGER DEFAULT 0,
    vendor_nda_shared INTEGER DEFAULT 0,
    vendor_msa_shared INTEGER DEFAULT 0,
    consultant_nda_shared INTEGER DEFAULT 0,
    consultant_msa_shared INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_compliance_req ON compliance_records(job_requirement_id);

-- -----------------------------------------------------------------------------
-- 3. Table: candidates
-- Tracks individual candidate profiles, recruitment stages, and placements.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_requirement_id INTEGER NOT NULL,          -- Associated Job Requirement
    candidate_name TEXT NOT NULL,                 -- Full Name of Candidate
    email TEXT,                                   -- Email Address
    phone TEXT,                                   -- Contact Phone Number
    current_stage TEXT NOT NULL DEFAULT 'Profile Shared', 
    -- Stages: 'Profile Shared', 'Shortlisted', '1st Round', '2nd Round', 'Final Selected', 'Rejected'
    doj TEXT,                                     -- Date of Joining / Project Start Date (YYYY-MM-DD)
    final_billing_rate TEXT,                      -- Confirmed Billing Rate to client (e.g. '$95/hr')
    consultant_pay_rate TEXT,                     -- Pay rate to consultant/vendor (e.g. '$70/hr')
    resume_filename TEXT,                         -- Saved file name on disk
    resume_original_name TEXT,                     -- Original uploaded file name
    notes TEXT,                                   -- General notes
    -- Candidate Sourcing Details
    source_type TEXT DEFAULT 'Internal',          -- Sourcing mode: 'Internal' or 'Vendor'
    current_ctc TEXT,                             -- Current CTC (Internal candidates)
    expected_ctc TEXT,                            -- Expected CTC (Internal candidates)
    notice_period TEXT,                           -- Notice Period (e.g. 'Immediate', '30 Days')
    current_location TEXT,                        -- Current Location of candidate
    remarks TEXT,                                 -- Screening remarks / recruiter notes
    vendor_name TEXT,                             -- Vendor / Agency Name (Vendor candidates)
    vendor_billing_rate TEXT,                     -- Vendor Billing / Pay Rate
    current_company TEXT,                         -- Current Employer of candidate
    office_work_type TEXT,                        -- Preferred work mode ('Remote', 'Hybrid', 'Work From Office')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_req ON candidates(job_requirement_id);
CREATE INDEX IF NOT EXISTS idx_candidates_stage ON candidates(current_stage);

-- -----------------------------------------------------------------------------
-- 4. Table: resumes
-- Dedicated resume storage in database supporting BLOB binaries & metadata.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_requirement_id INTEGER NOT NULL,          -- Linked Job Requirement
    candidate_id INTEGER,                         -- Linked Candidate Profile
    file_name TEXT NOT NULL,                      -- Stored disk name
    original_name TEXT NOT NULL,                  -- Original filename
    file_type TEXT,                               -- MIME type / Extension (e.g. 'pdf', 'docx')
    file_size INTEGER,                            -- File size in bytes
    file_data BLOB,                               -- Binary file content stored directly in database
    file_path TEXT,                               -- Local path backup
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_resumes_req ON resumes(job_requirement_id);
CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id);

-- -----------------------------------------------------------------------------
-- 5. Table: users
-- Authentication, passwords, and role-based access control (Admin & User).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,                -- Login username
    email TEXT UNIQUE,                            -- Key Dynamics / Microsoft Dynamics 365 Email
    password_hash TEXT NOT NULL,                  -- Securely hashed password
    role TEXT NOT NULL DEFAULT 'User',            -- 'Admin', 'Manager', or 'User'
    full_name TEXT,                               -- Display name
    rights TEXT,                                  -- JSON string of granular permissions/rights
    status TEXT DEFAULT 'Active',                 -- 'Active', 'Inactive'
    auth_provider TEXT DEFAULT 'Local',           -- 'Local', 'Microsoft 365'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- -----------------------------------------------------------------------------
-- 6. Table: candidate_comments
-- Profile reviews, feedback, and manager notifications on shared candidates.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidate_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,                -- Target Candidate Profile
    job_requirement_id INTEGER,                   -- Linked Job Requirement
    author_user_id INTEGER,                       -- Optional Author user id
    author_name TEXT NOT NULL,                    -- Author name (e.g. 'Hiring Manager')
    author_role TEXT NOT NULL DEFAULT 'Manager',  -- 'Manager', 'Admin', 'User'
    comment_type TEXT NOT NULL DEFAULT 'Comment', -- 'Comment', 'Notification', 'Feedback', 'Shortlist Decision'
    comment_text TEXT NOT NULL,                   -- Review / Notification content
    is_notification INTEGER DEFAULT 0,            -- 1 if high priority notification/alert
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_comments_cand ON candidate_comments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_comments_notif ON candidate_comments(is_notification);

-- -----------------------------------------------------------------------------
-- 7. Table: compliance_documents
-- Uploaded NDA & MSA signed documents, uploader tracking, and compliance remarks.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS compliance_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_requirement_id INTEGER NOT NULL,          -- Associated Job Requirement
    agreement_type TEXT NOT NULL,                 -- 'client_nda', 'client_msa', 'vendor_nda', 'vendor_msa', 'consultant_nda', 'consultant_msa'
    is_signed INTEGER DEFAULT 1,                  -- 1 = Signed, 0 = Pending
    file_name TEXT,                               -- Stored filename on disk
    original_name TEXT,                           -- Uploaded original document filename
    file_path TEXT,                               -- Full or relative filesystem path
    file_size INTEGER,                            -- File size in bytes
    uploaded_by TEXT NOT NULL,                    -- Uploader username or display name
    uploaded_by_role TEXT,                        -- Role of uploader ('Admin', 'Manager', 'User')
    remark TEXT,                                  -- Execution / compliance remarks
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_compliance_docs_req ON compliance_documents(job_requirement_id);
CREATE INDEX IF NOT EXISTS idx_compliance_docs_type ON compliance_documents(agreement_type);

