#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="x-twitter-mcp"
SERVICE_USER="x-twitter-mcp"
SERVICE_GROUP="x-twitter-mcp"

INSTALL_ROOT="/opt/x-twitter-mcp"
APP_DIR="${INSTALL_ROOT}/app"
VENV_DIR="${INSTALL_ROOT}/venv"
CONFIG_DIR="/etc/x-twitter-mcp"
CONFIG_FILE="${CONFIG_DIR}/x-twitter-mcp.env"
STATE_DIR="/var/lib/x-twitter-mcp"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_cmd() {
  local cmd="$1"
  local hint="${2:-}"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "ERROR: missing required command: ${cmd}" >&2
    if [[ -n "${hint}" ]]; then
      echo "HINT: ${hint}" >&2
    fi
    exit 1
  fi
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: must run as root" >&2
  exit 1
fi

require_cmd uv "Install uv first. Example: curl -Ls https://astral.sh/uv/install.sh | sh (then restart your shell)."
require_cmd python3 "Install Python 3.10+ and ensure 'python3' is in PATH."
require_cmd systemctl "Install and enable systemd (systemctl must be available)."
require_cmd rsync "Install rsync for syncing the repo into /opt/x-twitter-mcp/app."

SYSTEM_PYTHON="$(command -v python3)"

# Create service group if missing
if ! getent group "${SERVICE_GROUP}" >/dev/null 2>&1; then
  groupadd --system "${SERVICE_GROUP}"
fi

# Create service user if missing
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  useradd --system --home "${INSTALL_ROOT}" --shell /usr/sbin/nologin --gid "${SERVICE_GROUP}" "${SERVICE_USER}"
fi

# Create directories
mkdir -p "${INSTALL_ROOT}" "${APP_DIR}" "${VENV_DIR}" "${CONFIG_DIR}" "${STATE_DIR}"

chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_ROOT}" "${STATE_DIR}"
chown -R root:"${SERVICE_GROUP}" "${CONFIG_DIR}"
chmod 750 "${CONFIG_DIR}"

# Sync repo to app dir
rsync -a --delete --chown="${SERVICE_USER}:${SERVICE_GROUP}" --exclude ".git" --exclude ".venv" --exclude "__pycache__" "${REPO_ROOT}/" "${APP_DIR}/"

# Create/update venv using system Python to avoid user-home uv runtimes
uv venv --python "${SYSTEM_PYTHON}" "${VENV_DIR}"

# Install dependencies into venv
uv pip install --python "${VENV_DIR}/bin/python" "${APP_DIR}"

# Create env file if missing
if [[ ! -f "${CONFIG_FILE}" ]]; then
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    cp "${REPO_ROOT}/.env" "${CONFIG_FILE}"
  elif [[ -f "${REPO_ROOT}/.env.example" ]]; then
    cp "${REPO_ROOT}/.env.example" "${CONFIG_FILE}"
  else
    echo "ERROR: no .env or .env.example found in repo" >&2
    exit 1
  fi

  if ! grep -q '^PORT=' "${CONFIG_FILE}"; then
    # Ensure file ends with a newline before appending
    if [[ -s "${CONFIG_FILE}" ]]; then
      last_char="$(tail -c 1 "${CONFIG_FILE}" || true)"
      if [[ "${last_char}" != $'\n' ]]; then
        echo >> "${CONFIG_FILE}"
      fi
    fi
    echo 'PORT=8081' >> "${CONFIG_FILE}"
  fi

  chown root:"${SERVICE_GROUP}" "${CONFIG_FILE}"
  chmod 640 "${CONFIG_FILE}"
fi

# Install systemd unit
cat > "${UNIT_FILE}" <<UNIT
[Unit]
Description=X (Twitter) MCP Server
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${CONFIG_FILE}
ExecStart=${VENV_DIR}/bin/python -m x_twitter_mcp.http_server
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
UMask=027

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo "Installed and started ${SERVICE_NAME}."
