from flask import Flask, jsonify, request
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain
from utility.helper import Helper


app = Flask(__name__)
CORS(app)

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.get_chain()
    dict_chain = [el.__dict__.copy() for el in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [el.__dict__.copy()
                                      for el in dict_block['transactions']]
    return jsonify(dict_chain), 200


@app.route('/open_transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    response = {
        'message': 'Transactions fetched successfully',
        'transactions': dict_transactions
    }

    return jsonify(response), 200


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Saving the keys failed'
        }
        return jsonify(response), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Loading the keys failed'
        }
        return jsonify(response), 500


@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.resolve_conflicts:
        response = {'message': 'Resolve block first, block not added'}
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block != None:
        dict_block = Helper.get_dict_from_block(block)
        response = {
            'message': 'Block mined successfully.',
            'block': dict_block,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding a block failed.',
            'wallet_set_up': wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    chain_snapshot = blockchain.get_chain()
    dict_chain = [el.__dict__.copy() for el in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [el.__dict__.copy()
                                      for el in dict_block['transactions']]
    if replaced:
        response = {'message': 'Chain was replaced!', 'chain': dict_chain, 'open_transactions': dict_transactions, 'replaced': replaced}
    else:
        response = {'message': 'Local chain kept!', 'chain': dict_chain, 'open_transactions': dict_transactions, 'replaced': replaced}
    return jsonify(response), 200

@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance != None:
        response = {
            'message': 'Balance fetched successfully',
            'funds': balance
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Getting balance failed!',
            'wallet_set_up': wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {
            'message': 'No wallet setup'
        }
        return jsonify(response), 400
    values = request.get_json(force=True)
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        response = {
            'message': 'Required data is missing'
        }
        return jsonify(response), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(
        wallet.public_key, recipient, amount, signature)
    if success:
        response = {
            'message': 'Transaction added successfully',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Transaction failed!'
        }
        return jsonify(response), 500


@app.route("/node", methods=["POST"])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data attatched'
        }
        return jsonify(response), 400

    if 'node' not in values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400

    node = values['node']
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added successfully',
        'all_nodes': list(blockchain.get_peer_nodes())
    }

    return jsonify(response), 201


@app.route("/node/<node_url>", methods=["DELETE"])
def remove_node(node_url):
    if node_url == "" or node_url == None:
        response = {
            'message': 'No node found'
        }
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {
        'message': 'Node removed',
        'all_nodes': list(blockchain.get_peer_nodes())
    }

    return jsonify(response), 200


@app.route('/nodes', methods=["GET"])
def get_nodes():
    nodes = list(blockchain.get_peer_nodes())
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        response= {'message': 'No data found'}
        return jsonify(response), 400
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in values for key in required):
        response= {'message': 'Some data is missing'}
        return jsonify(response), 400

    success = blockchain.add_transaction(values['sender'], values['recipient'], values['amount'], values['signature'], is_receiving=True)
    if success:
        response = {
            'message': 'Transaction added successfully',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature']
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Creating transaction failed'}
        return jsonify(response), 500


@app.route('/broadcast-block', methods=["POST"])
def broadcast_block():
    values = request.get_json()
    if not values:
        response= {'message': 'No data found'}
        return jsonify(response), 400
    if 'block' not in values:
        response= {'message': 'Some data is missing'}
        return jsonify(response), 400
    block = values['block']
    if block['index'] == blockchain.get_chain()[-1].index + 1:
        success = blockchain.add_block(block)
        if success:
            response = {'message': 'Block added'}
            return jsonify(response), 200
        else:
            response = {'message': 'Block seems invalid.'}
            return jsonify(response), 409
    elif block['index'] > blockchain.get_chain()[-1].index:
        response = {'message': 'Blockchain seems to differ from local blockchain'}
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {'message': 'Blockchain seems to be shorter, block not added'}
        return jsonify(response), 409
    


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)
