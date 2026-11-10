#!/usr/bin/env bash
# Install the MathTutor print-button service on the Pi. Idempotent; run as root
# from a checkout or rsync of the pi/ directory:  sudo ./setup.sh
# Optional: PRINTER_URI=ipp://... to skip printer auto-discovery.
set -euo pipefail

SERVICE_USER=mathtutor-pi
APP_DIR=/opt/mathtutor-pi
CONF_DIR=/etc/mathtutor-pi
TOKEN_FILE="$CONF_DIR/token"
CONF_FILE="$CONF_DIR/config.toml"
PRINTER_NAME=Brother_HL_L2340DW
PRINTER_MODEL_PATTERN='HL-L2340D'
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
  echo "setup.sh must run as root (try: sudo $0)" >&2
  exit 1
fi

echo "==> Installing packages"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3-gpiozero python3-lgpio cups chromium-headless-shell

echo "==> Service user"
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin "$SERVICE_USER"
fi
for group in gpio lp; do
  if getent group "$group" >/dev/null; then
    usermod -aG "$group" "$SERVICE_USER"
  else
    echo "warning: group '$group' does not exist" >&2
  fi
done

echo "==> Copying package to $APP_DIR"
install -d -m 0755 "$APP_DIR"
rm -rf "$APP_DIR/mathtutor_pi"
cp -r "$SRC_DIR/mathtutor_pi" "$APP_DIR/mathtutor_pi"
find "$APP_DIR/mathtutor_pi" -name __pycache__ -type d -prune -exec rm -rf {} +
chown -R root:root "$APP_DIR"

echo "==> Config in $CONF_DIR"
install -d -m 0750 -o root -g "$SERVICE_USER" "$CONF_DIR"
if [[ ! -e "$CONF_FILE" ]]; then
  install -m 0640 -o root -g "$SERVICE_USER" "$SRC_DIR/config.example.toml" "$CONF_FILE"
  echo "created $CONF_FILE from the example; edit the child ids"
fi
if [[ ! -e "$TOKEN_FILE" ]]; then
  install -m 0600 -o "$SERVICE_USER" -g "$SERVICE_USER" /dev/null "$TOKEN_FILE"
fi

echo "==> CUPS printer $PRINTER_NAME"
systemctl enable --now cups
if lpstat -v "$PRINTER_NAME" >/dev/null 2>&1; then
  echo "printer already configured"
else
  uri="${PRINTER_URI:-}"
  if [[ -z "$uri" ]]; then
    echo "searching the network for the printer (may take a few seconds)..."
    uri="$(lpinfo --include-schemes dnssd -v 2>/dev/null \
      | awk -v pat="$PRINTER_MODEL_PATTERN" '$2 ~ /^(dnssd|ipp):\/\// && index($2, pat) {print $2; exit}' || true)"
  fi
  if [[ -n "$uri" ]]; then
    lpadmin -p "$PRINTER_NAME" -E -v "$uri" -m everywhere
    echo "printer added at $uri"
  else
    echo "warning: printer not found. Make sure it is on and on Wi-Fi, then re-run with" >&2
    echo "  sudo PRINTER_URI=ipp://<printer-address>/ipp/print ./setup.sh" >&2
  fi
fi

echo "==> systemd service"
install -m 0644 "$SRC_DIR/systemd/mathtutor-pi.service" /etc/systemd/system/mathtutor-pi.service
systemctl daemon-reload
if [[ -s "$TOKEN_FILE" ]]; then
  systemctl enable mathtutor-pi.service
  systemctl restart mathtutor-pi.service
  echo "service enabled and restarted"
else
  systemctl disable mathtutor-pi.service >/dev/null 2>&1 || true
  cat <<MSG
The service is NOT enabled yet: the token file is empty.
Next steps:
  1. Create a device token at <site>/settings/devices
  2. Put it in $TOKEN_FILE (owner $SERVICE_USER, mode 0600)
  3. Fill in the child ids in $CONF_FILE
     (sudo -u $SERVICE_USER env HOME=/tmp PYTHONPATH=$APP_DIR python3 -m mathtutor_pi children --config $CONF_FILE)
  4. Re-run setup.sh (it enables and restarts the service once the token is
     present), or: sudo systemctl enable --now mathtutor-pi
MSG
fi
