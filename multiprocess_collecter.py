'''
  Copyright 2016 Zhihui Xie, Sun Yat-sen University
'''

#-*- coding: utf-8 -*-
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import logging
import time
import MySQLdb
import json
import multiprocessing

startTime = time.clock()
blockTable = 'BLOCK'
txTable = 'TRANSACTION'
addressTable = 'ADDRESS'

connection = 'localhost'
host = 'root'
password = ''
database = 'bitcoin'
db = MySQLdb.connect(connection, host, password, database)

# Connect to the bitcoin core server with rpc_user and rpc_password in bitcoin.conf file
url = 'http://%s:%s@127.0.0.1:8332' % (rpc_user, rpc_password)

queue = multiprocessing.JoinableQueue()

def getNumRows(table):
	cursor = db.cursor()
	cursor.execute(SQLSet().getRowNums(table))
	res = cursor.fetchone()
	return res[0]


def initAutoIncrement(table):
	cursor = db.cursor()
	num = getNumRows(table)
	num = num if num != 0 else 1
	cursor.execute(SQLSet().setAutoIncrement(table, num))

# Set the starting points of three tables in each time 
def initStartingPoint():
	global blkId
	blkId = getNumRows(blockTable)
	initAutoIncrement(txTable)
	initAutoIncrement(addressTable)
	try:
		db.commit()
	except:
		db.rollback()

# Emptied all the tables and used to test the program
def clearAllTables():
	cursor = db.cursor()
	cursor.execute(SQLSet().delectTable(addressTable))
	cursor.execute(SQLSet().delectTable(txTable))
	cursor.execute(SQLSet().delectTable(blockTable))
	try:
		db.commit()
	except:
		db.rollback()

# Define a logger
class Logger:
	def logBlockPrc(self, blockId):
		curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
		print (curTime + ' Block ' + str(blockId) + ' is processing...')

	def logTx(self, txId):
		curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
		print (curTime + ' Transaction ' + str(txId))

	def logError(self, func, id, error):
		curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
		print (curTime + ' ***Error ' + func + ' ' + str(id) + ': ' + str(error) + '!***')

# The class includes a set of sql commands
class SQLSet:
	def getRowNums(self, table):
		return '''SELECT COUNT(*) FROM %s''' % (table)

	def delectTable(self, table):
		return '''DELETE FROM %s''' % table

	def setAutoIncrement(self, table, num):
		return '''ALTER TABLE %s AUTO_INCREMENT=%d''' % (table, num)	

	def insertBlock(self, blockId, time):
		return '''INSERT INTO BLOCK(BLOCK_ID, TIME)
					VALUES (%d, %d)''' % (blockId, time)

	def insertTx(self, Tx, blockId):
		return '''INSERT INTO TRANSACTION(TX, BLOCK_ID)
						VALUES ('%s', %d)''' % (Tx, blockId)

	def insertAddress(self, address, value, lastTx, outTxId):
		return '''INSERT INTO ADDRESS(ADDRESS, VALUE, LAST_TX, TX_ID)
							VALUES ('%s', %f, '%s', %d)''' % (address, value, lastTx, outTxId)

	def insertManyAddress(self):
		return '''INSERT INTO ADDRESS(ADDRESS, VALUE, LAST_TX, TX_ID)
							VALUES (%s, %s, %s, %s)'''

