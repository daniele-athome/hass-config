#!/bin/sh
/usr/sbin/iptables --line-numbers -nL FORWARD |
  grep HASS | grep "$1" | awk '{print $1}' |
  while read -r line; do /usr/sbin/iptables -D FORWARD "$line"; done
