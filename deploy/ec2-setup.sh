#!/usr/bin/env bash
# =============================================================================
# deploy/ec2-setup.sh
#
# One-time bootstrap script for a fresh AWS EC2 instance (Amazon Linux 2023
# or Ubuntu 22.04).  Run as root or with sudo.
#
# Usage:
#   chmod +x deploy/ec2-setup.sh
#   sudo ./deploy/ec2-setup.sh
# =============================================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/YOUR_ORG/iit_hyderabad_hackathon.git}"
APP_DIR="/opt/credit-underwriting"
DOMAIN="${DOMAIN:-yourdomain.com}"    # override with: DOMAIN=app.example.com ./ec2-setup.sh
APP_USER="deployuser"

echo "==> Detecting OS..."
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS_ID="$ID"
else
  echo "Cannot detect OS. Exiting."; exit 1
fi

# ── Package manager helpers ──────────────────────────────────────────────────

install_pkgs_ubuntu() {
  apt-get update -qq
  apt-get install -y --no-install-recommends \
    git curl ca-certificates gnupg lsb-release \
    ufw fail2ban
}

install_pkgs_amzn() {
  yum update -y -q
  yum install -y git curl ca-certificates
}

echo "==> Installing base packages..."
if [[ "$OS_ID" == "ubuntu" ]]; then
  install_pkgs_ubuntu
elif [[ "$OS_ID" == "amzn" ]]; then
  install_pkgs_amzn
fi

# ── Docker ───────────────────────────────────────────────────────────────────

if ! command -v docker &>/dev/null; then
  echo "==> Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker installation failed"; exit 1
fi

# Docker Compose v2 (plugin)
if ! docker compose version &>/dev/null; then
  echo "==> Installing Docker Compose plugin..."
  DOCKER_CONFIG="${DOCKER_CONFIG:-$HOME/.docker}"
  mkdir -p "$DOCKER_CONFIG/cli-plugins"
  COMPOSE_VERSION="v2.26.1"
  curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
    -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
  chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
fi

# ── Dedicated deploy user ────────────────────────────────────────────────────

if ! id "$APP_USER" &>/dev/null; then
  echo "==> Creating deploy user '$APP_USER'..."
  useradd -m -s /bin/bash "$APP_USER"
  usermod -aG docker "$APP_USER"
fi

# ── Clone / update repo ──────────────────────────────────────────────────────

echo "==> Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull origin main
else
  git clone "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── Firewall (Ubuntu only) ───────────────────────────────────────────────────

if [[ "$OS_ID" == "ubuntu" ]]; then
  echo "==> Configuring UFW firewall..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 22/tcp comment 'SSH'
  ufw allow 80/tcp comment 'HTTP'
  ufw allow 443/tcp comment 'HTTPS'
  ufw --force enable
fi

# ── Storage directories ──────────────────────────────────────────────────────

mkdir -p "$APP_DIR/backend/storage/cam_reports"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backend/storage"

# ── Systemd service for auto-restart on reboot ───────────────────────────────

cat > /etc/systemd/system/credit-underwriting.service <<SERVICE
[Unit]
Description=Credit Underwriting Docker Compose Stack
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml down
TimeoutStartSec=300
User=${APP_USER}

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable credit-underwriting.service

# ── TLS bootstrap: initial nginx without HTTPS, then issue certificate ────────

echo ""
echo "============================================================"
echo " EC2 setup complete!"
echo ""
echo " Next steps:"
echo ""
echo " 1. Copy your production env vars:"
echo "    sudo -u $APP_USER cp .env.production.example $APP_DIR/.env.production"
echo "    # edit DATABASE_URL, SECRET_KEY, AWS_*, OPENAI_API_KEY"
echo ""
echo " 2. Update your domain in nginx/conf.d/app.conf:"
echo "    sed -i 's/yourdomain.com/$DOMAIN/g' $APP_DIR/nginx/conf.d/app.conf"
echo ""
echo " 3. Point your domain DNS A-record to this server's public IP."
echo ""
echo " 4. Start the stack (HTTP only first — needed for cert issuance):"
echo "    cd $APP_DIR"
echo "    sudo -u $APP_USER docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo " 5. Issue the Let's Encrypt certificate:"
echo "    sudo -u $APP_USER docker compose exec certbot certbot certonly \\"
echo "      --webroot -w /var/www/certbot \\"
echo "      -d $DOMAIN -d www.$DOMAIN \\"
echo "      --email admin@$DOMAIN --agree-tos --non-interactive"
echo ""
echo " 6. Reload nginx (now with HTTPS):"
echo "    sudo -u $APP_USER docker compose exec nginx nginx -s reload"
echo ""
echo " 7. Verify HTTPS:  curl -I https://$DOMAIN/health"
echo "============================================================"