# Defined the comsumer process to collect bitcoin data
class ConsumerProcess(multiprocessing.Process):
	def __init__(self, name, q):
		multiprocessing.Process.__init__(self)
		self.name = name
		self.queue = q
		self.access = AuthServiceProxy(url)
		
	def run(self):
		access = AuthServiceProxy(url)
		self.oneDb = MySQLdb.connect(connection, host, password, database)
		while True:
			num = self.queue.get()
			self.blockInfo = []
			self.txInfo = []
			self.addressInfo = []
			try:
				self.recordBlockInfo(num, access)
				self.recordTxInfo()
				self.recordAddrInfo(access)
				self.oneDb.commit()
			except Exception, error:
				# print 'Error !!'
				self.oneDb.rollback()
				self.queue.put(num)
			self.queue.task_done()
		self.oneDb.close()

	# Collected the information of each block
	def recordBlockInfo(self, num, access):
		cursor = self.oneDb.cursor()
		blockHash = access.getblockhash(num)
		block = access.getblock(blockHash)
		# Logger().logBlockPrc(blockId)
		insertBlk = SQLSet().insertBlock(block['height'], block['time'])
		try:	
			cursor.execute(insertBlk) 
			self.blockInfo.extend([block['height'], block["tx"]])
		except Exception, error:
			Logger().logError(blockTable, blockId, error)
			raise error
			
	# Collected the information of all the transactions in a block
	def recordTxInfo(self):
		cursor = self.oneDb.cursor()
		blockId = self.blockInfo[0]
		txArray = self.blockInfo[1]
		for i in range(0, len(txArray)):
			# Logger().logTx(i)
			insertTx = SQLSet().insertTx(txArray[i], blockId)
			try:
				cursor.execute(insertTx)
				if blockId == 0:
					return
				self.txInfo.append([cursor.lastrowid, txArray[i]])
			except Exception, error:
				Logger().logError(txTable, cursor.lastrowid, error)
				raise error

	def checkAddress(self, scriptPubKey):
		if scriptPubKey.has_key('addresses'):
			return scriptPubKey['addresses'][0]
		else:
			return 'Unable to decode output address'	
		
	# Processed the vin transactions
	def subVinAddr(self, outTxId, txInfo, access):
		vin = txInfo['vin']
		for i in range(0, len(vin)):
			vinItem = vin[i]
			if vinItem.has_key('coinbase'):
				coinbase = vinItem['coinbase']
				self.results.append(('coinbase', -1, coinbase, outTxId))
			else:
				lastTx = vinItem['txid']
				voutId = vinItem['vout']
				lastTxInfo = access.getrawtransaction(lastTx, 1)
				value = lastTxInfo['vout'][voutId]['value']	
				scriptPubKey = lastTxInfo['vout'][voutId]['scriptPubKey']
				address = self.checkAddress(scriptPubKey)	
				self.results.append((address, value, lastTx, outTxId))		

	# Processed the vout transactions
	def subVoutAddr(self, outTxId, txInfo):
		vout = txInfo['vout']
		for i in range(0, len(vout)):
			voutItem = vout[i]
			scriptPubKey = voutItem['scriptPubKey']
			lastTx = 'vout'
			address = self.checkAddress(scriptPubKey)
			value = voutItem['value']
			self.results.append((address, value, lastTx, outTxId))


	# Collected the information of all the addresses in a transaction
	def recordAddrInfo(self, access):
		# The list is used to store the information of vin and vout addresses
		self.results = []	
		cursor = self.oneDb.cursor()
		for item in self.txInfo:
			outTxId = item[0]
			tx = item[1]
			txDetail = access.getrawtransaction(tx, 1)
			self.subVinAddr(outTxId, txDetail, access)
			self.subVoutAddr(outTxId, txDetail)
		try:		
			cursor.executemany(SQLSet().insertManyAddress(), self.results)	
		except Exception, error:
			Logger().logError(addressTable, '', error)
			raise error
				
def main():
	clearAllTables()
	initStartingPoint()
	accessBlock = AuthServiceProxy(url)
	blockCount = accessBlock.getblockcount()
	print 'The program is processing...'

	# Set the number of processes to run
	for i in range(20):
		c = ConsumerProcess(str(i), queue)
		c.daemon = True
		c.start()
	
	# Set the number of block to be collected
	for i in range(blkId, 1000):
		queue.put(i)

	queue.join()

	# Calculated the running time
	endTime = time.clock()
	print ('Running time: ' + str(endTime - startTime))

	db.close()
	
if __name__ == '__main__':
	# setScriptLogger()
	main()
