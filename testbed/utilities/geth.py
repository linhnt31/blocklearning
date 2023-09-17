import os
import rlp
import string
import random
import tempfile
""" class eth_account.account.Account
Ref: https://eth-account.readthedocs.io/en/stable/eth_account.html#eth_account.account.Account

The primary entry point for working with Ethereum private keys. It does not require a connection to an Ethereum node.
"""
from eth_account import Account
from .json import *
from .processes import *

default_datadir = './ethereum/datadir'
default_password_length = 32

def generate_qbft_extra_data(validators):
  vanity = bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000000')
  validators = map(lambda x : bytes.fromhex(x[2:]), list(validators))
  extra_data = '0x' + rlp.encode([vanity, list(validators), [], 0, []]).hex()
  return extra_data

def update_genesis(src, dst, consensus, balance, data_dir):
  genesis = read_json(src)
  genesis['alloc'] = {}
  accounts = read_json(os.path.join(data_dir, 'accounts.json'))
  
  for account in accounts['miners']:
    genesis['alloc'][account] = { 'balance': balance }
  
  for account in accounts['clients']:
    genesis['alloc'][account] = { 'balance': balance }

  for account in accounts['owner']:
    genesis['alloc'][account] = { 'balance': balance }

  if consensus == 'poa':
    extra_data = '0x0000000000000000000000000000000000000000000000000000000000000000'
    for account in list(accounts['miners']):
      extra_data += account[2:]
    extra_data += '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    genesis['extraData'] = extra_data

  if consensus == 'qbft':
    validators = read_json(os.path.join(data_dir, 'miners.json'))
    genesis['extraData'] = generate_qbft_extra_data(validators)
    
  save_json(dst, genesis)

def get_random_string(length):
  characters = string.ascii_letters + string.digits
  result_str = ''.join(random.choice(characters) for i in range(length))
  return result_str

def generate_keys(nodekey, host, data_dir):
  """
  Generate a key for a bootnode
  """
  nodekey_file = os.path.join(data_dir, 'geth', nodekey) # get the path to the public key of a node
  run_and_output(f'bootnode -genkey {nodekey_file}') # generate a key for the bootnode

  with open(nodekey_file, 'r') as f:
    privkey = f.read()
    account = Account.from_key(privkey)

  pubkey = run_and_output(f'bootnode -nodekey {nodekey_file} -writeaddress').strip() #This nodekey_file is used to generate publickey of a bootnode
  enode = f'enode://{pubkey}@{host}:30303'


  address = account.address # Return the address of the node
  return address, enode

def generate_account(password, data_dir):
  with tempfile.NamedTemporaryFile() as fp:
    fp.write(password.encode())
    fp.seek(0)

    out = run_and_output(f'geth --datadir {data_dir} account new --password {fp.name}')
    return out.split("Public address of the key:")[1].split('\n')[0].strip()
  
def generate_accounts(miners, clients, data_dir, password_length):
  """
  Generate different accounts for users with different roles: owner (DRs), miners (validators or sealers), and clients (trainers or DPs)
  """

  # key-value of accounts: role-password
  accounts = {
    'owner': {},
    'miners': {},
    'clients': {}
  }

  static_nodes = []
  miner_addresses = []

  password = get_random_string(password_length) # is used to unlock the directory of private keys (or keystore)
  address = generate_account(password, data_dir)
  accounts['owner'][address] = password

  #  Use of os.makedirs() method to create directory
  os.makedirs(f'{data_dir}/geth/')

  _, enode = generate_keys('nodekey_owner', 'bfl-geth-rpc-endpoint-1', data_dir)
  static_nodes.append(enode)

  # each miner will be a bootnode
  for i in range(0, miners):
    password = get_random_string(password_length)
    # *generate_account* func returns the address of the account
    address = generate_account(password, data_dir)
    accounts['miners'][address] = password

    # *generate_keys* func returns *address and enode* values
    address, enode = generate_keys(f'nodekey_{i}', f'bfl-geth-miner-{i+1}', data_dir)
    static_nodes.append(enode)
    miner_addresses.append(address)

  for i in range(0, clients):
    password = get_random_string(password_length)
    address = generate_account(password, data_dir)
    accounts['clients'][address] = password

  save_json(os.path.join(data_dir, 'accounts.json'), accounts)
  save_json(os.path.join(data_dir, 'miners.json'), miner_addresses)
  save_json(os.path.join(data_dir, 'geth', 'static-nodes.json'), static_nodes)
