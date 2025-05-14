#!/bin/bash
tc qdisc del dev ens33 root || true
tc qdisc add dev ens33 root handle 1: prio bands 4
MY_IP=$(ip -4 addr show dev ens33 | awk '/inet / {print $2}' | cut -d/ -f1)

declare -A GROUPMAP
GROUPMAP[1]="172.22.155.41 172.22.151.21 172.22.153.62 172.22.155.42 172.22.151.22"
GROUPMAP[2]="172.22.153.63 172.22.155.43 172.22.151.23 172.22.153.64 172.22.155.44"
GROUPMAP[3]="172.22.151.24 172.22.153.65 172.22.155.45 172.22.151.25 172.22.153.66"
GROUPMAP[4]="172.22.155.46 172.22.151.26 172.22.153.67 172.22.155.47"

declare -A NETEM
NETEM[1]="delay 10.0ms loss 5.0% rate 20mbit"
NETEM[2]="delay 10.0ms loss 5.0% rate 20mbit"
NETEM[3]="delay 10.0ms loss 5.0% rate 20mbit"
NETEM[4]="delay 2.0ms loss 2.0% rate 100mbit"

for i in {1..4}; do
  if [[ -n "${NETEM[$i]}" ]]; then
    tc qdisc add dev ens33 parent 1:$i handle ${i}0: netem ${NETEM[$i]}
    for ip in ${GROUPMAP[$i]}; do
      if [[ "$ip" == "$MY_IP" ]]; then
        echo "Skipping my own IP: $ip"
        continue
      fi
      echo "Adding filter for IP: $ip to group $i"
      tc filter add dev ens33 protocol ip parent 1: prio 1 u32 match ip dst $ip flowid 1:$i
    done
  fi
done