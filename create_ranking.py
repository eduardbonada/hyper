"""
Script that collects tweets information, pertitions per band, and updates ranking
"""

production = 1

import sqlite3
import pandas as pd
import string
import numpy as np
from datetime import datetime, timedelta

import helpers

"""
SETUP DB
"""
if production == 0:
    sqlite_file = 'hyper_live.db'
else:
    sqlite_file = '/home/ebonada/python/hyper/hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()


"""
LOAD DATA
"""

# get list of bands from db
bands = pd.read_sql_query("SELECT * FROM Bands;", connection)
#print("{} bands read".format(len(bands)))

# read ONLY tweets that have to be processed
tweets_to_process = pd.read_sql_query("SELECT * FROM TweetsRaw WHERE processed IS NULL", connection)
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
new_ranking = band_tweets.groupby(['bandCodedName', 'bandName', 'bandId', 'headLevel', 'popularity']).sum()

# insert a column with the number of tweets
new_ranking['tweets'] = band_tweets.groupby(['bandCodedName', 'bandName', 'bandId', 'headLevel', 'popularity']).size()

# reset the index created in the group by
new_ranking = new_ranking.reset_index()

# delete not needed columns
del new_ranking['id']
del new_ranking['userFriendsCount']
del new_ranking['userFollowersCount']
del new_ranking['userStatusesCount']
del new_ranking['userFavsCount']
del new_ranking['processed']

# add createdAt column
new_ranking['createdAt'] = datetime.now().strftime("%a %b %d %H:%M:%S +0000 %Y")

# rename and re-order columns
new_ranking = new_ranking.rename(columns={'favsCount':'favs', 'rtsCount':'retweets'})
new_ranking = new_ranking[['bandId', 'bandCodedName', 'tweets', 'favs', 'retweets', 'createdAt', 'popularity']]

# Compute BF-IBP (Band Frequency - Inverse Band Popularity)
#bf_numerator = new_ranking['tweets']*(1 + new_ranking['favs'] + new_ranking['retweets'])
#bf_numerator = new_ranking['tweets'] + np.log(1+new_ranking['retweets']) + np.log(1+new_ranking['favs'])
bf_numerator = new_ranking['tweets']
new_ranking['bf_ibp'] = (bf_numerator/bf_numerator.sum()) * np.log(new_ranking['popularity'].astype(float) + 1)


"""
COMPUTE CHANGES IN RANKING
"""

last_n_rankings_minutes = 60
if production == 0:
	# add 2h due to hour difference between local and server
	last_n_rankings_minutes = last_n_rankings_minutes + 120

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
last_n_rankings['bandCodedName'] = "" # fake name to match columns for a later merge

# add a column indicating ranking position
new_ranking['ranking_position'] = new_ranking['bf_ibp'].rank(ascending=0, method='first')

# add a column indicating position change compared to last ranking
if not last_ranking.empty:
    # if there is a last_ranking
    new_ranking['ranking_change'] = new_ranking.apply((lambda row: helpers.compareBandPosition(row, last_ranking)), axis=1)
else:
    # if there is no last_ranking yet
    new_ranking['ranking_change'] = 0


# add current ranking to lost of last_n_rankings
new_ranking = new_ranking[['bandId', 'bandCodedName', 'tweets', 'favs', 'retweets', 'createdAt', 'bf_ibp', 'ranking_position', 'ranking_change']]
last_n_rankings = last_n_rankings[['bandId', 'bandCodedName', 'tweets', 'favs', 'retweets', 'createdAt', 'bf_ibp', 'ranking_position', 'ranking_change']]
last_n_rankings = pd.concat([last_n_rankings, new_ranking])

# filter rankings of only last hour
last_n_rankings['createdAt_datetime'] = pd.to_datetime(last_n_rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
last_n_rankings = last_n_rankings[ last_n_rankings['createdAt_datetime'] > (datetime.now() - timedelta(minutes=last_n_rankings_minutes))]

# compute trending_level as tweets during the window defined by last_n_rankings
if not last_n_rankings.empty:
    data_start_window = last_n_rankings[['bandId', 'tweets', 'bf_ibp', 'createdAt_datetime']].sort_values('createdAt_datetime', ascending=True).groupby('bandId').head(1)
    data_end_window = last_n_rankings[['bandId', 'tweets', 'bf_ibp', 'createdAt_datetime']].sort_values('createdAt_datetime', ascending=False).groupby('bandId').head(1)

    # print(data_start_window[data_start_window['bandId'] == 21]);
    # print(data_end_window[data_end_window['bandId'] == 21]);

    trending_level = pd.merge(data_start_window, data_end_window, left_on='bandId', right_on='bandId', how='left')
    trending_level['trending_level'] = trending_level['bf_ibp_y'] - trending_level['bf_ibp_x']

    #print(trending_level[trending_level['bandId'] == 21][['bandId', 'trending_level']].sort_values('trending_level', ascending=False ))

else:
    trending_level = pd.DataFrame(columns=['bandId', 'trending_level'])


# # compute trending_level as accumulated ranking changes during last_n_rankings
# if not last_n_rankings.empty:
#     if last_n_rankings[last_n_rankings['ranking_change'] == -1].shape[0] > 0:
#         last_n_rankings.loc[last_n_rankings['ranking_change'] == -1, 'ranking_change'] = 0 # clear negative ranking_changes
#     trending_level = pd.DataFrame(last_n_rankings[last_n_rankings['ranking_change']>=0].groupby('bandId')['ranking_change'].sum())
#     trending_level = trending_level.rename(columns={'ranking_change':'trending_level'})
#     trending_level = trending_level.reset_index()
# else:
#     trending_level = pd.DataFrame(columns=['bandId', 'trending_level'])

# add trending_level to final ranking by joining dfs
new_ranking = pd.merge(new_ranking, trending_level, left_on='bandId', right_on='bandId', how='left')



"""
PERSIST TO DB
"""
if production == 1:

	# table with current ranking
	new_ranking[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].to_sql("BandsHype", connection, if_exists="replace", index=False)

	# table with historical of rankings
	new_ranking[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level','createdAt']].to_sql("BandsHypeHis", connection, if_exists="append", index=False)


"""
LOG
"""
if production == 0:
    #print("LAST RANKING\n{}".format(last_ranking[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].head(10)))
    #print("NEW RANKING\n{}".format(band_hypes[['bandId','tweets','favs','retweets','bf_ibp','ranking_position','ranking_change','trending_level']].sort_values('bf_ibp', ascending=False).head(10)))
    print("\nTOP RANKED\n{}".format(new_ranking[['bandCodedName','tweets','favs','retweets','bf_ibp','ranking_position']].sort_values('ranking_position', ascending=True).head(10)))
    print("\nTOP TRENDING\n{}".format(new_ranking[['bandCodedName','tweets','favs','retweets','bf_ibp','trending_level']].sort_values('trending_level', ascending=False).head(10)))



