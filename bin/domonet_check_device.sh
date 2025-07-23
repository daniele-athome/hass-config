#!/bin/sh
/usr/sbin/iptables -C FORWARD \
  -i "$1" -o "$2" \
  --src "$4" \! --dst 192.168.0.0/24 \
  -j ACCEPT -m comment --comment "HASS $3" >/dev/null 2>&1 && echo 1 || echo 0
