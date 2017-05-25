"""
Script that adds the bands into the db
"""

import sqlite3
import string
import unicodedata
import json
from pprint import pprint
import sys	

# Setup sqlite
sqlite_file = 'hyper_live.db'

# Connect to the database sqlite file
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()

# collect list of bands
json_data=open('bands_new.json').read()
bands = json.loads(json_data)
#pprint(bands)

# delete all entries and reset id
db.execute("DELETE FROM Bands")
connection.commit()

# loop bands and add them to DB
for b in bands:
	
	# set different band names encodings
	bandname = b['name']
	bandname_lowercase = bandname.lower()
	bandname_lowercase_no_spaces = ''.join(bandname_lowercase.split())
	bandname_lowercase_no_spaces_no_accents = ''.join((c for c in unicodedata.normalize('NFD', bandname_lowercase_no_spaces) if unicodedata.category(c) != 'Mn'))

	print("Adding band {} | {} | {} | {} ".format(b['id'], bandname, bandname_lowercase_no_spaces_no_accents, b['twitter']))

	# store band into db
	try:
		db.execute("INSERT INTO Bands (id,name,codedName,twitterName,headLevel,popularity) \
					VALUES ('{id}','{name}','{codedName}','{twitterName}','{headLevel}','{popularity}')".format(\
				        id=b['id'], \
				        name=bandname.replace("'","''"), \
				        codedName=bandname_lowercase_no_spaces_no_accents.replace("'","''"), \
				        twitterName=b['twitter'], \
				        headLevel=b['headLevel'], \
				        popularity=b['popularity'])
		)
		connection.commit()
	except sqlite3.Error as e:
		print("Error: ", e)

# Count number of inserted rows
db.execute("SELECT COUNT(*) FROM Bands")
count_rows = db.fetchone()
print("Inserted {} bands".format(count_rows[0]))

# close connection to db
connection.close() 
