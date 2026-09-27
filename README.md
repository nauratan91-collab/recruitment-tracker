# Key Dynamics Solutions — Enterprise Recruitment & Job Requirement Portal

An enterprise-grade Recruitment & Talent Management Portal built with **Python Flask**, **SQLite**, and **Tailwind CSS**. It provides complete end-to-end recruitment tracking, multi-currency budget configuration (INR ₹ / USD $), candidate pipelines, compliance (NDA/MSA) document management, and dynamic Role-Based Access Control (RBAC).

---

## 🗄️ Database & Pre-Seeded Data Included

This repository includes the complete SQLite database and SQL dump ready out of the box:
- **`recruitment_tracker.db`**: Live SQLite database with all tables, active job requisitions, candidate profiles, and settings.
- **`recruitment_tracker_dump.sql`**: Full portable SQL dump (schema + table data) compatible with SQLite, MySQL, and PostgreSQL converters.
- **`schema.sql`** & **`seeds.sql`**: Standalone DDL schema and seeding script.

### Default Login Accounts:
| Role | Email / Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@keydynamicssolutions.com` | `Admin@123` | Full access to all 7 modules + Admin Panel + Exchange Rate settings |
| **Hiring Manager** | `manager@keydynamicssolutions.com` | `Manager@123` | Requisitions, Candidates, Notes, Compliance & Reports |
| **Recruiter / Staff** | `user@keydynamicssolutions.com` | `User@123` | Requisitions, Candidate profiles & Compliance view |

*(Also supports 1-Click login using Microsoft Dynamics 365 Enterprise SSO)*

---

## 🚀 Key Features

1. **Job Requirement & Requisition Tracker**:
   - Track Open Positions, Status (Active, On Hold, Filled, Closed), SPOC Manager, and Location.
   - **Dual Currency Budget/Rate**: Set budgets in Rupees (₹ INR) or Dollars ($ USD) with frequency options (`/year`, `LPA`, `/hr`, `/month`, `Fixed`) with live dual currency preview.
2. **Interactive Candidate Pipeline**:
   - Stages: Profile Shared ➔ Shortlisted ➔ 1st Round ➔ 2nd Round ➔ Final Selected / Placed ➔ Rejected.
   - Sourcing channel tracking: **Internal Sourcing** (CTC, ECTC, Notice Period, Location) vs **Vendor Sourcing** (Partner Agency, Billing Rate).
3. **Legal Compliance & Document Management**:
   - Manage Client NDA/MSA, Vendor NDA/MSA, and Consultant NDA/MSA.
   - Upload, preview, modify, and delete executed legal agreements with audit timestamps.
4. **Universal Dual Currency Display (INR ₹ / USD $)**:
   - Configurable live USD/INR exchange rate in Admin Panel (default 1 USD = ₹84.00) with instant recalculation across all views.
5. **Dynamic Role-Based Access Control (RBAC)**:
   - Admins can customize user roles, activate/deactivate accounts, and adjust granular permissions dynamically.
6. **Zero-Backend Standalone Web Engine**:
   - Includes standalone `dist_website/index.html` with an embedded client-side database engine that runs 100% serverless on GitHub Pages, Vercel, Netlify, or direct double-click in browser!

---

## 💻 Local Setup & Running Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```
Open **http://127.0.0.1:5000** in your browser.

### 4. Run automated test suite
```bash
python -m unittest test_app.py
```

---

## 🌐 Deploy to GitHub Pages / Vercel / Netlify
- To deploy statically without a server, simply publish the files inside `dist_website/` or root `vercel.json`.
- The autonomous client-side engine in `dist_website/index.html` runs with zero server dependencies and preserves full CRUD capability using persistent browser storage.

---
© 2026 Key Dynamics Solutions Private Limited. All rights reserved.
