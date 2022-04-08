import utility.hash_util as hash_util
from store import Store
from block import Block
from transaction import Transaction
import utility.constants as constants
from utility.verification import Verification
from wallet import Wallet
from utility.balance_util import get_balance

import requests
from utility.helper import Helper


class Blockchain:
    def __init__(self, public_key, node_id):
        self.__chain = [constants.genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False

        self.load_data()

    def get_chain(self):
        return self.__chain.copy()

    def get_open_transactions(self):
        return self.__open_transactions.copy()

    def save_data(self):
        Store.save_data(self.__chain, self.__open_transactions,
                        self.__peer_nodes, self.node_id)

    def load_data(self):
        self.__chain, self.__open_transactions, self.__peer_nodes = Store.load_data(
            self.node_id)

    def get_last_block(self):
        """ Returns the last block in the blockchain """
        if(len(self.__chain) < 1):
            return None
        return self.__chain[-1]

    def mine_block(self):
        if self.public_key == None:
            return None
        last_block = self.get_last_block()
        hashed_string = hash_util.hash_block(last_block)
        proof = self.proof_of_work()
        for tx in self.__open_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        self.reward_miner(self.public_key)
        block = Block(len(self.__chain), hashed_string,
                      self.__open_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        # inform peer nodes
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = Helper.get_dict_from_block(block)
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def print_blockchain(self):
        """ Print the blockchain """
        for block in self.__chain:
            print(block)
        else:
            print("-" * 10)

    def reward_miner(self, node):
        reward_transaction = Transaction(
            'MINING', node, constants.MINING_REWARD, '')

        self.__open_transactions.append(reward_transaction)

    def proof_of_work(self):
        last_block = self.get_last_block()
        last_hash = hash_util.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def add_transaction(self, sender, recipient, amount, signature, is_receiving=False):
        if self.public_key == None:
            return False
        transaction = Transaction(sender, recipient, amount, signature)
        if Verification.verify_transaction(transaction, self.__open_transactions, self.__chain):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    print(url)
                    try:
                        response = requests.post(url, json={
                            'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})

                        print({'response', response})

                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def get_balance(self):
        return get_balance(self.public_key, self.__open_transactions, self.__chain)

    def add_peer_node(self, node):
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)

    def add_block(self, block):
        # check if proof of work is valid
        transactions = [Transaction(
            tx['sender'], tx['recipient'], tx['amount'], tx['signature']) for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_util.hash_block(
            self.__chain[-1]) == block['previous_hash']
        if not proof_is_valid or not (hashes_match or block['index'] == 1):
            return False

        converted_block = Block(
            block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        store_transactions = self.__open_transactions[:]
        print(store_transactions)
        for itx in block['transactions']:
            for opentx in store_transactions:
                print(opentx)
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.__chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature']) for tx in block['transactions']],
                                    block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_blockchain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.__chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace
