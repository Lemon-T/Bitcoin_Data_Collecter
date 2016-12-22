# Bitcoin Data Collecter
This python tool is used to collect bitcoin data from bitcoin core.

Requirements
------------
* Python 2.7
* Bitcoin Core - Wallet
* MySQL
* Python-bitcoinrpc

Deployment
----------
* Install python
* Download the bitcoin core - wallet and synchronize the blocks data (https://bitcoin.org/en/bitcoin-core) 
* Add the `bitcoin.conf` file to bitcoin data folder and modify rpc_user and rpc_password
```
# You must set rpcuser and rpcpassword to secure the JSON-RPC api
rpcuser=your_name
rpcpassword=your_password
```
* Install MySQL
* Install python-bitcoinrpc (https://github.com/jgarzik/python-bitcoinrpc)
```
pip install python-bitcoinrpc
```

Usage
-----
1. Start the bitcoin core - wallet as a local server
2. Run `bitcoin_database.py` to create block, transaction and address tables
3. Add the rpc_user and rpc_password and set the number of blocks in `multiprocess_collecter.py`
4. Run `multiprocess_collecter.py` to collect the bitcoin data

Individualization
-----------------
You can change the database tables and modify the code to collect different attributes of bitcoin data.


