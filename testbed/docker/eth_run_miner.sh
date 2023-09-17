#!/bin/sh

# Get IPv4 and IPv6
# ex:   192.168.101.129
#       fe80::8497:550d:6b19:d1d4
IP=$(ifconfig eth0 | grep 'inet' | awk '{print $2}' | sed 's/addr://')
INDEX=$(dig -x $IP +short | sed 's/[^0-9]*//g')
INDEX=$((INDEX-1))
ACCOUNT=$(jq -r '.miners' accounts.json | jq 'keys_unsorted' | jq -r "nth($INDEX)")
PASSWORD=$(jq -r '.miners' accounts.json | jq -r ".[\"$ACCOUNT\"]")
# NETWORK_ID="268f318d2622"
echo $ACCOUNT > ./account.txt
echo $INDEX > ./index.txt
echo $IP > ./ip.txt
cp /root/.ethereum/_geth/nodekey_${INDEX} /root/.ethereum/geth/nodekey
echo $PASSWORD > ./password.txt
geth --networkid=${NETWORK_ID} --miner.etherbase=${ACCOUNT} --unlock=${ACCOUNT} --syncmode=full --password=./password.txt "$@"