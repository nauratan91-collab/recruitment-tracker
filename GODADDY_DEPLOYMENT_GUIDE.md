# GoDaddy Deployment Guide (Step-by-Step)
## Key Dynamics Solutions - Job Requirement & Recruitment Tracker

Yeh guide aapko step-by-step explain karegi ki aap is Flask + MySQL application ko **GoDaddy** par kaise deploy kar sakte hain.

---

## 📌 GoDaddy Hosting ke 2 Options:
1. **Option 1 (Most Common): GoDaddy cPanel Shared / Web Hosting Plus** (*Recommended*)
2. **Option 2: GoDaddy VPS / Dedicated Linux Server**

---

# 🚀 Option 1: GoDaddy cPanel Shared / Web Hosting Plus

GoDaddy cPanel mein Python applications **"Setup Python App"** (Phusion Passenger) ke zariye natively run hoti hain. Humne iske liye sabhi zaruri configuration files (`passenger_wsgi.py`, `.htaccess`, `schema_mysql.sql`) pehle se tayar kar di hain.

### Step 1: GoDaddy cPanel mein MySQL Database banayein
1. GoDaddy account mein login karein aur **cPanel** open karein.
2. **Databases** section mein **MySQL® Databases** par click karein.
3. **Create New Database**: Jaise `recruitment_db` enter karke **Create Database** par click karein. (Poora naam hoga: `cpaneluser_recruitment_db`).
4. **MySQL Users** section mein naya user banayein:
   - Username: Jaise `app_user` (Poora: `cpaneluser_app_user`)
   - Strong Password generate karein aur save kar lein.
5. **Add User To Database**: User aur Database ko select karein aur **Add** par click karein.
   - **ALL PRIVILEGES** checkbox ko tick karein aur **Make Changes** par click karein.

---

### Step 2: Database Schema Import karein (phpMyAdmin)
1. cPanel mein wapas aakar **phpMyAdmin** open karein.
2. Left sidebar se apna naya banaya hua database select karein.
3. Top navigation menu mein **Import** tab par click karein.
4. **Choose File** par click karke project ki file [`schema_mysql.sql`](schema_mysql.sql) select karein.
5. Niche scroll karke **Import / Go** button daba dein. Sabhi 8 tables aur initial accounts create ho jayenge.

---

### Step 3: cPanel mein "Setup Python App" configure karein
1. cPanel search bar mein type karein: **"Setup Python App"** (ya Software section mein dekhein).
2. **Create Application** button par click karein:
   - **Python version**: `3.10`, `3.11`, ya `3.12` select karein.
   - **Application root**: `recruitment-tracker` (ya agar direct main domain par chalana hai to `public_html`).
   - **Application URL**: Apna domain ya subdomain select karein (e.g., `careers.yourdomain.com` ya `yourdomain.com`).
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
3. **CREATE** button par click karein. cPanel ek virtual environment create kar dega.

---

### Step 4: Project Files Upload karein
1. cPanel **File Manager** open karein aur Application root folder (jaise `recruitment-tracker`) mein jayein.
2. Sabhi project files ko ZIP karke upload karein aur extract karein:
   - `app.py`, `database.py`, `dependencies.py`
   - `passenger_wsgi.py`, `.htaccess`
   - `templates/`, `static/`, `uploads/`
   - `requirements.txt`, `.env`

---

### Step 5: Python Dependencies Install karein
1. cPanel **Setup Python App** page par wapas jayein aur apni application ko edit karein.
2. Page ke upar ek command dikhegi, jaise:
   ```bash
   source /home/youruser/virtualenv/recruitment-tracker/3.11/bin/activate && cd /home/youruser/recruitment-tracker
   ```
3. Niche **Configuration files** box mein `requirements.txt` type karke **Add** karein aur **Run Pip Install** button par click karein.
   *(Ya cPanel ke **Terminal** option ko open karke upar wali command paste karke `pip install -r requirements.txt` chala dein).*

---

### Step 6: `.env` file mein GoDaddy Database Credentials dalein
File Manager mein project folder ke andar `.env` file create/edit karein:
```env
DB_ENGINE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=cpaneluser_app_user
MYSQL_PASSWORD=Aapka_Database_Password
MYSQL_DATABASE=cpaneluser_recruitment_db
SECRET_KEY=secure-random-secret-key-godaddy-2026
```
*(Note: GoDaddy cPanel par `MYSQL_HOST=localhost` hi rehta hai).*

---

### Step 7: Restart Application
1. **Setup Python App** page par top par **RESTART** button par click karein.
2. Browser mein apna domain open karein:
   `https://yourdomain.com`
3. Aapka Key Dynamics Recruitment Portal live chalne lagega!
   - Default Admin Login: `admin` / `Admin@123`
   - Default Manager Login: `manager` / `Manager@123`
   - Default Recruiter Login: `user` / `User@123`

---

# 🖥️ Option 2: GoDaddy VPS (Ubuntu / AlmaLinux) Setup

Agar aapke paas GoDaddy ka Virtual Private Server (VPS) ya Dedicated Server hai:

1. Server par SSH ke through login karein:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
2. Humne automated script create ki hai:
   ```bash
   # Repository clone karein
   git clone https://github.com/nauratan91-collab/recruitment-tracker.git /var/www/recruitment-tracker
   cd /var/www/recruitment-tracker

   # Automated setup script run karein
   chmod +x godaddy_vps_setup.sh
   ./godaddy_vps_setup.sh
   ```
3. Nginx config ko apne domain ke sath link karein:
   ```bash
   sudo cp nginx_godaddy.conf /etc/nginx/sites-available/recruitment-tracker
   sudo ln -s /etc/nginx/sites-available/recruitment-tracker /etc/nginx/sites-enabled/
   # Apne domain ka naam file mein edit karein
   sudo nano /etc/nginx/sites-available/recruitment-tracker
   sudo nginx -t
   sudo systemctl reload nginx
   ```
4. SSL Certificate (Free Let's Encrypt HTTPS):
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

---

## 🛠️ Troubleshooting & Logs on GoDaddy
- Agar koi error aaye, to cPanel File Manager mein `passenger_error.log` file check karein.
- Har startup traceback wahan automatically record hota hai.
- File upload issues ke liye `.htaccess` file upload limit `25M` tak allow karti hai.
