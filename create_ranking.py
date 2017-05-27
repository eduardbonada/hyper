"""
Script that collects tweets information, pertitions per band, and updates ranking
"""

import sqlite3
import pandas as pd
import string
import unicodedata
import numpy as np
from datetime import datetime, timedelta

import helpers

"""
SETUP DB
"""
sqlite_file = 'hyper_live.db'
#sqlite_file = '/home/ebonada/python/hyper/hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()


"""
LOAD DATA
"""

# get list of bands from db
bands = pd.read_sql_query("SELECT * FROM Bands;", connection)
print("{} bands read".format(len(bands)))

# read ONLY tweets that have to be processed
tweets_to_process = pd.read_sql_query("SELECT * FROM TweetsRaw WHERE processed IS NULL", connection)
print("{} tweets to be processed".format(len(tweets_to_process)))


"""
PARTITION PER BAND
"""

# Extract bands and create dataframe of BandTweets
if(tweets_to_process.shape[0] > 0):

    # extract bands for each tweet
    tweets_to_process['bands'] = tweets_to_process.apply(helpers.extract_bands, axis=1)

    # construct the list of tweets per band
    new_band_tweets_list = []
    tweets_to_process.apply(helpers.band_partition, axis=1);

    # create a dataframe from the previous list
    new_band_tweets = pd.DataFrame.from_dict(new_band_tweets_list)
    print("{} band-tweets".format(new_band_tweets.shape[0]))
else:
    new_band_tweets = pd.DataFrame([])
    print("No new tweets to process")

# Persist extracted tweets in DB (BandTweets table)
if(new_band_tweets.shape[0] > 0):
    new_band_tweets[['tweetRawId', 'bandId']].to_sql('BandTweets', connection, if_exists='append')
    print("{} new band tweets persisted".format(new_band_tweets.shape[0]))
else:
    print("No new band tweets to persist")


"""
GET ALL BANDTWEETS
"""

# Construct a dataframe joining data from TweetsRaw and BandTweets
band_tweets = pd.read_sql_query("""
									SELECT bt.bandId, b.name AS bandName, b.codedName AS bandCodedName, b.headLevel AS headLevel, b.popularity AS popularity, tr.* 
	                                FROM BandTweets AS bt
	                                LEFT JOIN TweetsRaw AS tr ON bt.tweetRawId == tr.id 
	                                LEFT JOIN Bands AS b ON bt.bandId == b.id
	                            """, 
                                connection)
print("{} band tweets in db".format(band_tweets.shape[0]))


"""
COMPUTE CURRENT RANKING (BANDHYPE)
"""

# group and sum band tweets by band
band_hypes = band_tweets.groupby(['bandCodedName', 'bandName', 'bandId', 'headLevel', 'popularity']).sum()

# insert a column with the number of tweets
band_hypes['tweets'] = band_tweets.groupby(['bandCodedName', 'bandName', 'bandId', 'headLevel', 'popularity']).size()

# reset the index created in the group by
band_hypes = band_hypes.reset_index()

# delete not needed columns
del band_hypes['id']
del band_hypes['userFriendsCount']
del band_hypes['userFollowersCount']
del band_hypes['userStatusesCount']
del band_hypes['userFavsCount']
del band_hypes['processed']

# add createdAt column
band_hypes['createdAt'] = datetime.now().strftime("%a %b %d %H:%M:%S +0000 %Y")

# rename and re-order columns
band_hypes = band_hypes.rename(columns={'favsCount':'favs', 'rtsCount':'retweets'})
band_hypes = band_hypes[['bandId', 'bandCodedName', 'bandName', 'headLevel', 'popularity', 'tweets', 'favs', 'retweets', 'createdAt']]

# Compute BF-IBP (Band Frequency - Inverse Band Popularity)
bf_numerator = band_hypes['tweets']*(1 + band_hypes['favs'] + band_hypes['retweets'])
band_hypes['bf_ibp'] = (bf_numerator/bf_numerator.sum()) * np.log(band_hypes['popularity'].astype(float) + 1)


"""
COMPUTE CHANGES IN RANKING
"""

# Get last ranking
last_ranking = pd.read_sql_query("""
                                    SELECT * 
                                    FROM BandsHype
                                    ORDER BY bf_ibp DESC
                                """, 
                                connection)

# read the last N rankings from the historical table
last_n_rankings = pd.read_sql_query("""
                                    SELECT * 
                                    FROM BandsHypeHis
                                    """, 
                                connection)

# add a column indicating change in ranking
band_hypes['ranking_position'] = band_hypes['bf_ibp'].rank(ascending=0)
band_hypes['ranking_change'] = band_hypes.apply((lambda row: helpers.compareBandPosition(row, last_ranking)), axis=1)

#band_hypes['ranking_change'] = 0 # uncomment if BandHype is empty

# create a datetime version of createdAt
last_n_rankings['createdAt_datetime'] = pd.to_datetime(last_n_rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')

# filter rankings of only last hour
last_n_rankings = last_n_rankings[ last_n_rankings['createdAt_datetime'] > (datetime.now() - timedelta(hours=48))]

# compute accumulated ranking changes
cumulated_ranking_changes = pd.DataFrame(last_n_rankings.groupby('bandId')['ranking_change'].sum())
cumulated_ranking_changes = cumulated_ranking_changes.rename(columns={'ranking_change':'trending_level'})
cumulated_ranking_changes = cumulated_ranking_changes.reset_index()

# join dfs
band_hypes = pd.merge(band_hypes, cumulated_ranking_changes, left_on='bandId', right_on='bandId', how='left')


"""
PERSIST TO DB
"""
# table with current ranking
band_hypes[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].to_sql("BandsHype", connection, if_exists="replace", index=False)

# table with historical of rankings
band_hypes[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level','createdAt']].to_sql("BandsHypeHis", connection, if_exists="append", index=False)


"""
LOG
"""
print(band_hypes.columns)
#print("LAST RANKING\n{}".format(last_ranking[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].head(10)))
#print("NEW RANKING\n{}".format(band_hypes[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].sort_values('bf_ibp', ascending=False).head(10)))
print("TOP RANKED\n{}".format(band_hypes[['bandCodedName','ranking_position','ranking_change','trending_level']].sort_values('ranking_position', ascending=True).head(5)))
print("TOP TRENDING\n{}".format(band_hypes[['bandCodedName','ranking_position','ranking_change','trending_level']].sort_values('trending_level', ascending=False).head(5)))



