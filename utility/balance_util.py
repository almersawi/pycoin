from functools import reduce


def get_sum(values_list):
    return reduce(lambda tx_sum, tx_amount: tx_sum + sum(tx_amount) if len(tx_amount) > 0 else tx_sum, values_list, 0)


def get_balance(participant, open_transactions, blockchain):
    tx_sender = get_send_amount(participant, blockchain)
    print(open_transactions)
    open_tx_sender = [tx.amount
                      for tx in open_transactions if tx.sender == participant]
    tx_sender.append(open_tx_sender)
    tx_recipient = get_receive_amount(participant, blockchain)
    amount_sent = get_sum(tx_sender)
    amount_received = get_sum(tx_recipient)

    return amount_received - amount_sent


def get_send_amount(participant, blockchain):
    values = [[tx.amount for tx in block.transactions
               if tx.sender == participant] for block in blockchain]
    return values


def get_receive_amount(participant, blockchain):
    values = [[tx.amount for tx in block.transactions
               if tx.recipient == participant] for block in blockchain]
    return values
