import sqlite3
import random
import string
from datetime import datetime

total_num_tweets = 1000 # total number of fake tweets to create

bands = [\
			{"name" : "Arcade Fire", "twitter" : "@arcadefire"},\
			{"name" : "Bon Iver", "twitter" : "@boniver"},\
			{"name" : "Mishima", "twitter" : "@mishima"},\
			{"name" : "!!!", "twitter" : "@chkchkchk"},\
			{"name" : "Animic", "twitter" : "@animic"}\
		 ]

texts = [\
			"Lorem ipsum dolor sit l'amet", \
			"consectetur adipiscing  ÀÈÌÒÙ lit", \
			"sed do eiusmod tempor incididunt ÁÉÍÓÚ", \
			"ut labore et dolore magna aliqua", \
			"Ut enim ad minim veniam", \
			"quis nostrud exercitation ullamco", \
			"laboris nisi ut aliquip ex ea commodo consequat", \
			"Duis aute irure dolor in reprehenderit", \
			"in voluptate velit`esse´cillum", \
			" dolore eu fugiat nulla pariatur", \
			"Excepteur sint occaecat cupidatat", \
			" non proident áéíóú", \
			"sunt in culpa qui officia deserunt", \
			" mollit anim id est laborum", \
			"Sed ut perspiciatis unde", \
			" omnis iste natus error a'a", \
			"sit voluptatem accusantium", \
			"àèìòù doloremque laudantium", \
			"totam rem aperiam", \
			"eaque ipsa quae ab illo inventore", \
			" veritatis et äëïöü", \
			"quasi architecto beatae", \
			"vitae dicta sunt explicabo", \
			"Nemo enim ipsam voluptatem quia", \
			"voluptas sit aspernatur aut odit aut fugit", \
			"sed quia consequuntur magni dolores", \
			"eos ÄËÏÖÜ qui ratione voluptatem sequi nesciunt", \
			"Neque porro quisquam est, qui dolorem", \
			"ipsum quia dolor sit amet, consectetur", \
			"adipisci velit, sed quia non numquam", \
			"eius modi tempora incidunt ut.", \
			"labore et dolore magnam aliquam", \
			"quaerat voluptatem. Ut enim ad minima veniam", \
			"quis nostrum exercitationem ullam corporis", \
			"suscipit laboriosam, nisi ut aliquid ex", \
			"ea commodi consequatur?", \
			"Quis autem vel eum iure reprehenderit", \
			"qui in ea voluptate velit esse", \
			"quam nihil molestiae consequatur", \
			"vel illum qui dolorem eum fugiat", \
			"quo voluptas nulla pariatur?"\
		]

# Setup sqlite
sqlite_file = 'hyper.db'

# Connect to the database sqlite file
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()

# delete all entries and reset id
db.execute("DELETE FROM TweetsRaw")
db.execute("UPDATE SQLITE_SEQUENCE SET seq = 0 WHERE name = 'TweetsRaw'") # init starting id to 1
connection.commit()

# add fake tweets
for t in range(1, total_num_tweets+1):

	# construct tweet text as a list and add the first part of the text
	tweet_text_list = [format(random.choice(texts))]

	# add 3 random 'printable' characters (to test possible problems with sql query)
	for c in range(0, 3):
		tweet_text_list.append(random.choice(string.printable))

	# add another random text
	tweet_text_list.append(format(random.choice(texts)))

	# randomly add one of the bands in the list (as text or as mention)
	bands_to_add = random.randint(0,2)
	for b in range(0, bands_to_add):
		if random.randint(0,1) == 1:
			# add band as text
			if random.randint(0,1) == 1:
				# add as it is
				tweet_text_list.append(random.choice(bands)["name"])
			else:
				# add lowercase
				tweet_text_list.append(random.choice(bands)["name"].lower())
		else:
			# add band as mention
			tweet_text_list.append(random.choice(bands)["twitter"])

	# TODO: randomly add a random emoticon

	# randomly add a random mention
	if random.randint(0,1) == 1:
		tweet_text_list.append("@{}".format(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))))  

	# randomly add a random hashtag
	if random.randint(0,1) == 1:
		tweet_text_list.append("#{}".format(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))))  

	# randomly add a random url
	if random.randint(0,1) == 1:
		tweet_text_list.append("http://{}.{}/{}".format(\
			''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(4)),\
			''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(3)),\
			''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))\
		))  

	# transform tweet list into a string separated by spaces
	tweet_text = ' '.join(tweet_text_list)
	#print(tweet_text)

	# add generated tweet into db
	try:
		db.execute("INSERT INTO TweetsRaw (tweetId,createdAt,storedAt,tweetText,favsCount,rtsCount,language,userFriendsCount,userId,userFollowersCount,userStatusesCount,userFavsCount,userLocation) \
		            VALUES ('{tweetId}','{createdAt}','{storedAt}','{tweetText}','{favsCount}','{rtsCount}','{language}','{userId}','{userFriendsCount}','{userFollowersCount}','{userStatusesCount}','{userFavsCount}','{userLocation}')".format(\
		                tweetId=0, \
		                createdAt=datetime.now().strftime("%a %b %d %H:%M:%S +0200 %Y"), \
		                storedAt=datetime.now().strftime("%a %b %d %H:%M:%S +0200 %Y"), \
		                tweetText=tweet_text.replace("'","''"), \
		                favsCount=random.randint(0,100), \
		                rtsCount=random.randint(0,100), \
		                language="la", \
		                userId=random.randint(0,10), \
		                userFriendsCount=random.randint(0,1000), \
		                userFollowersCount=random.randint(0,1000), \
		                userStatusesCount=random.randint(0,10000), \
		                userFavsCount=random.randint(0,10000), \
		                userLocation="Barcelona") \
		)
		connection.commit()

	except sqlite3.Error as e:
		print("Error: ", e)

# Count number of inserted rows
db.execute("SELECT COUNT(*) FROM TweetsRaw")
count_rows = db.fetchone()
print("Inserted {}/{} tweets".format(count_rows[0],total_num_tweets))

# close db connection
connection.close()



