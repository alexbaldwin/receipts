#!/usr/bin/env bash
# Install the receipt server on a Raspberry Pi (Raspberry Pi OS Lite, 64-bit).
# Run from the repo directory on the Pi: bash deploy/install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SERVICE_USER:-$(id -un)}"

sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q \
  python3-venv python3-dev libusb-1.0-0 libjpeg62-turbo libopenjp2-7 libopenblas0

cd "$REPO_DIR"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip config set global.extra-index-url https://www.piwheels.org/simple >/dev/null
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e .

# USB access for a non-root user
sudo install -m 644 deploy/99-epson-tm-t88v.rules /etc/udev/rules.d/99-epson-tm-t88v.rules
sudo udevadm control --reload-rules
sudo usermod -aG lp "$SERVICE_USER"

# Environment file (kept if it already exists)
sudo mkdir -p /etc/receipt-printer
if [ ! -f /etc/receipt-printer/server.env ]; then
  sudo install -m 644 deploy/receipt-server.env.example /etc/receipt-printer/server.env
  echo "Edit /etc/receipt-printer/server.env and set THERMAL_PRINTER_CONNECTION=usb for a USB printer."
fi

# systemd unit, with the user and paths of this checkout
sed -e "s/^User=.*/User=$SERVICE_USER/" \
    -e "s/^Group=.*/Group=$SERVICE_USER/" \
    -e "s#/home/[^/]*/receipts#$REPO_DIR#g" \
    deploy/receipt-server.service | sudo tee /etc/systemd/system/receipt-server.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now receipt-server
systemctl --no-pager status receipt-server | head -5
