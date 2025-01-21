import sqlite3


def reply_tweet(usr, replyto_tid, conn):
    """
    Will allow the user to reply to a tweet while doing error checking.
    """
    c = conn.cursor()

    # get user input
    input_valid = False
    while not input_valid:
        text = input("Enter your reply here: \n")
        hashtags, input_valid = check_hashtag(text)

        if not input_valid:
            print("Your input has an error. \nYou might have multiple instances of the same hashtag. \nPlease try again below.")

    # get details
    tid = get_tweets_id(c)

    c.execute(
    '''INSERT INTO tweets VALUES (?, ?, ?, date('now'), time('now'), ?);''',
    (tid, usr, text, replyto_tid),
    )
    
    # insert hashtags into hashtags table
    if len(hashtags) > 0:
        for hashtag in hashtags:
            c.execute('INSERT INTO hashtag_mentions VALUES ( ?, ?);',
            (tid, hashtag),
            )

    conn.commit()
    print("Your reply has been posted successfully!")
    
def check_hashtag(text):
    """
    Checks if input text has hashtag and returns list with hashtags specified and bool if input is valid.
    return-> hashtags: [str], valid: bool
    """
    hashtags = []
    valid = True
    text_list = text.split()
    for word in text_list:
        if word[0] == '#' and len(word) > 1:
            word = word.lower()
            if word in hashtags:
                valid = False
            hashtags.append(word)

    return hashtags, valid

def get_tweets_id(c):
    """
    Gets the id of the new tweet to be created
    return: (int) id
    """
    # gets the current maximum user ID
    c.execute("SELECT COALESCE(MAX(tid), 1) FROM tweets;") # returns 1 if table is empty
    max_id = c.fetchone()[0]
    return max_id + 1


def retweet_tweet(usr, tid, writer_id, conn):
    """
    Will retweet specified tweet for the specified user.
    """
    c = conn.cursor()
    spam_flag = 0

    #check if user has already retweeted the tweet
    c.execute(
        'SELECT COALESCE(COUNT(tid), 0)FROM retweets WHERE tid = ? AND retweeter_id = ?;',
        (tid, usr)
    )
    result = c.fetchone()
    if result[0]  > 0:
        print("You already have retweeted this tweet")
        return
    else:
        c.execute(
        '''INSERT INTO retweets VALUES (?, ?, ?, ?, date('now'));''',
        ( tid, usr, writer_id, spam_flag),
        )
        conn.commit()
        print("Your retweet has been posted successfully!")

def list_followers(usr, conn):
    """
    List all followers of a user with an option to select user and see his profile.
    """
    print("\n--------------------------------------------------")
    print("-----------------Your Followers-------------------\n")
    
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    #select all followers of the user.
    c.execute(
        'SELECT u.usr as uid, u.name as uname FROM follows f LEFT JOIN users u ON u.usr = f.flwer WHERE f.flwee = ?;',
        (usr,),
    )
    flwers = c.fetchall()
    
    # if user has no followers
    if len(flwers) == 0:
        print("\nYou have no followers.")
        print("Redirecting you to the menu.")
        conn.row_factory = None
        return
    
    #iterate through all followers
    i = 0
    while i < len(flwers):
        print(f"{i+1}. {flwers[i]['uname']}")

        # when at the 5th follower show them more options
        if ((i + 1) % 5) == 0:
            print("\nSelect from the following options." )
            valid_choice = False
            
            while not valid_choice:
                choice = input("1. See more followers \n2. Select a follower and see more details.\n3. Return to menu.\n-> ")

                if choice == '1':
                    valid_choice = True
                    print("\nDisplaying more followers...\n")

                elif choice == '2':
                    valid_choice = True
                    i = len(flwers) + 10
                    selected_u = input("Please input the number of the desired follower:\n-> ")
                    selected_uid = flwers[selected_u]["uid"]
                    see_profile(usr, selected_uid, conn)

                elif choice == '3':
                    conn.row_factory = None
                    return
                else:
                    print("Your input is invalid. PLease try again and input 1, 2 or 3 as a response.")
        
        i += 1
    
    
    # if user has followers but aready showed all of them
    if i == len(flwers):
        print("\nThere are no more followers to show.")
        print("Select from the following options:")
        valid_choice = False
        
        # loop to ask for user input
        while not valid_choice:
            choice = input("1. Select a follower and see more details.\n2. Return to menu.\n-> ")   
            if choice == '1':
                valid_choice = True
                i = len(flwers) + 10
                input_valid = False
                while not input_valid:
                    selected_u = input("Please input the number of the desired follower:\n-> ")
                    try:
                        selected_u = int(selected_u)-1
                        input_valid = True
                    except ValueError:
                        print("Your input is invalid. Please try again and only input the number of the desired follower.\n")
                    
                selected_uid = flwers[selected_u]["uid"]
                see_profile(usr, selected_uid, conn)

            elif choice == '2':
                conn.row_factory = None
                return
            else:
                print("Your input is invalid. PLease try again and input 1 or 2 as a response.")


