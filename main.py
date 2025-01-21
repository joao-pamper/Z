import sqlite3
import sys
import getpass
import os
import platform
from joao import list_followers, see_profile
from srivanth import compose_tweet
from juan import search_tweets

def clear_screen():
    """
    clears the screen before program begins
    """
    system_name = platform.system().lower()
    if system_name == 'windows':
        os.system('cls')
    else:
        os.system('clear')

def connect(db):
    """
    connects to sql database
    """
    try:
       connection = sqlite3.connect(db)
       connection.execute("PRAGMA foreign_keys = ON;")
       return connection
    except sqlite3.Error as error_msg:
       print(f"Error connecting to database: {error_msg}")
       sys.exit(1)

def first_screen():
   """
   Welcome page for Z
   Asks users to exit, sign up, or log in
   return: (str) command choice
   """
   print("--------------------------------------------------")
   print("------------------Welcome to Z--------------------")
   print("--------------------------------------------------")
   print("Select any of the following options:")
   while True:
       print("0) Exit")
       print("1) Log in")
       print("2) Sign up")
       command = input("Enter your choice: ")
       if command in ['0','1','2']:
           break
       else:
           print("\nInvalid entry, please try again")
  
   return command


def log_in(connection):
    """
    Log in page for Z
    Asks users for valid username and password
    return: (str) the name of the user
    """
    print("\nPlease log in by providing the following...")

    # Asks users for valid username
    while True:
        username = input("Username: ")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE usr=?;", (username,))
        valid = cursor.fetchone()
        if not valid:
            print("Invalid Username. Try again.")
        else:
            break
    
    # Asks users for valid password
    while True:
        password = getpass.getpass("Password: ")
        cursor.execute("SELECT * FROM users WHERE pwd=? AND usr LIKE ?;", (password, username))
        valid = cursor.fetchone()
        if not valid:
            print("Invalid Password. Try again.")
        else:
            return valid[0], valid[1] # id, name

def get_email():
    """
    repeatedly prompts user for a valid email
    return: (str) email
    """
    while True:
        email = input("Email: ")
        try:
            user_part, domain_part = email.split('@')
            domain_one, domain_two = domain_part.split('.')
        except ValueError:
            print("Ensure your email contains an '@' and a '.'")
            continue

        if len(user_part) < 1:
            print("Ivalid email format: The username is missing")
            continue
        if len(domain_one) < 1:
            print("Ivalid email format: The mail server is missing")
            continue
        if len(domain_two) < 1:
            print("Ivalid email format: The domain is missing")
            continue
        return email

def get_phone_num():
    """
    repeatedly prompts user for a valid phone number
    return: (int) users phone number
    """
    while True:
        phone_num = input("Phone Number: ")

        # removes all non numerical characters
        phone_digits = ''.join(filter(str.isdigit, phone_num))
        if len(phone_digits) < 1:
            print("Please ensure you type in your phone number as an integer or sets of integers.\nExample: 111 111 1111")
        else:
            return int(phone_digits)


def sign_up(connection):
    """
    prompts users for information to create an account
    return: (str) the name of the user
    """
    print("\nTo create an account, please provide Z with the following...")
    name = input("Name: ")
    email = get_email()
    phone_num = get_phone_num()
    password = getpass.getpass("Password: ")
    id = get_id(connection) # gets the new and unique user id (int)
    cursor = connection.cursor()

    try:
        # Insert the new user with the generated unique ID
        cursor.execute("INSERT INTO users (usr, name, email, phone, pwd) VALUES (?, ?, ?, ?, ?)",
        (id, name, email, phone_num, password))
        connection.commit()
        print(f"\nWelcome {name}!")
        print("You have succesfully created an account with Z!")
        print(f"Your username is: {id}\n")
    except sqlite3.IntegrityError as error_msg:
        print(f"Error: {error_msg}")

    return id, name

def get_id(connection):
        """
        gets the id of the new user to be created
        return: (int) id
        """
        cursor = connection.cursor()

        # gets the current maximum user ID
        cursor.execute("SELECT COALESCE(MAX(usr), 0) FROM users") # returns 0 if table is empty
        max_id = cursor.fetchone()[0]
        return max_id + 1

def print_menu(name):
    """
    prints the programs 'Main Menu'
    contains a list of 'tasks' users are able to perform
    return: (str) users requested command
    """
    print("\n--------------------------------------------------")
    print(f"------------------Main Menu----------------------")
    print("--------------------------------------------------")
    print(f"Hi {name}! Select any of the following options:")
    
    # repeatedly prompts user for a valid task
    while True:
        print("0) Log out")
        print("1) Search for tweets")
        print("2) Search for users")
        print("3) Compose a tweet")
        print("4) List followers")
        command = input("Enter your choice: ")
        if command in ['0','1','2','3','4',]:
            return command
        else:
            print("\nInvalid choice. Please try again")

def timeline(id, connection):
    offset = 0
    limit = 5
    print("\n--------------------------------------------------")
    print(f"---------------------TimeLine---------------------")
    print("--------------------------------------------------")
    while True:
        # searches and displays users
        tl_tweets = search_tl_tweets(connection, offset, id)
        prompt_more = display_tl_tweets(tl_tweets, offset)

        # prompts user to display more z users if necessary
        if prompt_more:
            show_more = input("\nType 'm' to show more results.\nType anything else for Main Menu.\n").lower()
            if show_more != 'm':
                break
            offset = offset + limit
        else:
            break

