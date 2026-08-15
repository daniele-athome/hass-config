#!/bin/sh
/usr/sbin/iptables --line-numbers -nL HOTSPOT-FORWARD |
  grep HASS | grep "$1" | awk '{print $1}' |
  while read -r line; do /usr/sbin/iptables -D HOTSPOT-FORWARD "$line"; done
