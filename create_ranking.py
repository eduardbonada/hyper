"""
Script that collects tweets information, pertitions per band, and updates ranking
"""

import sqlite3
import pandas as pd
import string
import unicodedata
import numpy as np
from datetime import datetime

# Setup sqlite and connect to it
#sqlite_file = 'hyper_live.db'
sqlite_file = '/home/ebonada/python/hyper/hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()

"""
Aux functions
"""

def extract_bands(tweet):
    """
    Function that extracts the bands from a tweet text
    Returns a list of bands
    """
    
    # init list to return
    bands_in_tweet = []
    
    # loop all bands and check of any of the written forms is present in the tweet text
    for i, b in bands.iterrows():
                
        # set different band names writing possibilities
        bandname = b['name']
        bandname_lowercase = bandname.lower()
        bandname_lowercase_no_spaces = ''.join(bandname_lowercase.split())
        bandname_lowercase_no_accents = ''.join((c for c in unicodedata.normalize('NFD', bandname_lowercase) if unicodedata.category(c) != 'Mn'))
        bandname_lowercase_no_spaces_no_accents = ''.join((c for c in unicodedata.normalize('NFD', bandname_lowercase_no_spaces) if unicodedata.category(c) != 'Mn'))

        # check if any of the forms is in the tweet text
        if any(s in tweet['tweetText'].lower() for s in [bandname_lowercase, bandname_lowercase_no_spaces, bandname_lowercase_no_accents, bandname_lowercase_no_spaces_no_accents, b['twitterName']]):
            bands_in_tweet.append({"id": b['id'], "codedName": b['codedName']})

    return bands_in_tweet


def band_partition(tweet):
    """
    Function that reads a single tweet info and adds into a list the tweet information partitioned by bands.
    I.e. If a tweet mentions 2 bands, it adds a list of 2 dicts with the tweet info
    """
    
    # loop all bands and add an entry to the list
    for b in tweet['bands']:
        new_band_tweets_list.append({\
                                 "tweetRawId" : tweet['id'],\
                                 "createdAt" : tweet['createdAt'],\
                                 "storedAt" : tweet['storedAt'],\
                                 "bandId" : b['id'],\
                                 "bandCodedName" : b['codedName'],\
                                 "favsCount" : tweet['favsCount'],\
                                 "rtsCount" : tweet['rtsCount'],\
                                 "language" : tweet['language'],\
                                 "userId" : tweet['userId'],\
                                 "userFriendsCount" : tweet['userFriendsCount'],\
                                 "userFollowersCount" : tweet['userFollowersCount'],\
                                 "userStatusesCount" : tweet['userStatusesCount'],\
                                 "userFavsCount" : tweet['userFavsCount'],\
                                 "userLocation" : tweet['userLocation']\
                                })
    
    # Mark TweetsRaw as processed
    db.execute("UPDATE TweetsRaw SET processed = 1 WHERE id == {}".format(tweet.id))
    connection.commit()


"""
Load Data
"""

# get list of bands from db
bands = pd.read_sql_query("SELECT * FROM Bands;", connection)
print("{} bands read".format(len(bands)))

# read ONLY tweets that have to be processed
tweets_to_process = pd.read_sql_query("SELECT * FROM TweetsRaw WHERE processed IS NULL", connection)
print("{} tweets to be processed".format(len(tweets_to_process)))


"""
Partition per band
"""

# Extract bands and create dataframe of BandTweets
if(tweets_to_process.shape[0] > 0):

    # extract bands for each tweet
    tweets_to_process['bands'] = tweets_to_process.apply(extract_bands, axis=1)

    # construct the list of tweets per band
    new_band_tweets_list = []
    tweets_to_process.apply(band_partition, axis=1);

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
Get all BandTweets info
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
 Compute ranking and BandHype
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

# Get last ranking
last_ranking = pd.read_sql_query("""
                                    SELECT * 
                                    FROM BandsHype
                                    ORDER BY bf_ibp DESC
                                """, 
                                connection)
print("LAST RANKING\n{}".format(last_ranking.head(10)))

# uncomment if the last ranking does not have ranking_position yet
#print('!!!!!!\nREMOVE THIS LINE\n!!!!!!\n')
#last_ranking['ranking_position'] = last_ranking['bf_ibp'].rank(ascending=0)

# rename and re-order columns
band_hypes = band_hypes.rename(columns={'favsCount':'favs', 'rtsCount':'retweets'})
band_hypes = band_hypes[['bandId', 'bandCodedName', 'bandName', 'headLevel', 'popularity', 'tweets', 'favs', 'retweets', 'createdAt']]

# # merge bands with different names that are actually the same band: !!! and chk chk chk
# a=band_hypes[band_hypes['bandCodedName']=='!!!']
# b=band_hypes[band_hypes['bandCodedName']=='chkchkchk']
# band_hypes.loc[band_hypes.bandCodedName == '!!!', 'tweets'] = a.tweets.values[0] + b.tweets.values[0]
# band_hypes.loc[band_hypes.bandCodedName == '!!!', 'favs'] = a.favs.values[0] + b.favs.values[0]
# band_hypes.loc[band_hypes.bandCodedName == '!!!', 'retweets'] = a.retweets.values[0] + b.retweets.values[0]
# band_hypes = band_hypes.drop(band_hypes[band_hypes.bandCodedName == 'chkchkchk'].index)

# Compute BF-IBP (Band Frequency - Inverse Band Popularity)
bf_numerator = band_hypes['tweets']*(1 + band_hypes['favs'] + band_hypes['retweets'])
band_hypes['bf_ibp'] = (bf_numerator/bf_numerator.sum()) * np.log(band_hypes['popularity'].astype(float) + 1)

def compareBandPosition(band_row):
    """
    Function that compares the position of a band in the current ranking (in band_row) compared to the
    position in the last ranking
    """
    new_position = band_row.ranking_position
    difference = 0
    if(any(last_ranking['bandId'].isin([band_row['bandId']]))):
        last_postion = last_ranking['ranking_position'][last_ranking.bandId == band_row.bandId].values[0]
        difference = last_postion - new_position
    return difference

# add a column indicating change in ranking
band_hypes['ranking_position'] = band_hypes['bf_ibp'].rank(ascending=0)
band_hypes['ranking_change'] = band_hypes.apply(compareBandPosition, axis=1)
# band_hypes['ranking_change'] = 0

# add a column indicating the the trending level (based on the last position changes)


# log top 10
print("NEW RANKING\n{}".format(band_hypes.sort_values(by='bf_ibp', ascending=False).head(10)))

"""
Persist band_hypes to DB
"""
# table with current ranking
band_hypes[['bandId','tweets','favs','retweets','bf_ibp', 'ranking_change', 'ranking_position']].to_sql("BandsHype", connection, if_exists="replace", index=False)

# table with historical of rankings
band_hypes[['bandId','tweets','favs','retweets','bf_ibp','ranking_change','ranking_position','createdAt']].to_sql("BandsHypeHis", connection, if_exists="append", index=False)


