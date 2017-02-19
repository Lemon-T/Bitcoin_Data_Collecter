# Combine three tables (BLOCK, TRANSACTION, ADDRESS) into one table and export a file 
select b.BLOCK_ID, b.TIME, t.TX_ID, t.TX, a.ADDRESS_ID, a.ADDRESS, a.LAST_TX, a.`VALUE`
from block b, `transaction` t, address a
where b.BLOCK_ID = t.BLOCK_ID and t.TX_ID = a.TX_ID
into OUTFILE "F:/Bitcoin_Data/total/total.txt" 

# After importing the data into a table, you should modify the types of attributes
# BLOCK_ID INT
# TIME INT
# TX_ID INT
# TX CHAR(64)
# ADDRESS_ID BIGINT(20)
# ADDRESS CHAR(34)
# LAST_TX VARCHAR(255)
# VALUE DOUBLE 