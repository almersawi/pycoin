from utility.verification import Verification
from utility.balance_util import get_balance
from blockchain import Blockchain
from wallet import Wallet


class Node:

    def __init__(self):
        self.wallet = Wallet()
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_user_choice(self):
        user_choice = input("Your choice: ")
        return user_choice

    def get_user_input(self, msg):
        """ Returns the input of the user """
        return input(msg)

    def get_transaction_value(self):
        tx_amount = float(self.get_user_input("Enter the amount: "))
        tx_recipient = self.get_user_input("Enter the recipient: ")
        return tx_recipient, tx_amount

    def print_blockchain(self):
        for block in self.blockchain.get_chain():
            print('Outputting Block')
            print(block)
        else:
            print('-' * 20)

    def listen_for_input(self):
        waiting_for_input = True

        while waiting_for_input:
            print("Please choose: ")
            print("1: Add a new transaction value")
            print("2: Output the blockchain blocks")
            print("3: Mine new block")
            print("4: Load Wallet")
            print("5: Save Wallet")
            print("q: Quit")

            user_choice = self.get_user_choice()
            if(user_choice == "1"):
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                signature = self.wallet.sign_transaction(self.wallet.public_key, recipient, amount)
                if self.blockchain.add_transaction(self.wallet.public_key, recipient, amount, signature):
                    print("TRANSACTION DONE!")
                else:
                    print("TRANSACTION FAILED!")

            elif(user_choice == "2"):
                self.print_blockchain()

            elif(user_choice == "3"):
                if not self.blockchain.mine_block():
                    print("Mining Failed!")

            elif user_choice == '4':
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)

            elif user_choice == '5':
                self.wallet.save_keys()

            elif(user_choice == "q"):
                waiting_for_input = False


            else:
                print("Invalid input")
            if not Verification.verify_blockchain(self.blockchain.get_chain()):
                print("Invalid blockchain")
                break
            print(get_balance(
                self.wallet.public_key, self.blockchain.get_open_transactions(), self.blockchain.get_chain()))

        else:
            print("User left!")


if __name__ == '__main__':
    node = Node()
    node.listen_for_input()
