#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper installing cake-autorate and applying default qdisc limits
# across all VPN interfaces. Invoke from cron/systemd on every node.

IFACES=(wg0 amnezia0)
TARGET_RATE_DOWN="900Mbit"
TARGET_RATE_UP="900Mbit"

if ! command -v cake-autorate >/dev/null 2>&1; then
  echo "Installing cake-autorate via pipx..."
  pipx install cake-autorate
fi

for IFACE in "${IFACES[@]}"; do
  echo "Applying CAKE to ${IFACE}"
  tc qdisc replace dev "${IFACE}" root cake bandwidth "${TARGET_RATE_DOWN}"
  tc qdisc replace dev "${IFACE}" ingress cake bandwidth "${TARGET_RATE_UP}"
  cake-autorate --iface "${IFACE}" --autorate-ingress --autorate-egress &
done

echo "cake-autorate launched for interfaces: ${IFACES[*]}"
