#!/bin/sh
/usr/sbin/iptables -A HOTSPOT-FORWARD \
  -i "$1" -o "$2" \
  --src "0.0.0.0/0" \! --dst 192.168.0.0/24 \
  -j ACCEPT -m comment --comment "HASS (all devices)"
