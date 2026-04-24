# Self-Hosting Guide

Deploy OpenGlaze on your own infrastructure.

## Table of Contents

1. [Requirements](#requirements)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Platform-Specific Guides](#platform-specific-guides)
5. [SSL/TLS Setup](#ssltls-setup)
6. [Backup and Restore](#backup-and-restore)
7. [Updating](#updating)
8. [Troubleshooting](#troubleshooting)

## Requirements

### Minimum

- 1 CPU core
- 1 GB RAM
- 10 GB storage
- Docker 20.10+ & Docker Compose 2.0+

### Recommended

- 2 CPU cores
- 2 GB RAM
- 20 GB SSD storage
- Docker 24.0+ & Docker Compose 2.20+

## Docker Deployment

### Quick Start (5 minutes)

```bash
# Clone repository
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze

# Copy and edit environment
cp .env.example .env
nano .env  # Edit required values

# Start all services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f openglaze

# Access at http://localhost:8768
```

### Environment Configuration

Edit `.env` with your values:

```bash
# Required
BASE_URL=https://openglaze.yourdomain.com
DATABASE_URL=postgres://openglaze:secure_password@postgres:5432/openglaze
SECRET_KEY=$(openssl rand -hex 32)
KRATOS_HOOK_KEY=$(openssl rand -hex 32)

# Database (internal to Docker network)
POSTGRES_USER=openglaze
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=openglaze

# Stripe (optional, for billing)
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email (for auth notifications)
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your_smtp_password
```

### Services Overview

The Docker Compose stack includes:

| Service | Port | Description |
|---------|------|-------------|
| openglaze | 8768 | Main Flask application |
| postgres | 5432 | PostgreSQL database |
| kratos | 4433/4434 | Ory Kratos identity server |
| mailhog | 8025 | Email catching (development) |

### Production Profile

For production with nginx reverse proxy:

```bash
docker-compose --profile prod up -d
```

This adds:
- nginx with SSL termination
- Static file serving
- Rate limiting

### Volume Mounts

```yaml
volumes:
  postgres_data:/var/lib/postgresql/data
  uploads:/app/uploads
  ./kratos:/etc/config/kratos:ro
```

Data persists across container restarts.

## Manual Deployment

### Server Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx

# Create user
sudo useradd -m -s /bin/bash openglaze
sudo mkdir -p /opt/openglaze
sudo chown openglaze:openglaze /opt/openglaze
```

### Application Setup

```bash
sudo -u openglaze bash
cd /opt/openglaze
git clone https://github.com/Pastorsimon1798/openglaze.git .

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Create database
sudo -u postgres psql -c "CREATE USER openglaze WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "CREATE DATABASE openglaze OWNER openglaze;"

# Environment
cp .env.example .env
nano .env
```

### Systemd Service

Create `/etc/systemd/system/openglaze.service`:

```ini
[Unit]
Description=OpenGlaze
After=network.target postgresql.service

[Service]
User=openglaze
Group=openglaze
WorkingDirectory=/opt/openglaze
Environment="PATH=/opt/openglaze/.venv/bin"
EnvironmentFile=/opt/openglaze/.env
ExecStart=/opt/openglaze/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8768 server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable openglaze
sudo systemctl start openglaze
sudo systemctl status openglaze
```

## Platform-Specific Guides

### Hetzner Cloud ($5-10/mo)

```bash
# Create CX21 instance (2 vCPU, 4 GB RAM)
# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Clone and deploy
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze
cp .env.example .env
# Edit .env with your domain

# Use Cloudflare or Let's Encrypt for SSL
docker-compose --profile prod up -d
```

### DigitalOcean ($6-12/mo)

Use the 1-Click Docker Droplet or:

```bash
# Create droplet with Docker pre-installed
# Follow Docker deployment steps above
# Use DigitalOcean's managed PostgreSQL for reliability
```

### Render (Free tier available)

1. Fork repository to your GitHub account
2. Create new Web Service on Render
3. Connect your fork
4. Set environment variables in Render dashboard
5. Add PostgreSQL managed database
6. Deploy

### Railway ($5+/mo)

1. Click "New Project"
2. Deploy from GitHub repo
3. Add PostgreSQL plugin
4. Set environment variables
5. Deploy

### Fly.io (Free tier available)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch
fly launch --dockerfile Dockerfile

# Create database
fly postgres create --name openglaze-db
fly postgres attach openglaze-db

# Deploy
fly deploy
```

### Raspberry Pi (Local/Offline)

```bash
# Raspberry Pi 4 (4GB+ recommended)
sudo apt update
sudo apt install -y docker.io docker-compose

# Clone and deploy (SQLite mode for simplicity)
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze

# Use SQLite instead of PostgreSQL
cat > .env << 'EOF'
BASE_URL=http://raspberrypi.local:8767
DATABASE_URL=sqlite:///glaze.db
MODE=personal
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Run without PostgreSQL/Kratos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py
python server.py
```

Access at `http://raspberrypi.local:8767`

## SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d openglaze.yourdomain.com

# Auto-renewal is configured automatically
```

### Manual Certificate

```bash
# Generate private key and CSR
openssl req -newkey rsa:4096 -nodes -keyout openglaze.key -out openglaze.csr

# Submit CSR to your CA, receive certificate
# Place files:
# /etc/ssl/private/openglaze.key
# /etc/ssl/certs/openglaze.crt
```

### nginx Configuration

```nginx
server {
    listen 80;
    server_name openglaze.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name openglaze.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/openglaze.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openglaze.yourdomain.com/privkey.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8768;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads {
        alias /opt/openglaze/uploads;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Cloudflare

If using Cloudflare:

1. Set DNS A record to your server IP
2. Enable "Full (strict)" SSL mode
3. Enable "Always Use HTTPS"
4. Configure Page Rules for caching static assets

## Backup and Restore

### Automated Backups

Create `/opt/openglaze/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR=/opt/openglaze/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
if [ -f glaze.db ]; then
    cp glaze.db $BACKUP_DIR/glaze_$TIMESTAMP.db
else
    docker-compose exec -T postgres pg_dump -U openglaze openglaze > $BACKUP_DIR/db_$TIMESTAMP.sql
fi

# Uploads backup
tar czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz uploads/

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

```bash
chmod +x /opt/openglaze/scripts/backup.sh

# Run daily via cron
0 2 * * * /opt/openglaze/scripts/backup.sh
```

### Restoring from Backup

**SQLite:**
```bash
cp backups/glaze_20260424_020000.db glaze.db
```

**PostgreSQL:**
```bash
docker-compose exec -T postgres psql -U openglaze openglaze < backups/db_20260424_020000.sql
```

## Updating

### Docker Update

```bash
cd /opt/openglaze
git pull origin master

# Check for schema migrations in release notes
docker-compose down
docker-compose up -d --build

# Verify
Docker-compose logs -f openglaze
```

### Manual Update

```bash
cd /opt/openglaze
git pull origin master

source .venv/bin/activate
pip install -r requirements.txt

# Run any migrations
python -c "from server import init_db; init_db()"

# Restart
sudo systemctl restart openglaze
```

### Database Migrations

Check release notes for schema changes. If migrations are needed:

```bash
# The application runs migrations automatically on startup
# But verify by checking logs
docker-compose logs openglaze | grep migration
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs openglaze

# Check environment
docker-compose exec openglaze env | grep -E "BASE_URL|DATABASE_URL"

# Test database connection
docker-compose exec postgres pg_isready
```

### Database Connection Errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check credentials
docker-compose exec postgres psql -U openglaze -d openglaze -c "SELECT 1"

# Reset database (WARNING: destroys all data)
docker-compose down -v
docker-compose up -d
```

### SSL Certificate Issues

```bash
# Test certificate
openssl s_client -connect openglaze.yourdomain.com:443

# Renew manually
sudo certbot renew --force-renewal

# Check expiry
sudo certbot certificates
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Limit memory
docker-compose up -d --memory=1g

# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow Performance

1. **Enable nginx caching** for static assets
2. **Add Gunicorn workers**: `-w $(($(nproc) * 2 + 1))`
3. **Use PostgreSQL** instead of SQLite
4. **Enable query logging** to identify slow queries
5. **Consider a CDN** for image uploads

### Email Not Working

```bash
# Check Mailhog (development)
curl http://localhost:8025/api/v2/messages

# For production, verify SMTP settings
telnet smtp.yourdomain.com 587
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY` (32+ random characters)
- [ ] Enable HTTPS with valid certificate
- [ ] Configure firewall (allow only 80, 443, 22)
- [ ] Enable automatic security updates
- [ ] Set up log monitoring
- [ ] Configure backups
- [ ] Disable debug mode (`FLASK_ENV=production`)
- [ ] Use PostgreSQL in production
- [ ] Enable rate limiting

## Monitoring

### Basic Health Checks

```bash
# Application
curl -f http://localhost:8768/health || echo "App down"

# Database
docker-compose exec postgres pg_isready || echo "DB down"

# Disk space
df -h | grep -E "Filesystem|/dev/"
```

### Uptime Monitoring

Free options:
- UptimeRobot (free tier: 50 monitors)
- Better Uptime (free tier: 10 monitors)
- Cronitor (free tier: 5 monitors)

Configure to ping `https://yourdomain.com/health` every 5 minutes.

---

**Need help?** Open a [GitHub Discussion](https://github.com/Pastorsimon1798/openglaze/discussions) or check the [Configuration Guide](configuration.md).
