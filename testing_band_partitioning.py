"""
Script used to test how bands are detected in tweets
"""

import sqlite3
import pandas as pd
import string
import numpy as np
from datetime import datetime, timedelta

import helpers

"""
SETUP DB
"""
sqlite_file = 'hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()


"""
LOAD DATA
"""

# get list of bands from db
bands = pd.read_sql_query("SELECT * FROM Bands;", connection)
print("{} bands read".format(len(bands)))

# read ONLY tweets that have to be processed
tweets_to_process = pd.read_sql_query("SELECT * FROM TweetsRaw WHERE tweetText LIKE '%soledad%' LIMIT 100", connection)
print("{} tweets to be processed".format(len(tweets_to_process)))


"""
PARTITION PER BAND
"""

# Extract bands and create dataframe of BandTweets
if(tweets_to_process.shape[0] > 0):

    # extract bands for each tweet
    tweets_to_process['bands'] = tweets_to_process.apply((lambda row: helpers.extract_bands(row, bands)), axis=1)

    # construct the list of tweets per band
    new_band_tweets_list = []
    tweets_to_process.apply((lambda row: helpers.band_partition(row, new_band_tweets_list, db, connection)), axis=1);

    # create a dataframe from the previous list
    new_band_tweets = pd.DataFrame.from_dict(new_band_tweets_list)
    print("{} band-tweets".format(new_band_tweets.shape[0]))
else:
    new_band_tweets = pd.DataFrame([])
    print("No new tweets to process")
