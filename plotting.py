"""
Script that creates a plot with a tweet timeline
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
import seaborn as sns


"""
SETUP DB
"""
#sqlite_file = 'hyper_live.db'
#sqlite_file = '/Users/eduard/DeveloperWeb/hyper/hyper_live.db'
sqlite_file = '/home/ebonada/python/hyper/hyper_live.db'
connection = sqlite3.connect(sqlite_file)
db = connection.cursor()


"""
PLOT WITH ALL TWEETS
"""

# read ALL tweets from db
all_tweets = pd.read_sql_query("SELECT * FROM TweetsRaw", connection)
all_tweets['createdAt'] = pd.to_datetime(all_tweets['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
all_tweets.index = all_tweets['createdAt']

# Construct a dataframe joining data from TweetsRaw and BandTweets
band_tweets = pd.read_sql_query(""" SELECT bt.bandId, 
                                        b.name AS bandName, 
                                        b.codedName AS bandCodedName, 
                                        b.headLevel AS headLevel, 
                                        b.popularity AS popularity, 
                                        tr.* 
                                    FROM BandTweets AS bt 
                                    LEFT JOIN TweetsRaw AS tr ON bt.tweetRawId == tr.id 
                                    LEFT JOIN Bands AS b ON bt.bandId == b.id""", connection)
band_tweets['createdAt'] = pd.to_datetime(band_tweets['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
band_tweets.index = band_tweets['createdAt']

# timeline plot comparing alltweets vs bandtweets
fig = plt.figure()
ax1 = fig.add_subplot(211)
all_tweets.resample('D').count()['tweetId'].plot(kind='bar', \
                                                 color=sns.xkcd_rgb['sky'], \
                                                 label='All', \
                                                 ax=ax1)
band_tweets.resample('D').count()['bandId'].plot(kind='bar', \
                                                 color=sns.xkcd_rgb['green'], \
                                                 label='Bands', \
                                                 ax=ax1)
ax1.set_title(datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
ax1.set_xlabel("All Days")
ax1.set_xticklabels([])
#ax1.set_xticklabels(list(np.arange(min(all_tweets['createdAt']).day, max(all_tweets['createdAt']).day + 1)), rotation=None)
ax1.set_ylabel("Tweets")
ax1.legend()

"""
PLOT WITH RECENT TWEETS
"""

# get recent tweets (last 24h)
recent_all_tweets = all_tweets[ all_tweets['createdAt'] > (datetime.now() - timedelta(hours=24))]
recent_band_tweets = band_tweets[ band_tweets['createdAt'] > (datetime.now() - timedelta(hours=24))]

# plot last day of tweets & band_tweets
ax2 = fig.add_subplot(212)
ax2 = recent_all_tweets.resample('H').count()['tweetId'].plot(kind='bar', color=sns.xkcd_rgb['sky'], label='All', ax=ax2)
recent_band_tweets.resample('H').count()['bandId'].plot(kind='bar', color=sns.xkcd_rgb['green'], label='Bands', ax=ax2)
ax2.set_xlabel("Last 24h")
ax2.set_xticklabels([])
ax2.set_ylabel("Tweets")
ax2.legend()

# store in file
fig = ax2.get_figure()
#fig.savefig("tweets.png")
fig.savefig("/home/ebonada/python/hyper/server/public/images/tweets.png")
#fig.savefig("/Users/eduard/DeveloperWeb/hyper/public/images/tweets.png")


"""
PLOT WITH RANKING EVOLUTION
"""

# Read current ranking
current_ranking = pd.read_sql_query("""	SELECT b.codedName AS bandCodedName, cr.tweets, cr.favs, cr.retweets, cr.bf_ibp 
                                       	FROM BandsHype AS cr 
                                    	LEFT JOIN Bands AS b ON cr.bandId = b.id""", connection)

# Read history of rankings
rankings = pd.read_sql_query("""SELECT b.codedName AS bandCodedName, rs.tweets, rs.favs, rs.retweets, rs.bf_ibp, rs.createdAt 
                            	FROM BandsHypeHis AS rs
                            	LEFT JOIN Bands AS b ON rs.bandId = b.id""", connection)

# filter last N-hours
rankings['createdAt'] = pd.to_datetime(rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
recent_rankings = rankings[ rankings['createdAt'] > (datetime.now() - timedelta(hours=24))]

# get top-10 bands
top_10 = current_ranking.sort_values('bf_ibp', ascending = False)['bandCodedName'][0:10]

# plot band evolution
bands = top_10 #['arcadefire', '!!!', 'frankocean']
ax3 = plt.figure().add_subplot(111)
for b in bands:
    recent_rankings[recent_rankings['bandCodedName'] == b].set_index('createdAt').plot(y='bf_ibp', label=b, ax=ax3)
ax3.set_title('Evolution of bf_ibp')
ax3.set_ylabel('bf_ibp')
ax3.set_xlabel('Last 24h')
ax3.set_xticklabels([])
plt.gcf().subplots_adjust(bottom=0.15)
ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5)

# store in file
fig = ax3.get_figure()
#fig.savefig("rankings.png")
fig.savefig("/home/ebonada/python/hyper/server/public/images/rankings.png")
#fig.savefig("/Users/eduard/DeveloperWeb/hyper/public/images/rankings.png")

