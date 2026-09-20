#!/bin/bash
# Layout baked Ansible build into the dnsmasq TFTP root and start services.
# TFTP clients request netboot.xyz.efi / menu.ipxe at the ROOT of tftp-root
# (not under ipxe/ or remote/).

set -euo pipefail

PUID=${PUID:-1000}
PGID=${PGID:-1000}
NGINX_PORT=${NGINX_PORT:-80}
TFTP_ROOT=${TFTP_ROOT:-/config/menus}
SRC=${NETBOOT_SRC:-/opt/netbootxyz}

echo "[entrypoint] netboot.xyz runtime starting"
echo "[entrypoint] SRC=${SRC} TFTP_ROOT=${TFTP_ROOT} BOOT_DOMAIN=${BOOT_DOMAIN:-<build-time>}"

mkdir -p \
  "${TFTP_ROOT}/remote" \
  "${TFTP_ROOT}/local" \
  /assets \
  /config/nginx/site-confs \
  /config/log/nginx \
  /run/nginx \
  /var/lib/nginx/tmp/client_body \
  /var/tmp/nginx \
  /var/log/nginx

# Ensure nbxyz user exists for tftp-secure ownership
if ! getent group "${PGID}" >/dev/null 2>&1; then
  addgroup -g "${PGID}" nbxyz
fi
if ! getent passwd "${PUID}" >/dev/null 2>&1; then
  adduser -u "${PUID}" -G nbxyz -D -h /config -s /sbin/nologin nbxyz
fi

if [[ ! -d "${SRC}" ]]; then
  echo "[entrypoint] ERROR: baked menus not found at ${SRC}" >&2
  exit 1
fi

# --- Install menus + assets from image ---
# 1) Full tree into remote/ (webapp-compatible mirror)
# 2) Flatten ipxe bootloaders + menus onto TFTP root (what PXE actually requests)
echo "[entrypoint] syncing baked build into ${TFTP_ROOT}"
rm -rf "${TFTP_ROOT}/remote"
mkdir -p "${TFTP_ROOT}/remote"
cp -a "${SRC}/." "${TFTP_ROOT}/remote/"

# Menu scripts and helpers at TFTP/HTTP root
find "${SRC}" -maxdepth 1 -type f -exec cp -a {} "${TFTP_ROOT}/" \;

# Bootloaders live under ipxe/ in the Ansible output — PXE needs them at TFTP root
if [[ -d "${SRC}/ipxe" ]]; then
  echo "[entrypoint] placing bootloaders from ipxe/ onto TFTP root"
  find "${SRC}/ipxe" -maxdepth 1 -type f -exec cp -a {} "${TFTP_ROOT}/" \;
  find "${SRC}/ipxe" -maxdepth 1 -type f -exec cp -a {} "${TFTP_ROOT}/remote/" \;
fi

# Optional runtime override for HTTP menu/asset host (does not recompile iPXE)
if [[ -n "${BOOT_DOMAIN:-}" && -f "${TFTP_ROOT}/boot.cfg" ]]; then
  echo "[entrypoint] setting boot_domain to ${BOOT_DOMAIN} in boot.cfg"
  sed -i -E "s|^(set boot_domain ).*$|\1${BOOT_DOMAIN}|" "${TFTP_ROOT}/boot.cfg"
  if [[ -f "${TFTP_ROOT}/remote/boot.cfg" ]]; then
    sed -i -E "s|^(set boot_domain ).*$|\1${BOOT_DOMAIN}|" "${TFTP_ROOT}/remote/boot.cfg"
  fi
fi

# Preserve local overrides on top of remote defaults
if [[ -d "${TFTP_ROOT}/local" ]]; then
  find "${TFTP_ROOT}/local" -maxdepth 1 -type f -exec cp -a {} "${TFTP_ROOT}/" \;
fi

# nginx site
if [[ ! -f /config/nginx/nginx.conf ]]; then
  cp /defaults/nginx.conf /config/nginx/nginx.conf
fi
export NGINX_PORT
envsubst '${NGINX_PORT}' < /defaults/default.conf > /config/nginx/site-confs/default

chown -R "${PUID}:${PGID}" /config /assets /var/lib/nginx /var/log/nginx /run/nginx /var/tmp/nginx || true

echo "[entrypoint] TFTP root bootloaders:"
ls -la "${TFTP_ROOT}"/netboot.xyz* 2>/dev/null || echo "[entrypoint] WARNING: no netboot.xyz* bootloaders at TFTP root"

echo "[entrypoint] starting dnsmasq TFTP on UDP/69 (root=${TFTP_ROOT})"
dnsmasq \
  --port=0 \
  --keep-in-foreground \
  --enable-tftp \
  --tftp-root="${TFTP_ROOT}" \
  --user=nbxyz \
  --group=nbxyz \
  --log-facility=- \
  --log-dhcp \
  ${TFTPD_OPTS:-} \
  &
DNSMASQ_PID=$!

echo "[entrypoint] starting nginx on port ${NGINX_PORT}"
nginx -c /config/nginx/nginx.conf &
NGINX_PID=$!

cleanup() {
  kill "${DNSMASQ_PID}" "${NGINX_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Fail if either dies
while kill -0 "${DNSMASQ_PID}" 2>/dev/null && kill -0 "${NGINX_PID}" 2>/dev/null; do
  sleep 5
done

echo "[entrypoint] a service exited; shutting down" >&2
exit 1
