"""
Script that collects info from various origins and creates a text-based monitorign report
"""

production = 1

import sqlite3
import pandas as pd
import os

# files
# cron_ranking_file = 'cron_ranking.log'
# cron_plotting_file = 'cron_plotting.log'
# cron_search_file = 'cron_search.log'
#cron_streaming_file = 'cron_search.log'
cron_ranking_file = '/home/ebonada/python/hyper/cron_ranking.log'
cron_plotting_file = '/home/ebonada/python/hyper/cron_plotting.log'
cron_search_file = '/home/ebonada/python/hyper/cron_search.log'
cron_streaming_file = '/home/ebonada/python/hyper/streaming.log'


# SETUP DB
if production == 0:
    sqlite_file = 'hyper_live.db'
else:
    sqlite_file = '/home/ebonada/python/hyper/hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()


# Top ranked and top trending
ranking = pd.read_sql_query("SELECT * FROM BandsHype AS bh LEFT JOIN Bands AS b ON bh.bandId = b.id", connection)
ranking = ranking.rename(columns={'tweets':'tw', 'favs':'fv', 'retweets':'rt','ranking_position':'pos', 'ranking_change':'chng', 'trending_level':'trend'})
ranking['bfibp'] = ranking['bf_ibp'].round(2)
print("\n\n********************\nTOP RANKED\n\n{}".format(ranking.sort_values('bf_ibp', ascending=False).head(10)[['name','tw','fv','rt','bfibp','pos','chng','trend']]))
print("\n\n********************\nTOP TRENDING\n\n{}".format(ranking.sort_values('trend', ascending=False).head(10)[['name','tw','fv','rt','bfibp','pos','chng','trend']]))


# Number of tweets in db
db.execute("SELECT COUNT(*) FROM TweetsRaw")
num_tweets = db.fetchone()[0]
db.execute("SELECT COUNT(*) FROM BandTweets")
num_band_tweets = db.fetchone()[0]
print("\n\n********************\nDB COUNTS\n")
print("    Tweets Raw:  {}".format(num_tweets))
print("    Band Tweets: {}".format(num_band_tweets))


# List of last N tweets
tweetsRaw = pd.read_sql_query("SELECT * FROM TweetsRaw ORDER BY id DESC LIMIT 10", connection)
tweetsRaw['createdAt'] = pd.to_datetime(tweetsRaw['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y').dt.strftime('%d %H:%M')
print("\n\n********************\nLAST TWEETS\n\n{}".format(tweetsRaw[['createdAt', 'tweetText']].values))


# List of last N band tweets
bandTweets = pd.read_sql_query("SELECT * FROM BandTweets AS bt LEFT JOIN TweetsRaw AS tr ON bt.tweetRawId = tr.id ORDER BY tr.id DESC LIMIT 10", connection)
bandTweets['createdAt'] = pd.to_datetime(bandTweets['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y').dt.strftime('%d %H:%M')
print("\n\n********************\nLAST BAND TWEETS\n\n{}".format(bandTweets[['createdAt', 'tweetText']].values))


# Last streamed tweets
try:
	print("\n\n********************\nSTREAMING LOG\n")
	with open(cron_streaming_file) as fid:
	    lines = fid.readlines()
	for line in lines[len(lines)-10:]:
	    print(line, end='')
except:
	print('ERROR: Streaming log file not found')


# Results of last crons
try:
	print("\n\n********************\nCRON RANKING LOG\n")
	with open(cron_ranking_file) as fid:
	    lines = fid.readlines()
	for line in lines:
	    print(line, end='')
	os.remove(cron_ranking_file)

	print("\n\n********************\nCRON SEARCH LOG\n")
	with open(cron_search_file) as fid:
	    lines = fid.readlines()
	for line in lines[len(lines)-10:]:
	    print(line, end='')
	if len(lines) >= 10:
		os.remove(cron_search_file) 

	print("\n\n********************\nCRON PLOTTING LOG\n")
	with open(cron_plotting_file) as fid:
	    lines = fid.readlines()
	for line in lines[len(lines)-4:]:
	    print(line, end='')
	os.remove(cron_plotting_file)

except:
	print('ERROR: Some problem with the cron log files')


