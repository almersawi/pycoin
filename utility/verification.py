import utility.hash_util as hash_util
import utility.balance_util as balance_util
from wallet import Wallet


class Verification:
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_util.hash_string_256(guess)
        if guess_hash[0:2] == '00':
            return True

    @classmethod
    def verify_blockchain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue

            if block.previous_hash != hash_util.hash_block(blockchain[index - 1]):
                return False

            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Proof of work invalid")
                return False

        return True

    
    @staticmethod
    def verify_transaction(transaction, open_transactions, chain, check_funds=True):
        if check_funds:
            balance = balance_util.get_balance(transaction.sender, open_transactions, chain)
            return balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)
