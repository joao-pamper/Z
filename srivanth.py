from datetime import date
from joao import check_hashtag

def compose_tweet(conn, writer_id):
    cursor = conn.cursor()

    # Generate a new unique TID (optional if auto-increment is used)
    cursor.execute("SELECT MAX(tid) FROM tweets")
    max_tid = cursor.fetchone()[0]
    new_tid = max_tid + 1 if max_tid is not None else 1

    # text = input("Compose your tweet: ")

    # ask for text of tweet and check if tweet is valid
    input_valid = False
    while not input_valid:
        text = input("Compose your tweet: \n")
        hashtags, input_valid = check_hashtag(text)

        if not input_valid:
            print("Your input has an error. \nYou might have multiple instances of the same hashtag. \nPlease try again below.")


    # Insert the tweet with the calculated TID
    store_in_tweets = """
        INSERT INTO tweets (tid, writer_id, text, tdate, ttime, replyto_tid)
        VALUES (?, ?, ?, date('now'), time('now'), NULL)
    """
    cursor.execute(store_in_tweets, (new_tid, writer_id, text))

    # # Extract hashtags and insert into hashtag_mentions
    # for word in text.split():
    #     if word.startswith('#'):
    #         # Remove '#' from the hashtag
    #         hashtag_term = word[1:]
    #         cursor.execute(
    #             "INSERT INTO hashtag_mentions (tid, term) VALUES (?, ?)",
    #             (new_tid, hashtag_term)
    #         )

    # insert hashtags into hashtags table
    if len(hashtags) > 0:
        for hashtag in hashtags:
            cursor.execute(
                'INSERT INTO hashtag_mentions VALUES ( ?, ?);',
                (new_tid, hashtag),
            )

    conn.commit()
    print(f"Tweet posted successfully with TweetID {new_tid}!")

