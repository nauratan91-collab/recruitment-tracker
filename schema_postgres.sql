-- =============================================================================
-- RECRUITPULSE: Job Requirement & Recruitment Pipeline Database Schema (PostgreSQL)
-- =============================================================================

-- 1. Table: job_requirements
CREATE TABLE IF NOT EXISTS job_requirements (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    end_client VARCHAR(255),
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    work_location_type VARCHAR(50) NOT NULL DEFAULT 'Hybrid', -- 'Remote', 'Work From Office', 'Hybrid'
    location_city VARCHAR(255),
    budget VARCHAR(100),
    open_positions INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Active',
    open_date DATE,
    close_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pg_job_client ON job_requirements(client_name);
CREATE INDEX IF NOT EXISTS idx_pg_job_status ON job_requirements(status);

-- 2. Table: compliance_records
CREATE TABLE IF NOT EXISTS compliance_records (
    id SERIAL PRIMARY KEY,
    job_requirement_id INTEGER NOT NULL UNIQUE REFERENCES job_requirements(id) ON DELETE CASCADE,
    client_nda_shared SMALLINT DEFAULT 0,
    client_msa_shared SMALLINT DEFAULT 0,
    vendor_nda_shared SMALLINT DEFAULT 0,
    vendor_msa_shared SMALLINT DEFAULT 0,
    consultant_nda_shared SMALLINT DEFAULT 0,
    consultant_msa_shared SMALLINT DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table: candidates
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    job_requirement_id INTEGER NOT NULL REFERENCES job_requirements(id) ON DELETE CASCADE,
    candidate_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    current_stage VARCHAR(50) NOT NULL DEFAULT 'Profile Shared',
    doj DATE,
    final_billing_rate VARCHAR(100),
    consultant_pay_rate VARCHAR(100),
    resume_filename VARCHAR(255),
    resume_original_name VARCHAR(255),
    notes TEXT,
    source_type VARCHAR(50) DEFAULT 'Internal',
    current_ctc VARCHAR(100),
    expected_ctc VARCHAR(100),
    notice_period VARCHAR(100),
    current_location VARCHAR(150),
    remarks TEXT,
    vendor_name VARCHAR(200),
    vendor_billing_rate VARCHAR(100),
    current_company VARCHAR(200),
    office_work_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pg_candidates_req ON candidates(job_requirement_id);
CREATE INDEX IF NOT EXISTS idx_pg_candidates_stage ON candidates(current_stage);

-- 4. Table: resumes
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    job_requirement_id INTEGER NOT NULL REFERENCES job_requirements(id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    file_data BYTEA,
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Table: users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'User',
    full_name VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pg_users_username ON users(username);
