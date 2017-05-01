"""
Script that adds the bands into the db
"""

import sqlite3
import string
import unicodedata

# Setup sqlite
sqlite_file = 'hyper.db'

# Connect to the database sqlite file
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()

# collect list of bands
bands = [\
			{"id": 1, "name" : "Arcade Fire", "twitter" : "@arcadefire"},\
			{"id": 2, "name" : "Bon Iver", "twitter" : "@boniver"},\
			{"id": 3, "name" : "Mishima", "twitter" : "@mishima"},\
			{"id": 4, "name" : "!!!", "twitter" : "@chkchkchk"},\
			{"id": 5, "name" : "Anímic", "twitter" : "@animic"}\
		 ]

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

	# store band into db
	try:
		db.execute("INSERT INTO Bands (id,name,codedName,twitterName) \
					VALUES ('{id}','{name}','{codedName}','{twitterName}')".format(\
				        id=b['id'], \
				        name=bandname, \
				        codedName=bandname_lowercase_no_spaces_no_accents, \
				        twitterName=b['twitter']
				        ) \
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
