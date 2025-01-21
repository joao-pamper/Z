'''
users(usr, name, email, phone, pwd) 

follows(flwer, flwee, start_date)

lists(owner_id, lname)

include(owner_id, lname, tid)

tweets(tid, writer_id, text, tdate, ttime, replyto_tid)

retweets(tid, retweeter_id, writer_id, spam, rdate)

hashtag_mentions(tid,term)
'''

from joao import retweet_tweet, reply_tweet

def search_tweets(conn, usr):
    '''
    This function searches for tweets based on user-provided keywords (hashtags and text)
    and calls display function for viewing and interacting with results.
    '''
    keywords = input("Enter keywords: ")
    keywords = keywords.split(',')
    cursor = conn.cursor()

    #Parse input to identify hashtags and text
    hashtag_keywords = [kw for kw in keywords if kw.startswith('#')]
    text_keywords = [kw for kw in keywords if not kw.startswith('#')]
    
    queries = []

    #SQL for Hashtags
    #hashtag_mentions(tid,term)
    if hashtag_keywords:
        query = """
        SELECT t.tid, t.writer_id, t.text, t.tdate, t.ttime
        FROM tweets t
        JOIN hashtag_mentions h ON t.tid = h.tid
        WHERE LOWER(h.term) LIKE ?
        ORDER BY t.tdate DESC, t.ttime DESC
        """
        #Lowercase and trim keywords in parameter list
        hashtag_keywords = ['%' + kw.lower().strip() + '%' for kw in hashtag_keywords]
        queries.append((query, hashtag_keywords))

    #SQL for text
    #tweets(tid, writer_id, text, tdate, ttime, replyto_tid)
    if text_keywords:
        query = """
        SELECT t.tid, t.writer_id, t.text, t.tdate, t.ttime
        FROM tweets t
        WHERE """ + ' OR '.join("LOWER(t.text) LIKE ?" for _ in text_keywords) + """
        ORDER BY t.tdate DESC, t.ttime DESC
        """
        text_keywords = ['%' + kw.lower().strip() + '%' for kw in text_keywords]
        queries.append((query, text_keywords))
    
    results = []
    for query, params in queries:
        #print("Executing query:", query)
        #print("With parameters:", params)
        cursor.execute(query, params)
        results.extend(cursor.fetchall())

    # Paginate results and allow selection
    display_tweets(results, conn, cursor, usr)


def display_tweets(results, conn, cursor, usr):
    '''
    This function displays tweets as paginated results (5 tweets per page), and prompts user interaction
    to view specific tweets, view next page, or quit.
    '''
    if not results:
        print("No tweets or retweets found.")
        return
    
    results_per_page = 5
    total_results = len(results)
    current_index = 0

    while current_index < total_results:
        i = 1
        print(f"\nDisplaying tweets {current_index + 1} to {min(current_index + results_per_page, total_results)} of {total_results}:")
        for i, tweet in enumerate(results[current_index : current_index + results_per_page], start=1):
            tid, writer_id, text, tdate, ttime = tweet
            print(f"{i}. Tweet ID: {tid}, Writer ID: {writer_id}, Date: {tdate}, Time: {ttime}")
            print(f"   Text: {text}\n")
        if i == 5 and current_index + results_per_page < total_results:
            u_input = input("Enter 1-5 to select a tweet, 'n' to see next tweets, or 'q' to quit:\n")
        else: 
            u_input = input(f"Enter 1-{i} to select a tweet, or 'q' to quit.\n")

        if u_input.lower() == 'n' and i == 5:  # Next 5 tweets
            if current_index + results_per_page >= total_results:
                print("No more tweets to display.")
                break
            else:
                current_index += results_per_page

        elif u_input.lower() == 'q':  # Quit
            break

        elif u_input.isdigit() and 1 <= int(u_input) <= min(5, total_results - current_index):
            selected_index = current_index + int(u_input) - 1
            selected_tweet = results[selected_index]
            show_tweet_options(selected_tweet, conn, cursor, usr)
        else:
            print("Invalid input. Please try again.")

def show_tweet_options(tweet, conn, cursor, usr):
    '''
    This functions shows all details of a specific tweet (tweet ID, writer ID, Date, Time) as well as statistics
    including number of retweets and replies. Prompts and allows user to reply, retweet, or go back. 
    '''
    tid, writer_id, text, tdate, ttime = tweet
    print(f"\nSelected Tweet ID: {tid}, Writer ID: {writer_id}")
    print(f"Date: {tdate}, Time: {ttime}")
    print(f"Text: {text}")

    # Get tweet statistics
    retweet_count = total_retweet_count(tid, cursor)
    reply_count = total_reply_count(tid, cursor)
    print(f"Retweets: {retweet_count}, Replies: {reply_count}")

    # Options for reply or retweet
    action = input("Enter 1 to reply, 2 to retweet, or 'b' to go back:\n")
    if action == '1':
        reply_tweet(usr, tid, conn)
    elif action == '2':
        retweet_tweet(usr, tid, writer_id, conn)
    elif action.lower() == 'b':
        pass
    else:
        print("Invalid input. Returning to tweet list.")


def total_retweet_count(tid, cursor):
    '''
    This function obtains total number of retweets for a given tweet using a query.
    '''
    query = "SELECT COUNT(*) FROM retweets WHERE tid = ?"
    cursor.execute(query, (tid,))
    return cursor.fetchone()[0]


def total_reply_count(tid, cursor):
    '''
    This function obtains total number of replies for a given tweet using a query.
    '''
    query = "SELECT COUNT(*) FROM tweets WHERE replyto_tid = ?"
    cursor.execute(query, (tid,))
    return cursor.fetchone()[0]

def view_tweets(usr, cursor, conn):
    '''
    This function retrieves and displays Tweets and Retweets from users followed by the specified user (usr).
    Uses queries to combine tweets and retweets with UNION ALL and orders by descending order of date
    (new to old).

    '''
    query = """
    SELECT t.tid, t.writer_id, t.text, t.tdate, t.ttime, t.replyto_tid
    FROM tweets t
    JOIN follows f ON t.writer_id = f.flwee
    WHERE f.flwer = ?

    UNION ALL

    SELECT r.tid, r.retweeter_id AS writer_id, 'Retweet' AS text, r.rdate AS tdate, r.rtime AS ttime
    FROM retweets r
    JOIN follows f ON r.retweeter_id = f.flwee
    WHERE f.flwer = ?

    ORDER BY tdate DESC, ttime DESC
    """
    cursor.execute(query, (usr, usr))
    tweets_rtweets = cursor.fetchall()

    display_tweets(tweets_rtweets, conn, cursor, usr)
    