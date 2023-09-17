#!/bin/sh

cp /root/.ethereum/_geth/nodekey_owner /root/.ethereum/geth/nodekey
# NETWORK_ID="268f318d2622"
geth --networkid=${NETWORK_ID} "$@"
