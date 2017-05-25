SELECT * FROM Bands

DELETE FROM TweetsRaw
SELECT * FROM TweetsRaw
SELECT COUNT(*) FROM TweetsRaw
SELECT * FROM TweetsRaw WHERE processed IS NULL
SELECT * FROM TweetsRaw WHERE processed IS NOT NULL
UPDATE TweetsRaw SET processed = NULL

DELETE FROM BandTweets
SELECT * FROM BandTweets

/* select last n tweets with a band */
SELECT r.tweetText
FROM BandTweets b
LEFT JOIN TweetsRaw r ON b.tweetRawId = r.id
ORDER BY r.createdAt 
LIMIT 10 
