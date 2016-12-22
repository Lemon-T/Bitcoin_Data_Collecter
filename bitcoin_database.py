'''
  Copyright 2016 Zhihui Xie, Sun Yat-sen University
'''

# -*- coding: utf-8 -*-
import MySQLdb

db = MySQLdb.connect(host='localhost',
					port=3306,
					user='root',
					passwd='',
					db='bitcoin')

cursor = db.cursor()

# create three tables to store blocks, transactions and addresses
blockTable = '''CREATE TABLE BLOCK (
					BLOCK_ID INT PRIMARY KEY,
					TIME BIGINT
					)'''

txTable = '''CREATE TABLE TRANSACTION(
					TX_ID INT PRIMARY KEY AUTO_INCREMENT,
					TX CHAR(64) NOT NULL,
					BLOCK_ID INT,
					FOREIGN KEY (BLOCK_ID) REFERENCES BLOCK(BLOCK_ID)
					)'''

addressTable = '''CREATE TABLE ADDRESS(
					ADDRESS_ID INT PRIMARY KEY AUTO_INCREMENT,
					ADDRESS CHAR(34),
					VALUE DOUBLE,
					LAST_TX VARCHAR(256),
					TX_ID INT NOT NULL,
					FOREIGN KEY (TX_ID) REFERENCES TRANSACTION(TX_ID)
					)'''

try:
	cursor.execute(blockTable)
	cursor.execute(txTable)
	cursor.execute(addressTable)
	db.commit()
except Exception, e:
	print e
	db.rollback()

db.close()