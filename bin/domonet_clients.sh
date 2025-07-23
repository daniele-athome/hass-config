#!/bin/sh

export PATH=/usr/sbin:/sbin:$PATH

# TODO mergia i risultati col comando lnxrouter --lc PID poiché è l'unico modo per determinare se un device è online

echo '{"clients":['
/opt/lnxrouter/lnxrouter --lc "wlo1" |
  grep lease_ |
  awk '{print "{\"address\":\""$2 "\",\"name\":\"" $3 "\"},"}' |
  sed '$ s/.$//'
echo "]}"
