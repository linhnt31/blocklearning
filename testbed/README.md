# Experiment Testbed 🛌

This directory contains all the necessary code to run experiments using the [`blocklearning`](../blocklearning/) library via Docker.

- [Setup](#setup)
  - [Generate Ethereum Accounts](#generate-ethereum-accounts)
  - [Update Genesis with Accounts](#update-genesis-with-accounts)
  - [Build Docker Images](#build-docker-images)
  - [Create Docker Network](#create-docker-network)
  - [Launch Blockchain Containers](#launch-blockchain-containers)
  - [Connect Peers](#connect-peers)
  - [Deploy the Contract](#deploy-the-contract)
  - [Launch ML Containers](#launch-ml-containers)
  - [Collect Statistics](#collect-statistics)
  - [Run Rounds](#run-rounds)
  - [Collect Logs](#collect-logs)
- [Contract](#contract)
- [IPFS](#ipfs)
- [How to Run Different Experiments](#how-to-run-different-experiments)
  - [Consensus Algorithms](#consensus-algorithms)
  - [Selection Mechanisms](#selection-mechanisms)
  - [Without Score Mechanisms](#without-scoring-mechanisms)
  - [With Score Mechanisms](#with-scoring-mechanisms)

## Setup

### Generate Ethereum Accounts

Generate the accounts that will be used on the network. To generate 1 account for owner (default), 5 accounts for miners (or validators) and 10 for trainers, run:

```bash
python3 toolkit.py generate_accounts 5 10
```

The files in `ethereum/datadir` are as follows:

- `keystore` includes the accounts information that were generated and this is necessary to start the node.
- `geth/nodekey_owner` is the node key that will be given to the "owner" RPC endpoint for our Ethereum network.
- `geth/nodekey_{i}` is the node key that will be given to the i-th Ethereum miner.
- `geth/static-nodes.json` includes the addresses that will be added as static peers to our nodes.
- `accounts.json` is the account **address** and **password**.
- `miners.json` has the public addresses generated from the private key of the miners `nodekey`. This is important for some consensus protocol genesis.
- By default, your accounts in Geth are **locked**, which means that you can't send transactions from them. You need to unlock an account in order to send transactions from it through Geth directly or via RPC (though web3 does not support this). In order to unlock an account, ***you'll need to provide the password, which is used to decrypt the private key associated with your account, hence allowing you to sign transactions***.[Answered by Zack Coburn](https://ethereum.stackexchange.com/a/4159/123762)

- Every account is defined by a pair of keys, a private key and public key. ***Accounts are indexed by their address which is derived/hashed from the public key by taking the last 20 bytes***. Every private key/address pair is encoded in a keyfile.

- **Bootnode** and **enode**:

+ [When a new node joins the Ethereum network it needs to connect to nodes that are already on the network in order to then discover new peers. These entry points into the Ethereum network are called bootnodes. Note that bootnodes are not the same as static nodes. Static nodes are called over and over again, whereas bootnodes are only called upon if there are not enough peers to connect to and a node needs to bootstrap some new connections.](https://ethereum.org/en/developers/docs/nodes-and-clients/bootnodes/)

### Update Genesis with Accounts

After generating the accounts, the genesis files needs to be generated with the new accounts accounts in order to boot the network with 100 ETH in each of the accounts. To do so, run:

```bash
python3 toolkit.py update_genesis
```

### Build Docker Images

Several Docker images are used to run the Ethereum blockchain. Each container includes essential programs for running miners, trainers and federated learning. To build then, run:

```bash
python3 toolkit.py build_images
```

### Create Docker Network

```bash
docker network create \
  --driver=bridge \
  --subnet=172.16.254.0/20 \
  bflnet
```

### Launch Blockchain Containers

For Docker compose, use:

```bash
CONSENSUS=poa MINERS=5 docker compose -f blockchain.yml -p bfl up
```

Where 

+ `CONSENSUS` = `poa|qbft|pow`

+ **deploy.replicas**: specifies the number of containers that should be running at any given time.

### Useful command lines to check the Ethereum network working correctly

```python
# to mute logs
+ geth attach http://127.0.0.1:8545 [preferred]
+ geth <other flags> console 2> /dev/null
> net.peerCount
> admin.peers
# to save logs to file
geth <other flags> console --verbosity 3 2> geth-logs.log
```
### Connect Peers

Unfortunately, peer discovery [doesn't work with private networks](https://ethereum.stackexchange.com/questions/121380/private-network-nodes-cant-find-peers) and [this link](https://ethereum.stackexchange.com/questions/8712/automatic-peer-discovery-in-a-private-blockchain). Not even if we use a bootstrap node. Thus, we need to connect the peers to each other manually.

```bash
python3 toolkit.py connect_peers <network>
```

Where `<network>` is the ID of the Docker network where the containers are running. You can check that by running `docker network ls` and looking for `bflnet`. If no network is passed, the script will try to infer the correct network.

### Deploy the Contract

The contract deployment script fetches the account to use from `ethereum/datadir/accounts.json` and uses the first account (index 0).

```bash
python3 toolkit.py deploy_contract
```

### Launch ML Containers

```bash
CONTRACT=0x9a26730FD9893c6273c4F97c626fb752F6B8fad8 \
  DATASET=mnist MINERS=2 AGGREGATORS=1 SERVERS=2 SCORERS=0 CLIENTS=2 \
  SCORING="none" ABI=NoScore \
  docker compose -f ml.yml -p bfl-ml up
```

where 

- `-p` command line: specifies a project name

- `up`: creates and starts containers

### Collect Statistics

Start collecting statistics before running the rounds (on the results repository):

```bash
DIR=./results/CURRENT/stats
mkdir -p $DIR

while true; do
  echo "fetching"
  docker stats --no-stream --format "{{.ID}}, {{.Name}}, {{.CPUPerc}}, {{.MemUsage}}, {{.MemPerc}}, {{.NetIO}}, {{.BlockIO}}" > $DIR/$(date '+%s').log
  sleep 2
done
```

### Run Rounds

```bash
python3 start_round.py \
  --contract 0x8C3CBC8C31e5171C19d8a26af55E0db284Ae9b4B \
  --abi ../build/contracts/NoScore.json \
  --rounds 50
```

### Collect Logs

To collect the logs of the trainers and validators afterwards, run:

```bash
python3 toolkit.py collect-logs
```

## Contract

Some *required* base information for the contract can be found in [../contracts.json](../contracts.json). This file includes two fields that must be filled before deploying the contract:

- `model`: the IPFS CID of the exported model (head model for Split-CNN contract) in `.h5` format.
- `bottomModel`: the IPFS CID of the exported bottom model for the Split-CNN contract in `.h5` format.
- `weights` (optional): the IPFS CID with the initial weights.

## IPFS

To add any file to IPFS, run:

```
ipfs add [-r] path
```

## How to Run Different Experiments

### Consensus Algorithms

```bash
CONSENSUS=poa|pow|qbft MINERS=10 docker compose -f blockchain.yml -p bfl up

CONTRACT=0x8C3CBC8C31e5171C19d8a26af55E0db284Ae9b4B \
  DATASET=mnist MINERS=10 SERVERS=10 CLIENTS=25 \
  SCORING="none" ABI=NoScore \
  docker compose -f ml.yml -p bfl-ml up

python3 start_round.py \
  --contract 0x8C3CBC8C31e5171C19d8a26af55E0db284Ae9b4B \
  --abi ../build/contracts/NoScore.json \
  --rounds 50
```

### Selection Mechanisms

```bash
CONSENSUS=poa MINERS=10 docker compose -f blockchain.yml -p bfl up

CONTRACT=0xA63052D2C43CD996731937AAD7986bF8f88C2511 \
  DATASET=mnist MINERS=10 SERVERS=10 CLIENTS=25 \
  SCORING="none" ABI=FirstComeFirstServed \
  docker compose -f ml.yml -p bfl-ml up

python3 start_round.py \
  --contract 0xA63052D2C43CD996731937AAD7986bF8f88C2511 \
  --trainers fcfs \
  --abi ../build/contracts/FirstComeFirstServed.json \
  --rounds 50
```

### Without Score Mechanisms

```bash
CONSENSUS=poa MINERS=10 docker compose -f blockchain.yml -p bfl up

CONTRACT=0x8C3CBC8C31e5171C19d8a26af55E0db284Ae9b4B \
  DATASET=mnist MINERS=10 SERVERS=10 CLIENTS=5|10|25|50 \
  SCORING="none" ABI=NoScore \
  docker compose -f ml.yml -p bfl-ml up

python3 start_round.py \
  --contract 0x8C3CBC8C31e5171C19d8a26af55E0db284Ae9b4B \
  --abi ../build/contracts/NoScore.json \
  --rounds 50
```

### With Score Mechanisms

```bash
CONSENSUS=poa MINERS=10 docker compose -f blockchain.yml -p bfl up

CONTRACT=0x2988207C0b2666E554A803D25524B0822bd1B1A8 \
  DATASET=mnist MINERS=10 SERVERS=10 CLIENTS=5|10|25|50 \
  SCORING="<mechanism>" ABI=Score \
  docker compose -f ml.yml -p bfl-ml up

python3 start_round.py \
  --contract 0x2988207C0b2666E554A803D25524B0822bd1B1A8 \
  --abi ../build/contracts/Score.json \
  --scoring "<mechanism>" \
  --rounds 50
```

### Vertical (Split-CNN)

```bash
CONSENSUS=poa MINERS=10 docker compose -f blockchain.yml -p bfl up

CONTRACT=0x4A59e668c68c7915bCdfD5530B7C1C3D0F83885f \
  DATASET=../../blocklearning-results/datasets/vertical-mnist MINERS=10 SERVERS=5 CLIENTS=2 \
  docker compose -f vml.yml -p bfl-ml up

python3 start_vertical_round.py \
  --contract 0x4A59e668c68c7915bCdfD5530B7C1C3D0F83885f \
  --rounds 50
```
