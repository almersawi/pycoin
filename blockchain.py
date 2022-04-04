import utility.hash_util as hash_util
from store import Store
from block import Block
from transaction import Transaction
import utility.constants as constants
from utility.verification import Verification
from wallet import Wallet

class Blockchain:
    def __init__(self, hosting_node_id):
        self.__chain = [constants.genesis_block]
        self.__open_transactions = []
        self.hosting_node = hosting_node_id

        self.load_data()

    def get_chain(self):
        return self.__chain.copy()

    def get_open_transactions(self):
        return self.__open_transactions.copy()

    def load_data(self):
        self.__chain, self.__open_transactions = Store.load_data()

    def get_last_block(self):
        """ Returns the last block in the blockchain """
        if(len(self.__chain) < 1):
            return None
        return self.__chain[-1]


    def mine_block(self):
        if self.hosting_node == None:
            return False
        last_block = self.get_last_block()
        hashed_string = hash_util.hash_block(last_block)
        proof = self.proof_of_work()
        for tx in self.__open_transactions:
            if not Wallet.verify_transaction(tx):
                return False
        self.reward_miner(self.hosting_node)
        block = Block(len(self.__chain), hashed_string, self.__open_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        Store.save_data(self.__chain, self.__open_transactions)
        return True


    def print_blockchain(self):
        """ Print the blockchain """
        for block in self.__chain:
            print(block)
        else:
            print("-" * 10)


    def reward_miner(self, node):
        reward_transaction = Transaction('MINING', node, constants.MINING_REWARD, '')

        self.__open_transactions.append(reward_transaction)


    def proof_of_work(self):
        last_block = self.get_last_block()
        last_hash = hash_util.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def add_transaction(self, sender, recipient, amount, signature):
        if self.hosting_node == None:
            return False
        transaction = Transaction(sender, recipient, amount, signature)
        if Verification.verify_transaction(transaction, self.__open_transactions, self.__chain):
            self.__open_transactions.append(transaction)
            Store.save_data(self.__chain, self.__open_transactions)
            return True
        return False
