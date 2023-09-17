#!/bin/sh

DIR=./results/CURRENT/stats
mkdir -p $DIR

while true; do
  echo "fetching"
  docker stats --no-stream --format "{{.ID}}, {{.Name}}, {{.CPUPerc}}, {{.MemUsage}}, {{.MemPerc}}, {{.NetIO}}, {{.BlockIO}}" > $DIR/$(date '+%s').log
  sleep 2
done
