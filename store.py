import json
import pickle

import utility.constants as constants
from block import Block
from transaction import Transaction

class Store:
    @staticmethod
    def save_data(blockchain, open_transactions):
        saveable_chain = [block.__dict__.copy() for block in blockchain]
        for block in saveable_chain:
            block['transactions'] = [tx.to_ordered_dict()
                                    for tx in block['transactions']]
        saveable_tx = [tx.__dict__.copy() for tx in open_transactions]
        try:
            with open('blockchain.txt', mode="w") as f:
                f.write(json.dumps(saveable_chain))
                f.write("\n")
                f.write(json.dumps(saveable_tx))
        except IOError:
            print("SAVE FAILED!")


    @staticmethod
    def load_data():
        try:
            with open('blockchain.txt', mode="r") as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])
                converted_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['amount'], tx['signature']) for tx in block['transactions']],
                                        block['proof'], block['timestamp']) for block in blockchain]
                open_transactions = json.loads(file_content[1])
                converted_open_transactions = [Transaction(
                    tx['sender'], tx['recipient'], tx['amount'], tx['signature']) for tx in open_transactions]

                return (converted_chain, converted_open_transactions)
        except (IOError, IndexError):
            return([constants.genesis_block], [])

    @staticmethod
    def save_data_b(blockchain, open_transactions):
        try:
            with open('blockchain.b', mode="wb") as f:
                save_date = {
                    'chain': blockchain,
                    'ot': open_transactions
                }
                f.write(pickle.dumps(save_date))
        except IOError:
            print("SAVE FAILED!")

    @staticmethod
    def load_data_b():
        try:
            with open('blockchain.b', mode="rb") as f:
                file_content = pickle.loads(f.read())
                blockchain = file_content['chain']
                open_transactions = file_content['ot']
                return (blockchain, open_transactions)
        except (IOError, IndexError):
            return([constants.genesis_block], [])