def see_profile(usr: int, profile_usr: int, conn):
    """
    Will show profile of desired user and have an option for usr to follow
    or see more tweets from this profile.
    """
    c = conn.cursor()
    # selecting stats of the user
    c.execute(
    '''
    SELECT 
        u.name AS name, 
        COUNT(DISTINCT t.tid) AS tweets, 
        COUNT(DISTINCT f1.flwer) AS followers, 
        COUNT(DISTINCT f2.flwee) AS following 
    FROM 
        users u
    LEFT JOIN 
        tweets t ON u.usr = t.writer_id 
    LEFT JOIN 
        follows f1 ON u.usr = f1.flwee 
    LEFT JOIN 
        follows f2 ON u.usr = f2.flwer 
    WHERE 
        u.usr = ?
    GROUP BY 
        u.usr;
    ''',
    (profile_usr,)
)
    stats = c.fetchone()
    
    #show stats
    if stats is not None:
        print(f"\nName: {stats[0]}")
        print(f"tweets: {stats[1]}, followers: {stats[2]}, following: {stats[3]}")
    else:
        print("Couldn't find stats of desired user or user doesn'y exist.")
        return
    
    # get tweets of user
    c.execute(
        'SELECT t.tid, t.text, t.replyto_tid, t.tdate, t.ttime FROM tweets t WHERE writer_id = ? ORDER BY t.tdate, t.ttime DESC;',
        (profile_usr,)
    )
    tweets = c.fetchall()
    
    # if user has no tweets
    if 0 == len(tweets):
        print("This person has no tweets to show :(")
        print("Select from the following options.")
        valid_choice = False
        while not valid_choice:
            choice = input("1. Follow user \n2. Back to menu\n-> ")
            if choice == '1':
                valid_choice = True
                follow_user(usr, profile_usr, conn)
                return
            elif choice == '2': 
                return
            else:
                print("Your input is invalid. Please try again and input 1 or 2 as a response.")
    
    # iterate through tweets
    i = 0
    while i < len(tweets):
        #print text of tweet showing if it is a tweet or a reply
        if tweets[i][2] == None:
            tweet_or_reply = 'Tweet'
        else:
            tweet_or_reply = 'Reply'
        print(f"{tweet_or_reply}: {tweets[i][1]} || {tweets[i][3]} at {tweets[i][4]}")

        # at the third tweet shown, show options for the user
        if ((i + 1) % 3) == 0:
            print("\nSelect from the following options." )
            valid_choice = False
            
            while not valid_choice:
                choice = input("1. See more tweets \n2. Follow user\n3. Exit to menu.")
                
                if choice == '1':
                    valid_choice = True
                    print("Displaying more tweets...")

                elif choice == '2':
                    valid_choice = True
                    i = len(tweets) + 10
                    follow_user(usr, profile_usr, conn)
                elif choice == '3': 
                    return
                else:
                    print("Your input is invalid. PLease try again and input 1 or 2 as a response.")
        i += 1

    # if showed all tweets to the user
    if i ==  len(tweets):
        print("\nThis person has no more tweets to show :(")
        print("Select from the following options.")
        valid_choice = False
        while not valid_choice:
                choice = input("1. Follow user \n2. Back to menu\n->")
                if choice == '1':
                    valid_choice = True
                    follow_user(usr, profile_usr, conn)
                elif choice == '2': 
                    return
                else:
                    print("Your input is invalid. Please try again and input 1 or 2 as a response.")


def follow_user(flwer, flwee, conn):
    """
    Will attempt to follow user. Returns False is user already follows.
    return: bool
    """
    c = conn.cursor()

    c.execute(
        '''
        SELECT COALESCE(COUNT(u.usr), 0) as follows
        FROM users u 
        LEFT JOIN follows f ON u.usr = f.flwer
        WHERE u.usr = ? AND f.flwee = ?;
        ''',
        (flwer, flwee),
    )
    follows = c.fetchone()
    
    # already follows
    if follows[0] > 0:
        print("You already follow this user.")
        return False
    
    # doesn't follow yet
    else: 
        
        c.execute(
            '''INSERT INTO follows VALUES (?, ?, date('now'));''',
            (flwer, flwee),
        )
        conn.commit()
        print(f"You succesfully followed user with id {flwee}.")
        return True