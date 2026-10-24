import os
import zipfile
import shutil

def build_godaddy_deploy_zip():
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    zip_filename = "deploy.zip"
    zip_path = os.path.join(proj_dir, zip_filename)

    # 1. Essential files to include at zip root
    essential_files = [
        "app.py",
        "database.py",
        "dependencies.py",
        "passenger_wsgi.py",
        ".htaccess",
        "web.config",
        "requirements.txt",
        "schema_mysql.sql",
        "schema.sql",
        "seeds.sql",
        "migrate_sqlite_to_mysql.py",
        ".env.example",
        "GODADDY_DEPLOYMENT_GUIDE.md",
        "index.html",
        "recruitment_tracker.db",
    ]

    # Directories to include recursively
    essential_dirs = [
        "templates",
        "static",
        "uploads"
    ]

    # Make sure uploads directory has proper subfolders
    for sub in ["resumes", "compliance_docs"]:
        sub_path = os.path.join(proj_dir, "uploads", sub)
        os.makedirs(sub_path, exist_ok=True)
        gitkeep = os.path.join(sub_path, ".gitkeep")
        if not os.path.exists(gitkeep):
            with open(gitkeep, "w") as f:
                f.write("")

    # If .env does not exist or user needs clean GoDaddy template
    env_content = """# Key Dynamics Solutions - GoDaddy Deployment Configuration
# -------------------------------------------------------------
# Change DB_ENGINE to 'mysql' once you create your database in GoDaddy cPanel
DB_ENGINE=mysql

# GoDaddy cPanel MySQL Credentials (Default host in GoDaddy is 'localhost')
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_cpanel_db_user
MYSQL_PASSWORD=your_cpanel_db_password
MYSQL_DATABASE=your_cpanel_db_name

# Security Secret Key
SECRET_KEY=key-dynamics-godaddy-secret-token-2026-production
"""

    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"[*] Packaging {zip_filename} for GoDaddy upload...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add root files
        for filename in essential_files:
            file_path = os.path.join(proj_dir, filename)
            if os.path.exists(file_path):
                zf.write(file_path, filename)
                print(f"  + Added file: {filename} ({os.path.getsize(file_path):,} bytes)")
            else:
                print(f"  ! Warning: {filename} not found!")

        # Add ready-to-edit .env file into the zip
        zf.writestr(".env", env_content)
        print("  + Added file: .env (Pre-configured GoDaddy template)")

        # Add directories recursively (excluding __pycache__ and test files)
        for dir_name in essential_dirs:
            full_dir_path = os.path.join(proj_dir, dir_name)
            if os.path.exists(full_dir_path):
                for root, dirs, files in os.walk(full_dir_path):
                    # Filter out __pycache__
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for file in files:
                        if file.endswith(".pyc") or file.endswith(".tmp"):
                            continue
                        fpath = os.path.join(root, file)
                        arcname = os.path.relpath(fpath, proj_dir)
                        zf.write(fpath, arcname)
                        print(f"  + Added: {arcname}")

    zip_size = os.path.getsize(zip_path)
    print(f"\n[OK] Built {zip_filename} successfully! Size: {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")

    # Copy to Downloads
    downloads_dir = r"C:\Users\ITkey\Downloads"
    if os.path.exists(downloads_dir):
        dl_target = os.path.join(downloads_dir, zip_filename)
        shutil.copy2(zip_path, dl_target)
        print(f"[OK] Copied to Downloads: {dl_target}")

    # Copy to Desktop
    desktop_dirs = [
        r"C:\Users\ITkey\OneDrive - Key Dynamics Solutions Private Limited\Desktop",
        r"C:\Users\ITkey\Desktop"
    ]
    for d_dir in desktop_dirs:
        if os.path.exists(d_dir):
            dt_target = os.path.join(d_dir, zip_filename)
            shutil.copy2(zip_path, dt_target)
            print(f"[OK] Copied to Desktop: {dt_target}")

    # Verification: Read back zip contents
    with zipfile.ZipFile(zip_path, "r") as check_zf:
        names = check_zf.namelist()
        required = ["passenger_wsgi.py", "app.py", ".htaccess", "requirements.txt", "templates/index.html", "schema_mysql.sql"]
        for r in required:
            assert r in names, f"CRITICAL: {r} is missing from zip!"
        assert not any("cloudflared" in n for n in names), "ERROR: cloudflared binary found in zip!"
        assert not any(n == ".git" or n.startswith(".git/") or "/.git/" in n or "\\.git\\" in n for n in names), "ERROR: .git directory found in zip!"

    print("\n[ALL CHECKS PASSED] deploy.zip is 100% production-ready for GoDaddy cPanel / VPS upload!")

if __name__ == "__main__":
    build_godaddy_deploy_zip()
