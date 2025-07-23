#!/usr/bin/env bash

# Connect to Google Home BT A2DP sink
bluetoothctl << EOF
connect 48:D6:D5:8F:19:54
EOF

sleep 5s

# set bluetooth as default output
pactl set-default-sink "$(pactl list short sinks | grep bluez | awk '{print $1}')"
