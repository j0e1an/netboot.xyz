# Multi-stage image for netboot.xyz
#
# Targets:
#   buildout  - existing behavior: dump Ansible HTML/ipxe output to a volume
#   runtime   - (default) self-contained TFTP + HTTP server with correct layout
#
# Example:
#   docker build -t netbootxyz:local --build-arg BOOT_DOMAIN=192.168.1.50:8080 .
#   docker compose up -d --build

ARG NBXYZ_OVERRIDES=default
ARG BOOT_DOMAIN=boot.netboot.xyz

FROM ghcr.io/netbootxyz/builder:latest AS builder
COPY . /ansible

FROM builder AS netbootxyz-default
ENV EXTRA_VARS=""

FROM builder AS netbootxyz-production
ENV EXTRA_VARS="--extra-vars @script/netbootxyz-overrides.yml"

FROM netbootxyz-${NBXYZ_OVERRIDES} AS ansible-build
ARG BOOT_DOMAIN
RUN set -eux; \
  cd /ansible; \
  printf '%s\n' \
    "---" \
    "boot_domain: ${BOOT_DOMAIN}" \
    "bootloader_https_enabled: false" \
    "bootloader_http_enabled: true" \
    > /tmp/docker-boot-domain.yml; \
  ansible-playbook site.yml ${EXTRA_VARS} --extra-vars @user_overrides.yml --extra-vars @/tmp/docker-boot-domain.yml; \
  echo "**** build tree ****"; \
  ls -la /var/www/html; \
  ls -la /var/www/html/ipxe | head -40

# ----- buildout (legacy dump-to-volume) -----
FROM alpine:latest AS buildout
COPY --from=ansible-build /var/www/html/ /mnt/
COPY docker-build-root/ /
ENTRYPOINT [ "/dumper.sh" ]

# ----- runtime TFTP + HTTP -----
FROM alpine:3.21 AS runtime
RUN apk add --no-cache \
  bash \
  dnsmasq \
  gettext \
  nginx \
  curl

COPY --from=ansible-build /var/www/html/ /opt/netbootxyz/
COPY docker/runtime/entrypoint.sh /entrypoint.sh
COPY docker/runtime/defaults/ /defaults/
RUN chmod +x /entrypoint.sh \
  && mkdir -p /config /assets \
  && ls -la /opt/netbootxyz/ipxe | head -20

ENV PUID=1000 \
    PGID=1000 \
    NGINX_PORT=80 \
    TFTP_ROOT=/config/menus \
    NETBOOT_SRC=/opt/netbootxyz

EXPOSE 69/udp 80
VOLUME ["/config", "/assets"]
ENTRYPOINT ["/entrypoint.sh"]
