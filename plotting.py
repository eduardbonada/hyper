"""
Script that creates a plot with a tweet timeline
"""

production = 1

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib as mpl

if production == 1: 
    mpl.use('Agg') # Force matplotlib to not use any Xwindows backend.

import matplotlib.pyplot as plt
import seaborn as sns


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
GET DATA
"""

# read ALL tweets from db
all_tweets = pd.read_sql_query("SELECT tweetId, createdAt FROM TweetsRaw", connection)
all_tweets['createdAt'] = pd.to_datetime(all_tweets['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
all_tweets.index = all_tweets['createdAt']

# Construct a dataframe joining data from TweetsRaw and BandTweets
band_tweets = pd.read_sql_query(""" SELECT bt.bandId, 
                                        b.name AS bandName, 
                                        b.codedName AS bandCodedName,
                                        tr.createdAt
                                    FROM BandTweets AS bt 
                                    LEFT JOIN TweetsRaw AS tr ON bt.tweetRawId == tr.id 
                                    LEFT JOIN Bands AS b ON bt.bandId == b.id""", connection)
band_tweets['createdAt'] = pd.to_datetime(band_tweets['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
band_tweets.index = band_tweets['createdAt']

# Read current ranking
current_ranking = pd.read_sql_query(""" SELECT b.codedName AS bandCodedName, cr.bf_ibp, cr.ranking_position, cr.trending_level 
                                        FROM BandsHype AS cr 
                                        LEFT JOIN Bands AS b ON cr.bandId = b.id""", connection)

# Read history of rankings
rankings = pd.read_sql_query("""SELECT b.codedName AS bandCodedName, rs.bf_ibp, rs.ranking_position, rs.trending_level, rs.createdAt 
                                FROM BandsHypeHis AS rs
                                LEFT JOIN Bands AS b ON rs.bandId = b.id""", connection)


"""
PLOT WITH ALL TWEETS
"""

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

hours_plot = 24

# get recent tweets (last 24h)
recent_all_tweets = all_tweets[ all_tweets['createdAt'] > (datetime.now() - timedelta(hours=hours_plot))]
recent_band_tweets = band_tweets[ band_tweets['createdAt'] > (datetime.now() - timedelta(hours=hours_plot))]

# plot last day of tweets & band_tweets
ax2 = fig.add_subplot(212)
ax2 = recent_all_tweets.resample('H').count()['tweetId'].plot(kind='bar', color=sns.xkcd_rgb['sky'], label='All', ax=ax2)
recent_band_tweets.resample('H').count()['bandId'].plot(kind='bar', color=sns.xkcd_rgb['green'], label='Bands', ax=ax2)
ax2.set_xlabel("Last {}h".format(hours_plot))
ax2.set_xticklabels([])
ax2.set_ylabel("Tweets")
ax2.legend()

# store in file
fig = ax2.get_figure()
if production == 0:
    fig.savefig("tweets.png")
else:
    fig.savefig("/home/ebonada/python/hyper/server/public/images/tweets.png")


"""
PLOT WITH RANKING EVOLUTION (BF_IBP)
"""

hours_plot = 24

# filter last N-hours
rankings['createdAt'] = pd.to_datetime(rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
recent_rankings = rankings[ rankings['createdAt'] > (datetime.now() - timedelta(hours=hours_plot))]

# get top-10 bands
top_10 = current_ranking.sort_values('bf_ibp', ascending = False)['bandCodedName'][0:10]

# plot band evolution
bands = top_10 #['arcadefire', '!!!', 'frankocean']
ax3 = plt.figure().add_subplot(111)
for b in bands:
    recent_rankings[recent_rankings['bandCodedName'] == b].set_index('createdAt').plot(y='bf_ibp', label=b, ax=ax3)
ax3.set_title('Evolution of bf_ibp')
ax3.set_ylabel('bf_ibp')
ax3.set_xlabel('Last {}h'.format(hours_plot))
ax3.set_xticklabels([])
plt.gcf().subplots_adjust(bottom=0.15)
ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5)

# store in file
fig = ax3.get_figure()
if production == 0:
    fig.savefig("ranking_bfibp.png")
else:
    fig.savefig("/home/ebonada/python/hyper/server/public/images/ranking_bfibp.png")

"""
PLOT WITH RANKING EVOLUTION (POSITION)
"""

hours_plot = 24

# filter last N-hours
rankings['createdAt'] = pd.to_datetime(rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
recent_rankings = rankings[ rankings['createdAt'] > (datetime.now() - timedelta(hours=hours_plot))]

# get top-10 bands
top_10 = current_ranking.sort_values('ranking_position', ascending = True)['bandCodedName'][0:10]

# plot band evolution
bands = top_10
ax4 = plt.figure().add_subplot(111)
for b in bands:
    recent_rankings[recent_rankings['bandCodedName'] == b].set_index('createdAt').plot(y='ranking_position', label=b, ax=ax4)
ax4.set_title('RANKING POSITION of TOP RANKED BANDS')
ax4.set_ylabel('Ranking Position')
ax4.set_yticks([1,2,3,4,5,6,7,8,9,10])
ax4.set_xlabel('Last {} hours'.format(hours_plot))
ax4.set_xticklabels([])
plt.gcf().subplots_adjust(bottom=0.15)
ax4.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=5)
ax4.invert_yaxis()

# store in file
fig = ax4.get_figure()
if production == 0:
    fig.savefig("ranking_position.png")
else:
    fig.savefig("/home/ebonada/python/hyper/server/public/images/ranking_position.png")

"""
TRENDING LEVEL of TOP TRENDING BANDS
"""

hours_plot = 2

# filter last N-hours
rankings['createdAt'] = pd.to_datetime(rankings['createdAt'], format ='%a %b %d %H:%M:%S +0000 %Y')
recent_rankings = rankings[rankings['createdAt'] > (datetime.now() - timedelta(hours=hours_plot))]

# get top-10 bands
top_10 = current_ranking.sort_values('trending_level', ascending = False)['bandCodedName'][0:5]

# plot band evolution
bands = top_10
ax5 = plt.figure().add_subplot(111)
for b in bands:
    recent_rankings[recent_rankings['bandCodedName'] == b].set_index('createdAt').plot(y='trending_level', label=b, ax=ax5)
ax5.set_title('TRENDING LEVEL of TOP TRENDING BANDS')
ax5.set_ylabel('Trending Level')
ax5.set_xlabel('Last {} hours'.format(hours_plot))
ax5.set_xticklabels([])
plt.gcf().subplots_adjust(bottom=0.15)
ax5.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=5)

# store in file
fig = ax5.get_figure()
if production == 0:
    fig.savefig("trending.png")
else:
    fig.savefig("/home/ebonada/python/hyper/server/public/images/trending.png")
