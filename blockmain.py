import hashlib
import json
from time import time
from uuid import uuid4
from textwrap import dedent
from urllib.parse import urlparse

from flask import Flask, jsonify, request
import requests

"""
    区块链是不可变，有序的记录连，记录也叫做区块。
    区块可以包含交易，文件或者任何你能够想到数据，
    不过至关重要是他们哈希值链接在一起的
"""


class BlockChain(object):
    """
       负责管理链。用来存储交易信息，也有一些帮助方法用来将新的区块添加到链中
    """

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # create the genesis block
        self.new_block(previous_hash=1, proof=100)

    # 需要新建一个区块，它没有任何前序区块。
    # 创始区块中加入证明，证明自己来自挖矿(或者工作量证明)
    def new_block(self, proof, previous_hash=None):
        # create a new Block and adds it to the chain
        """
        create a new block in the BlockChain
        :param proof:<int> the proof given by the Proof of the work algorithm
        :param previous_hash: (Optional) <str> hash of previous Block
        :return: <dict> new block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transactions(self, sender, recipient, amount):
        # add a new transaction to the list of transactions
        """
        create a new transaction to go into the next mined block
        :param sender:<str> address of the sender
        :param recipient:<str> address of the recipient
        :param amount:<int> amount
        :return:<int> the index of the block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        create a SHA-256 hash of a Block
        :param block: <dict> block
        :return: <str>
        """
        # we must make sure that the Dictionary is ordered ,or we'll have inconsistent(不一致) hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # return the last block in the chain
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        simple proof of work algorithm
            -find a number p such that hash(pp) contains leading 4 zeroes,where p is the p
            - p is the previous proof ,and p' is the new proof
        :param last_proof:<int>
        :return:<int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        validates the proof:does hash(last_proof,proof) contain 4 leading zeroes？
        :param last_proof:<int> previous proof
        :param proof:<int> current proof
        :return: <bool> true if correct ,False if not
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        add a new node to the list of nodes
        :param address: <str> address of node .Eg:'http://192.168.0.5:5000'
        :return:None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        determine if a given blockchain is valid
        :param chain:<list> a block chain
        :return:<bool> True if valid,False if not
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n--------------\n")
            # check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """

        :return:
        """
        neighbours = self.nodes
        new_chain = None
        # we're only looking for chains longer than ours
        max_length = len(self.chain)

        # grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # check if the length is longer than the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # replace our chain if we discovered a new ,valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False


##########################################################
# Flask微框架
##########################################################
# instantiate our Node
app = Flask(__name__)

# instantiate the blockchain
blockchain = BlockChain()
# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')


# TODO:挖出区块接收方就是节点地址。
@app.route('/mine', methods=['GET'])
def mine():
    # we run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # we must receive a reward for finding the proof.
    # the sender is "0" to signify that this node has mined a new coin
    blockchain.new_transactions(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # forge(锻造) the new block by adding it to the chain
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # create a new Transaction
    index = blockchain.new_transactions(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block{index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
