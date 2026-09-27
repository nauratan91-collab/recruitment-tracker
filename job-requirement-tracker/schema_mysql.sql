-- =============================================================================
-- RECRUITPULSE: Job Requirement & Recruitment Pipeline Database Schema (MySQL / MariaDB)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS recruitment_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recruitment_tracker;

-- 1. Table: job_requirements
CREATE TABLE IF NOT EXISTS job_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    end_client VARCHAR(255) DEFAULT NULL,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT DEFAULT NULL,
    work_location_type ENUM('Remote', 'Work From Office', 'Hybrid') NOT NULL DEFAULT 'Hybrid',
    location_city VARCHAR(255) DEFAULT NULL,
    budget VARCHAR(100) DEFAULT NULL,
    open_positions INT NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Active',
    open_date DATE DEFAULT NULL,
    close_date DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_client_name (client_name),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- 2. Table: compliance_records
CREATE TABLE IF NOT EXISTS compliance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_requirement_id INT NOT NULL UNIQUE,
    client_nda_shared TINYINT(1) DEFAULT 0,
    client_msa_shared TINYINT(1) DEFAULT 0,
    vendor_nda_shared TINYINT(1) DEFAULT 0,
    vendor_msa_shared TINYINT(1) DEFAULT 0,
    consultant_nda_shared TINYINT(1) DEFAULT 0,
    consultant_msa_shared TINYINT(1) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_compliance_req FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Table: candidates
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_requirement_id INT NOT NULL,
    candidate_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) DEFAULT NULL,
    phone VARCHAR(50) DEFAULT NULL,
    current_stage ENUM('Profile Shared', 'Shortlisted', '1st Round', '2nd Round', 'Final Selected', 'Rejected') NOT NULL DEFAULT 'Profile Shared',
    doj DATE DEFAULT NULL,
    final_billing_rate VARCHAR(100) DEFAULT NULL,
    consultant_pay_rate VARCHAR(100) DEFAULT NULL,
    resume_filename VARCHAR(255) DEFAULT NULL,
    resume_original_name VARCHAR(255) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    source_type VARCHAR(50) DEFAULT 'Internal',
    current_ctc VARCHAR(100) DEFAULT NULL,
    expected_ctc VARCHAR(100) DEFAULT NULL,
    notice_period VARCHAR(100) DEFAULT NULL,
    current_location VARCHAR(150) DEFAULT NULL,
    remarks TEXT DEFAULT NULL,
    vendor_name VARCHAR(200) DEFAULT NULL,
    vendor_billing_rate VARCHAR(100) DEFAULT NULL,
    current_company VARCHAR(200) DEFAULT NULL,
    office_work_type VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidate_req FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    INDEX idx_stage (current_stage)
) ENGINE=InnoDB;

-- 4. Table: resumes
CREATE TABLE IF NOT EXISTS resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_requirement_id INT NOT NULL,
    candidate_id INT DEFAULT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) DEFAULT NULL,
    file_size INT DEFAULT NULL,
    file_data LONGBLOB DEFAULT NULL,
    file_path VARCHAR(500) DEFAULT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_resume_req FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    CONSTRAINT fk_resume_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Table: users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'User',
    full_name VARCHAR(150) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_username (username)
) ENGINE=InnoDB;
