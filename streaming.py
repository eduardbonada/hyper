"""
Script that listens tweets from the Twitter Streaming API (according to searching query) and stores them into the given sqlite db
"""

# https://marcobo# https://www.dataquest.io/blog/streaming-data-python/
# https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/
# http://adilmoujahid.com/posts/2014/07/twitter-analytics/
# http://sebastianraschka.com/Articles/2014_sqlite_in_python_tutorial.html

import tweepy
import sqlite3
from datetime import datetime
from pprint import pprint

# track number of tweets (developing purposes)
max_tweets_to_store = -1 # maximum number of tweets to store before shutting down the streaming (-1 for non stop)

# Class that manages the events received from streaming API
class TweetsListener(tweepy.StreamListener):
 
    def __init__(self):
        """ Initialize listener """
        self.count = 0
        super(TweetsListener, self).__init__()
    
    def on_status(self, status):
        """ Manage 'status' event."""

        self.count = self.count + 1

        tweet_info = status._json;

        print("Received tweet #{} {} => {}".format(self.count, tweet_info['id_str'],tweet_info['text']))
        #pprint(status)
        # print(tweet_info['id_str'])

        # Connect to the database sqlite file
        connection = sqlite3.connect(sqlite_file)
        db = connection.cursor()

        # Store the tweet in DB
        try:
            db.execute("INSERT OR IGNORE INTO TweetsRaw (tweetId,createdAt,storedAt,tweetText,favsCount,rtsCount,language,userId,userFriendsCount,userFollowersCount,userStatusesCount,userFavsCount,userLocation) \
                        VALUES ('{tweetId}','{createdAt}','{storedAt}','{tweetText}','{favsCount}','{rtsCount}','{language}','{userId}','{userFriendsCount}','{userFollowersCount}','{userStatusesCount}','{userFavsCount}','{userLocation}')".format(\
                            tweetId=tweet_info['id_str'], \
                            createdAt=tweet_info['created_at'], \
                            storedAt=datetime.now().strftime("%a %b %d %H:%M:%S +0200 %Y"), \
                            tweetText=tweet_info['text'].replace("'","''"), \
                            favsCount=tweet_info['favorite_count'], \
                            rtsCount=tweet_info['retweet_count'], \
                            language=tweet_info['lang'], \
                            userId=tweet_info['user']['id_str'], \
                            userFriendsCount=tweet_info['user']['friends_count'], \
                            userFollowersCount=tweet_info['user']['followers_count'], \
                            userStatusesCount=tweet_info['user']['statuses_count'], \
                            userFavsCount=tweet_info['user']['favourites_count'], \
                            userLocation='') \
            )
            # tweet_info['user']['location'].replace("'","''"))
        except sqlite3.Error as e:
            print("####################\nError: {}\n####################\n".format(e))

        # Commit and close
        connection.commit()
        connection.close()

        # shut down streaming if maximum number of tweets has been reached
        if max_tweets_to_store != -1:
            if self.count == max_tweets_to_store:
                return False

        return True
 
    def on_error(self, status):
        """ Manage 'error' event."""

        print("Error TweetsListener:on_error => %s" % str(status))
        return True


# Setup twitter API access
consumer_key = 'Ib3yDL5HYSLxAqENZ6QCHRFex'
consumer_secret = 'TuTQKld9os111vx7oMSM3PTfoNz9dZDcnACxIvHGL9euIvLE8I'
access_token = '74265344-UOJgWD9vzB9wJvgnet3f63bkQdJ0rLGz9gg67fqDP'
access_secret = '4AFqod7kCScnSDf9OcgmVeIdnxwa9ZKn9pwwFMBbpLi7u'

# Setup sqlite
sqlite_file = 'hyper.db'
    
# Manage twitter API access
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

# Create tweepy instance
api = tweepy.API(auth)

# Setup streaming
twitter_stream = tweepy.Stream(auth, TweetsListener())

# Launch streaming
twitter_stream.filter(track=['@Primavera_Sound','primavera sound', '#PS2017'])
