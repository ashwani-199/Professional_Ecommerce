# ShopZone E-Commerce - Production Deployment Guide

## Overview
This guide covers deploying the ShopZone Django e-commerce application to a production server.

## Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Nginx (reverse proxy)
- Gunicorn (WSGI server)
- Linux server (Ubuntu 22.04 LTS recommended)

---

## 1. Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv postgresql nginx git
```

### 1.2 Create Application User
```bash
sudo useradd -m -s /bin/bash shopzone
sudo su - shopzone
```

---

## 2. Database Setup

### 2.1 Configure PostgreSQL
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE shopzone_db;
CREATE USER shopzone_user WITH PASSWORD 'your-secure-password';
ALTER ROLE shopzone_user SET client_encoding TO 'utf8';
ALTER ROLE shopzone_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE shopzone_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE shopzone_db TO shopzone_user;
\q
```

---

## 3. Application Setup

### 3.1 Clone Repository
```bash
mkdir -p /var/www/shopzone
cd /var/www/shopzone
git clone <your-repo-url> .
```

### 3.2 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Configure Environment Variables
```bash
cp .env.example .env
nano .env
```

Update the following in `.env`:
```
DJANGO_SECRET_KEY=<generate-a-secure-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

DB_ENGINE=django.db.backends.postgresql
DB_NAME=shopzone_db
DB_USER=shopzone_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Generate a secure secret key:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3.4 Create Logs Directory
```bash
mkdir -p logs
```

### 3.5 Run Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 3.6 Create Superuser
```bash
python manage.py createsuperuser
```

### 3.7 Seed Sample Data (Optional)
```bash
python manage.py seed_data
```

---

## 4. Gunicorn Configuration

### 4.1 Test Gunicorn
```bash
gunicorn --config gunicorn.conf.py ecommerce.wsgi:application
```

### 4.2 Create Systemd Service
```bash
sudo nano /etc/systemd/system/shopzone.service
```

```ini
[Unit]
Description=ShopZone Gunicorn Application Server
After=network.target

[Service]
User=shopzone
Group=www-data
WorkingDirectory=/var/www/shopzone
Environment="PATH=/var/www/shopzone/venv/bin"
ExecStart=/var/www/shopzone/venv/bin/gunicorn --config gunicorn.conf.py ecommerce.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 4.3 Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable shopzone
sudo systemctl start shopzone
sudo systemctl status shopzone
```

---

## 5. Nginx Configuration

### 5.1 Create Nginx Config
```bash
sudo nano /etc/nginx/sites-available/shopzone
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/shopzone/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/shopzone/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    client_max_body_size 10M;
}
```

### 5.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/shopzone /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically update your Nginx config for HTTPS.

---

## 7. Security Hardening

### 7.1 Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 7.2 File Permissions
```bash
sudo chown -R shopzone:www-data /var/www/shopzone
sudo chmod -R 755 /var/www/shopzone
sudo chmod 600 /var/www/shopzone/.env
```

### 7.3 Verify Security Settings
The application includes these production security settings (active when DEBUG=False):
- SSL redirect
- Secure cookies
- HSTS (1 year with preload)
- XSS protection
- Content type sniffing prevention
- Clickjacking protection

---

## 8. Maintenance

### 8.1 Backup Database
```bash
sudo -u postgres pg_dump shopzone_db > /backup/shopzone_$(date +%Y%m%d).sql
```

### 8.2 Restore Database
```bash
sudo -u postgres psql shopzone_db < /backup/shopzone_YYYYMMDD.sql
```

### 8.3 Update Application
```bash
cd /var/www/shopzone
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart shopzone
```

### 8.4 View Logs
```bash
# Application logs
tail -f /var/www/shopzone/logs/django.log

# Gunicorn logs
tail -f /var/www/shopzone/logs/gunicorn-access.log
tail -f /var/www/shopzone/logs/gunicorn-error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 9. Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `abc123...` |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domains | `example.com,www.example.com` |
| `DB_ENGINE` | Database backend | `django.db.backends.postgresql` |
| `DB_NAME` | Database name | `shopzone_db` |
| `DB_USER` | Database user | `shopzone_user` |
| `DB_PASSWORD` | Database password | `secure-password` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `app-password` |
| `CSRF_TRUSTED_ORIGINS` | Trusted CSRF origins | `https://example.com` |

---

## 10. Quick Commands Reference

```bash
# Start/stop/restart application
sudo systemctl start shopzone
sudo systemctl stop shopzone
sudo systemctl restart shopzone

# Check status
sudo systemctl status shopzone
sudo systemctl status nginx
sudo systemctl status postgresql

# Django management
python manage.py runserver          # Development only
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py shell
python manage.py dbshell
```
