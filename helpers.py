import unicodedata
import re

"""
Create Ranking
"""

def extract_bands(tweet, bands):
    """
    Function that extracts the bands from a tweet text
    Returns a list of bands
    """
    
    if tweet.name % 1000 == 0:
        print(tweet.name)
    
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

        # create regex's
        my_regex_1 = r"[., ]" + re.escape(bandname_lowercase) + r"[., ]"
        my_regex_2 = r"[., ]" + re.escape(bandname_lowercase_no_accents) + r"[., ]"
        my_regex_3 = r"[., ]" + re.escape(b['twitterName']) + r"[., ]"

        # check if any of the regex's is in the tweet text
        if  re.search(my_regex_1,tweet['tweetText'].lower()) or \
            re.search(my_regex_2,tweet['tweetText'].lower()) or \
            re.search(my_regex_3,tweet['tweetText'].lower()):
            bands_in_tweet.append({"id": b['id'], "codedName": b['codedName']})

        # if any(s in tweet['tweetText'].lower() for s in [   " {} ".format(bandname_lowercase), 
        #                                                     " {} ".format(bandname_lowercase_no_accents), 
        #                                                     "{},".format(bandname_lowercase), 
        #                                                     "{},".format(bandname_lowercase_no_accents), 
        #                                                     ",{}".format(bandname_lowercase), 
        #                                                     ",{}".format(bandname_lowercase_no_accents),
        #                                                     b['twitterName']]):
        #     bands_in_tweet.append({"id": b['id'], "codedName": b['codedName']})

    return bands_in_tweet


def band_partition(tweet, new_band_tweets_list, db, connection):
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


def compareBandPosition(band_row, last_ranking):
    """
    Function that compares the position of a band in the current ranking (in band_row) compared to the
    position in the last ranking
    """
    new_position = band_row.ranking_position
    difference = 0
    if(any(last_ranking['bandId'].isin([band_row['bandId']]))):
        last_position = last_ranking['ranking_position'][last_ranking.bandId == band_row.bandId].values[0]
        difference = last_position - new_position
    return difference
