# Quick Start Deployment Guide

Get Personal Finance Manager Pro running in production quickly with Docker.

## Prerequisites

- Docker & Docker Compose
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)

## 1. Server Setup

Update system
sudo apt update && sudo apt upgrade -y

Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

Install Docker Compose
sudo apt install docker-compose -y

Create app user
sudo useradd -m -s /bin/bash financeapp
sudo usermod -aG docker financeapp



## 2. Application Deployment

Switch to app user
sudo su - financeapp

Clone repository
git clone <your-repo-url> finance-manager
cd finance-manager

Configure environment
cp .env.example .env
nano .env



### Essential Environment Variables

SECRET_KEY=your-256-bit-secret-key-here
FLASK_ENV=production
DEBUG=False
FORCE_HTTPS=True
SESSION_COOKIE_SECURE=True
DATABASE_PATH=/app/data/finance.db



## 3. SSL Setup (Let's Encrypt)

Install certbot
sudo apt install certbot -y

Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

Copy certificates to app directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown financeapp:financeapp ssl/*



## 4. Start Application

Create required directories
mkdir -p data logs ssl

Start services
docker-compose up -d

Initialize database
docker-compose exec web python -c "
import model
model.init_db()
model.seed_default_categories()
print('Database initialized successfully!')
"



## 5. Verify Deployment

Check services
docker-compose ps

Check logs
docker-compose logs web
docker-compose logs nginx

Test application
curl -I https://yourdomain.com



## 6. Configure Firewall

Allow necessary ports
sudo ufw allow 22/tcp # SSH
sudo ufw allow 80/tcp # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable


## 7. Setup Automated Backups

Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/financeapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
docker-compose exec -T web sqlite3 /app/data/finance.db ".backup /app/data/backup_$DATE.db"
docker cp $(docker-compose ps -q web):/app/data/backup_$DATE.db $BACKUP_DIR/
docker-compose exec web rm /app/data/backup_$DATE.db

Keep only last 30 backups
find $BACKUP_DIR -name "backup_*.db" -type f -mtime +30 -delete
EOF

chmod +x backup.sh

Add to crontab (daily backups at 2 AM)
echo "0 2 * * * /home/financeapp/finance-manager/backup.sh" | crontab -



## 8. Setup SSL Renewal

Test renewal
sudo certbot renew --dry-run

Add to crontab (check twice daily)
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -



## 9. Monitoring Setup

### Basic Health Check Script

cat > health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f -s https://yourdomain.com/health > /dev/null; then
echo "$(date): Health check failed" >> logs/health.log
# Restart services if needed
docker-compose restart web
fi
EOF

chmod +x health-check.sh

Run every 5 minutes
echo "*/5 * * * * /home/financeapp/finance-manager/health-check.sh" | crontab -

#

## 10. Maintenance Commands

### View Logs
Application logs
docker-compose logs -f web

Nginx logs
docker-compose logs -f nginx

System logs
sudo journalctl -f

#

### Update Application
Pull latest changes
git pull origin main

Rebuild and restart
docker-compose build
docker-compose up -d

Apply any database migrations if needed
docker-compose exec web python -c "
import model
model.init_db() # This is safe - won't overwrite existing data
"

#

### Scale Services
Scale web workers
docker-compose up -d --scale web=3

#

### Backup & Restore

#### Manual Backup
./backup.sh

#

#### Restore from Backup
Stop application
docker-compose down

Restore database
cp backups/backup_YYYYMMDD_HHMMSS.db data/finance.db

Start application
docker-compose up -d

#

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
sudo chown -R financeapp:financeapp /home/financeapp/finance-manager

#

2. **SSL Certificate Issues**
Check certificate expiry
sudo certbot certificates

Force renewal
sudo certbot renew --force-renewal

#

3. **Database Lock Errors**
Stop application
docker-compose down

Check for zombie processes
sudo fuser data/finance.db

Restart
docker-compose up -d

#

4. **High Memory Usage**
Check container stats
docker stats

Restart services
docker-compose restart

#

### Performance Optimization

1. **Enable Log Rotation**
sudo nano /etc/logrotate.d/finance-manager

#

Add:
/home/financeapp/finance-manager/logs/*.log {
daily
rotate 30
compress
delaycompress
missingok
notifempty
}

#

2. **Optimize Docker**
Clean up unused containers/images
docker system prune -a

Monitor resource usage
docker stats

#

## Security Hardening

### Additional Security Measures

1. **Change SSH Port**
sudo nano /etc/ssh/sshd_config

Change Port 22 to Port 2222
sudo systemctl restart ssh
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp

#

2. **Install Fail2Ban**
sudo apt install fail2ban -y
sudo systemctl enable fail2ban


3. **Setup Log Monitoring**
Monitor failed login attempts
sudo tail -f /var/log/auth.log

Monitor application errors
tail -f logs/app.log



## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review health status: `curl https://yourdomain.com/health`
3. Verify database: Access dashboard and check functionality
4. Review security: Check SSL rating at SSL Labs

Your Personal Finance Manager Pro should now be running securely in production!
