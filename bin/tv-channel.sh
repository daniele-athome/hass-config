#!/bin/bash

hass_config=$(python3 -c "import yaml; import json; import sys; from pathlib import Path; print(json.dumps(yaml.safe_load(sys.stdin)))" < "$(dirname "$0")/../secrets.yaml")

xbmcAddress=$(echo "$hass_config" | jq -r '.mediarasp_host')
xbmcPort=8080
xbmcUser=$(echo "$hass_config" | jq -r '.kodi_username')
xbmcPass=$(echo "$hass_config" | jq -r '.kodi_password')

result=$(curl -s -u "$xbmcUser:$xbmcPass" --data-binary '{"jsonrpc": "2.0", "method": "PVR.GetChannelGroups", "params": {"channeltype" : "tv"}, "id": 1 }' -H 'content-type: application/json;' http://$xbmcAddress:$xbmcPort/jsonrpc)
groupid=$(echo "$result" | jq '.result.channelgroups[] | select(.label=="All channels") | .channelgroupid')

result=$( curl -s -u "$xbmcUser:$xbmcPass" --data-binary '{"jsonrpc": "2.0", "method": "PVR.GetChannels", "params": {"channelgroupid" : '"$groupid"',"properties":["channel"]}, "id": 1 }' -H 'content-type: application/json;' http://$xbmcAddress:$xbmcPort/jsonrpc)
channelid=$(echo "$result" | jq '.result.channels[] | select(.label=="'"$1"'") | .channelid')

echo "$channelid" | head -n 1
