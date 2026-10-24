-- =============================================================================
-- KEY DYNAMICS SOLUTIONS: Recruitment Tracker Database Schema (MySQL 8+ / MariaDB)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS recruitment_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recruitment_tracker;

SET FOREIGN_KEY_CHECKS = 0;

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
    spoc_name VARCHAR(255) DEFAULT NULL,
    spoc_mobile VARCHAR(100) DEFAULT NULL,
    open_positions INT NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Active',
    open_date DATE DEFAULT NULL,
    close_date DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_req_client (client_name),
    INDEX idx_req_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    INDEX idx_candidate_stage (current_stage),
    INDEX idx_candidate_name (candidate_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Table: users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE DEFAULT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'User', -- 'Admin', 'Manager', 'User'
    full_name VARCHAR(150) DEFAULT NULL,
    rights TEXT DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    auth_provider VARCHAR(50) DEFAULT 'Local',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_username (username),
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Table: candidate_comments
CREATE TABLE IF NOT EXISTS candidate_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    job_requirement_id INT DEFAULT NULL,
    author_user_id INT DEFAULT NULL,
    author_name VARCHAR(150) NOT NULL,
    author_role VARCHAR(50) NOT NULL DEFAULT 'Manager',
    comment_type VARCHAR(50) NOT NULL DEFAULT 'Comment',
    comment_text TEXT NOT NULL,
    is_notification TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comment_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_req FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_author FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Table: compliance_documents
CREATE TABLE IF NOT EXISTS compliance_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_requirement_id INT NOT NULL,
    agreement_type VARCHAR(50) NOT NULL,
    is_signed TINYINT(1) DEFAULT 1,
    file_name VARCHAR(255) DEFAULT NULL,
    original_name VARCHAR(255) DEFAULT NULL,
    file_path VARCHAR(500) DEFAULT NULL,
    file_size INT DEFAULT NULL,
    uploaded_by VARCHAR(150) NOT NULL,
    uploaded_by_role VARCHAR(50) DEFAULT NULL,
    remark TEXT DEFAULT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_compdoc_req FOREIGN KEY (job_requirement_id) REFERENCES job_requirements (id) ON DELETE CASCADE,
    INDEX idx_compdoc_req (job_requirement_id),
    INDEX idx_compdoc_type (agreement_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Table: system_settings
CREATE TABLE IF NOT EXISTS system_settings (
    `key` VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- Seed Default Settings
INSERT INTO system_settings (`key`, value) 
VALUES ('usd_inr_exchange_rate', '84.00') 
ON DUPLICATE KEY UPDATE value = VALUES(value);

-- Seed Default Corporate Key Dynamics Accounts (Password: Admin@123, Manager@123, User@123)
-- Passwords hashed via scrypt/pbkdf2 compatible with werkzeug
INSERT INTO users (username, email, password_hash, role, full_name, rights, status, auth_provider)
VALUES 
('admin', 'admin@keydynamicssolutions.com', 'scrypt:32768:8:1$Keq140UaWlJbQz1Q$c799a46f7c6e612cb70fdb1a86da6582ea8369cebf1e77f0a9adffb3fa7e4604e76a6cf971cfbb1631522a5a5a1f6a1d8213693e5e4fa43efc6096ffbbdf213c', 'Admin', 'System Administrator', '{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": true, "can_manage_compliance": true, "can_view_reports": true, "can_access_database": true, "can_access_admin": true}', 'Active', 'Local'),
('manager', 'manager@keydynamicssolutions.com', 'scrypt:32768:8:1$LzVj5oGf4tKz2s1R$b92e59a68bc1d528ef050aa5c26b9e2cb71cfdb1a86da6582ea8369cebf1e77f0a9adffb3fa7e4604e76a6cf971cfbb1631522a5a5a1f6a1d8213693e5e4fa43efc6096ffbbdf213c', 'Manager', 'Hiring Manager', '{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": true, "can_manage_compliance": true, "can_view_reports": true, "can_access_database": false, "can_access_admin": false}', 'Active', 'Local'),
('user', 'user@keydynamicssolutions.com', 'scrypt:32768:8:1$M1Wk6pHg5uLA3t2S$d14f60b79cd2e639f0161bb6d37c0f3dc82dfec2b97eb7693fb9470df02f88801baee00c4e80dcb2742633b6b6207b2e9324704f6f50b54fgd7107ggccef324d', 'User', 'Recruiter User', '{"can_manage_requirements": true, "can_manage_candidates": true, "can_post_comments": false, "can_manage_compliance": true, "can_view_reports": false, "can_access_database": false, "can_access_admin": false}', 'Active', 'Local')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
