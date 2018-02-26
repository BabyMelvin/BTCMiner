import hashlib
import json
from time import time
from uuid import uuid4
from textwrap import dedent

from flask import Flask, jsonify

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


# instantiate our Node
app = Flask(__name__)

# instantiate the blockchain
blockchain = BlockChain()
# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')


@app.route('/mine', methods=['GET'])
def mine():
    return "we'll mine a new block"


@app.route('/transactions/new', method=['POST'])
def new_transaction():
    return "we'll add a new transaction"


@app.route('/chain', method=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=500)
