import tweepy
import sqlite3
from pprint import pprint

# Setup twitter API access
consumer_key = 'Ib3yDL5HYSLxAqENZ6QCHRFex'
consumer_secret = 'TuTQKld9os111vx7oMSM3PTfoNz9dZDcnACxIvHGL9euIvLE8I'
access_token = '74265344-UOJgWD9vzB9wJvgnet3f63bkQdJ0rLGz9gg67fqDP'
access_secret = '4AFqod7kCScnSDf9OcgmVeIdnxwa9ZKn9pwwFMBbpLi7u'

# Setup sqlite
sqlite_file = 'hyper.db'

# Connect to the database sqlite file
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()

query = 'python'
max_tweets = 10
searched_tweets = [status for status in tweepy.Cursor(api.search, q=query).items(max_tweets)]


# Store the tweet in DB
try:
    db.execute("INSERT INTO TweetsRaw (tweetId,createdAt,tweetText,favsCount,rtsCount,language,userFriendsCount,userFollowersCount,userStatusesCount,userFavsCount,userLocation) \
                VALUES ('{tweetId}','{createdAt}','{tweetText}','{favsCount}','{rtsCount}','{language}','{userFriendsCount}','{userFollowersCount}','{userStatusesCount}','{userFavsCount}','{userLocation}')".format(\
                    tweetId=tweet_info['id_str'], \
                    createdAt=tweet_info['created_at'], \
                    tweetText=tweet_info['text'], \
                    favsCount=tweet_info['favorite_count'], \
                    rtsCount=tweet_info['retweet_count'], \
                    language=tweet_info['lang'], \
                    userFriendsCount=tweet_info['user']['friends_count'], \
                    userFollowersCount=tweet_info['user']['followers_count'], \
                    userStatusesCount=tweet_info['user']['statuses_count'], \
                    userFavsCount=tweet_info['user']['favourites_count'], \
                    userLocation=tweet_info['user']['location']) \
    )
except sqlite3.Error as e:
    print("Error: ", e)

# Commit and close
connection.commit()
connection.close()
    
# Manage twitter API access
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

# Create tweepy instance
api = tweepy.API(auth)

# Setup streaming
twitter_stream = tweepy.Stream(auth, TweetsListener())

# Launch streaming
twitter_stream.filter(track=['#trump'])