def display_tl_tweets(tl_tweets, offset):
    prompt_more = False
    if not tl_tweets: # list of users is empty
        if offset == 0:
            print("\nNo results found")
        else:
            print("\nNo more results found")
    else:
        prompt_more = True
        for row in tl_tweets:
            tweet_id, writer_id, content, date, time, retweeter_id = row
            if retweeter_id:
                print(f"TID: {tweet_id}| User {retweeter_id} retweeted: {content} | {date} {time}")
            else:
                print(f"TID: {tweet_id}| User {writer_id} tweeted: {content} | {date} {time}")
        
    if len(tl_tweets) < 5 and len(tl_tweets) >= 1:
        print("\nEnd of results.")
        prompt_more = False

    return prompt_more

def search_tl_tweets(conn, offset, user_id):
    cursor = conn.cursor()
    query = """
    SELECT 
        t.tid AS tweet_id,
        t.writer_id AS user_id,
        t.text AS content,
        t.tdate AS date,
        t.ttime AS time,
        NULL AS retweeter_id
    FROM tweets t
    JOIN follows f ON t.writer_id = f.flwee
    WHERE f.flwer = ?

    UNION ALL

    SELECT 
        t.tid AS tweet_id,
        t.writer_id AS user_id,
        t.text AS content,          
        r.rdate AS date,
        t.ttime AS time,
        r.retweeter_id
    FROM retweets r
    JOIN tweets t ON r.tid = t.tid  
    JOIN follows f ON r.retweeter_id = f.flwee
    WHERE f.flwer = ?

    GROUP BY tweet_id, date, retweeter_id
    ORDER BY date DESC, time DESC
    LIMIT 5 OFFSET ?;
    """
    cursor.execute(query, (user_id, user_id, offset))
    results = cursor.fetchall()
    return results

def user_search_main(log_in_id, connection):
    """
    Prompts user requests for different search user functions
    return: NA
    """
    # prompts key word
    keyword = input("\nEnter a keyword: ")
    limit = 5 # max number of users to be displayed
    offset = 0 # starting "index"

    # searches and displays z users based on commands
    while True:
        # searches and displays users
        users = search_users(connection, keyword, offset)
        prompt_more = display_users(users, offset)

        # prompts user to display more z users if necessary
        if prompt_more:
            show_more = input("\nType 'm' to show more results.\nOtherwise, type anyhting else.\n").lower()
            if show_more != 'm':
                break
            offset = offset + limit
        else:
            break

    # requests user if they would like to see users profile.
    while True:
        info_id = input("To see info about a user, type their user id.\nOtherwise, type 'q' to quit.\n").lower()
        if info_id == 'q':
            return
        elif info_id.isdigit():
            valid = validate_user(info_id, connection)
            if valid:
                see_profile(log_in_id, info_id, connection)
                return
            else: 
                print("Your input is invalid. Please choose a valid option from the following:")
        else:
            print("Your input is invalid. Please choose a valid option from the following:")

def validate_user(usr_id: str, conn):
    """
    Validates if user exists in database.
    """
    c = conn.cursor()
    usr_id = int(usr_id)
    c.execute('SELECT usr FROM users WHERE usr = ?;',
              (usr_id,))
    result = c.fetchone()
    if result is not None:
        return True
    else:
        return False

def display_users(users, offset):
    if not users: # list of users is empty
            if offset == 0:
                print("\nNo results found")
            else:
                print("\nNo more results found")
    else:
        for user in users:
            print(f"User ID: {user[0]}, Name: {user[1]}")
        prompt_more = True
        
    if len(users) < 5:
        print("End of results.\n")
        prompt_more = False

    return prompt_more


def search_users(conn, keyword, offset):
    cursor = conn.cursor()

    # SQL query to search users by keyword in name
    query = """
    SELECT usr, name FROM users
    WHERE name LIKE ?
    ORDER BY LENGTH(name) ASC
    LIMIT 5 OFFSET ?
    """
    cursor.execute(query, (f"%{keyword}%", offset))
    results = cursor.fetchall()
    
    return results
      
def main():
    # clears screen to initiate program
    clear_screen()

    # ensures db file is provided
    if len(sys.argv) != 2:
        print("Program will exit. Please provide the database filename as an argument")
        sys.exit(1)

    # retieves db file from command line
    db_file = sys.argv[1]

    # connects to sql database
    connection = connect(db_file)

    # prompt users to sign up or log in
    first_command = first_screen()

    # prompts login or sign up if user did not request to exit program
    if first_command != '0':
        prompt_login = True

    counter = 1 # to only show the timeline after first login 

    # prompts login or signup and/or menu upon users request
    while first_command != '0':
        #prompts login or signup
        while prompt_login:
            if first_command == '1': # user asks to login
                id, name = log_in(connection)
                counter = 1
            if first_command == '2': # users asks to sign up
                id, name = sign_up(connection)
            prompt_login = False


        if first_command == '1' and counter < 2:
            timeline(id, connection)
            counter = counter + 1

        # prints the menu
        command = print_menu(name)

        if command == '0':
            # user is logged out and taken back to home page
            print("\nYou have been logged out.")
            print("You will be returned to the home page.\n")
            prompt_login = True
            first_command = first_screen()
            
        elif command == '1': # users asks to search tweets
            search_tweets(connection, id)
        elif command == '2': # users asks to search users
            user_search_main(id, connection)
        elif command == '3': # users asks to make a tweet
            compose_tweet(connection, id)
        elif command == '4': # users asks to list his followers
            list_followers(id, connection)

    # closes connection and ends program
    connection.commit()
    connection.close
    print("\nThanks for using 'Z'!\n")


if __name__ == "__main__":
   main()

