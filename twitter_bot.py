import os
import json
import pprint
from openai import OpenAI
import tweepy
import schedule
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OpenAI credentials and parameters
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")
PROMPT = os.getenv("PROMPT", "Summarize the following tweets.")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

# Bot configuration
SEARCH_TOPICS = [topic.strip() for topic in os.getenv("SEARCH_TOPICS", "").split(",")]
KEY_INFLUENCERS = [influencer.strip() for influencer in os.getenv("KEY_INFLUENCERS", "").split(",")]
MY_TWITTER_NAME = os.getenv("MY_TWITTER_NAME")
SCHEDULED_TWEETS_PER_DAY = int(os.getenv("SCHEDULED_TWEETS_PER_DAY", 1))
TWITTER_ACCOUNT_CONTEXT = os.getenv("TWITTER_ACCOUNT_CONTEXT")

openai_client = OpenAI(
    base_url=f"{BASE_URL}",

    # required but ignored if not using OpenAI API
    api_key=f"{OPENAI_API_KEY}",
)

# auth = tweepy.OAuth2BearerHandler(TWITTER_BEARER_TOKEN)
# api = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        bearer_token=TWITTER_BEARER_TOKEN,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

def fetch_tweets_for_topics(topics, count=10):
    """
    Fetch popular tweets for each topic in 'topics'
    and return a list of tweet texts.
    """
    all_tweets = []

    for topic in topics:
        print("\n##################\ntopic: ", topic)
        # Construct the query to include the topic and filter for English language
        query = f"{topic} lang:en -is:retweet is:verified"
        try:
            response = client.search_recent_tweets(
                query=query,
                tweet_fields=['author_id', 'context_annotations', 'created_at', 'lang', 'text'],
                expansions=['author_id'],
                user_fields=['username', 'name', 'public_metrics'],
                max_results=100            
                )
            
            tweets = response.data
            #print("tweets: ", tweets)

            users = {user['id']: user for user in response.includes['users']}
            if tweets:
                # Create a list of users with their followers_count
                user_list = []
                for tweet in tweets:
                    user = users.get(tweet.author_id)
                    if user:
                        followers_count = user['public_metrics']['followers_count']
                        user_info = {
                            'username': user['username'],
                            'name': user['name'],
                            'timestamp': tweet.created_at,
                            'followers_count': followers_count,
                            'tweet_text': tweet.text
                        }
                        user_list.append(user_info)
                
                # Sort the user list by followers_count in descending order
                sorted_users = sorted(user_list, key=lambda x: x['followers_count'], reverse=True)
                
                # Print sorted users
                for i in range(5):
                    all_tweets.append(sorted_users[i])

                #for user_info in sorted_users:
                    #print(f"User: {user_info['username']} ({user_info['name']})")
                    #print(f"Followers: {user_info['followers_count']}")
                    #print(f"Tweet: {user_info['tweet_text']}\n")

            else:
                print("No tweets found for this topic.")



        except Exception as e:
            print(f"Error fetching tweets for topic '{topic}': {e}")
    print("all tweets:\n", all_tweets)
    return all_tweets

def fetch_tweets_for_one_influencer(influencer, count=10, start_time=None):

    all_tweets = []
    if start_time is None:
        start_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec='milliseconds')

    try:
        response = client.get_user(username=influencer)
        if response.data:
            print(f"User ID for {influencer} is {response.data.id}")
            try:
                query = f"from:{influencer} lang:en -is:retweet"
                response = client.search_recent_tweets(
                    query=query, 
                    tweet_fields=['created_at', 'text'],
                    start_time=start_time,
                    max_results=10
                    )
                tweets = response.data
                if tweets:
                    for tweet in tweets:
                        print(f"- {tweet.created_at}: {tweet.text}")
                        user_info = {
                            'username': influencer,
                            'timestamp': tweet.created_at,
                            'tweet_text': tweet.text
                        }
                        all_tweets.append(user_info)
                    return all_tweets
                else:
                    print("No tweets found for this influencer.")
            except tweepy.TweepyException as e:
                print(f"An error occurred while fetching tweets for {influencer}: {e}")

        else:
            print(f"User {influencer} not found.")

    except Exception as e:
        print(f"Error fetching tweets for {influencer}: {e}")

def fetch_tweets_for_influencers(influencers, count=10, start_time=None):

    all_tweets = []
    if start_time is None:
        start_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec='milliseconds')

    for influencer in influencers:
        print("\n##################\nusername: ", influencer)
        try:
            response = client.get_user(username=influencer)
            if response.data:
                print(f"User ID for {influencer} is {response.data.id}")
                try:
                    query = f"from:{influencer} lang:en -is:retweet is:verified"
                    response = client.search_recent_tweets(
                        query=query, 
                        tweet_fields=['created_at', 'text'],
                        start_time=start_time,
                        max_results=10
                        )
                

                    tweets = response.data
                    if tweets:
                        for tweet in tweets:
                            print(f"- {tweet.created_at}: {tweet.text}")
                            user_info = {
                                'username': influencer,
                                'timestamp': tweet.created_at,
                                'tweet_text': tweet.text
                            }
                            all_tweets.append(user_info)
                    else:
                        print("No recent tweets found.")
                except tweepy.TweepyException as e:
                    print(f"An error occurred while fetching tweets for {influencer}: {e}")

            else:
                print(f"User {influencer} not found.")

        except Exception as e:
            print(f"Error fetching user id for user '{influencer}': {e}")

    print("all influencer tweets:\n", pprint.pformat(all_tweets))
    return all_tweets

def summarize_tweets(tweets):
    """
    Use OpenAI to summarize the collected tweets.
    """
    if not tweets:
        return "No tweets to summarize."

    # Combine all tweets into a single text block
    #combined_text = "\n\n".join(tweets)

    # Prepare the messages for OpenAI ChatCompletion (for GPT-3.5-turbo or similar)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{PROMPT}\n\n{tweets}"}
    ]

    try:
        response = openai_client.chat.completions.create(
            messages=messages,
            max_tokens=4000,
            temperature=0.1,
            model=MODEL,
        )


        # Extract the assistant's reply
        summary = response.choices[0].message.content

        print("Summary:\n", summary)

        return summary
    except Exception as e:
        print(f"Error summarizing tweets: {e}")
        return "Error summarizing tweets."

def ask_llm(user_input, system_prompt, previous_output=None):

    # Combine all tweets into a single text block
    #combined_text = "\n\n".join(tweets)

    # Prepare the messages for OpenAI ChatCompletion (for GPT-3.5-turbo or similar)
    # messages = [
    #     {"role": "system", "content": system_prompt},
    #     {"role": "user", "content": f"{user_input}\nPREVIOUS OUTPUT: {previous_output}"}
    # ]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]    

    try:
        response = openai_client.chat.completions.create(
            messages=messages,
            max_tokens=4000,
            temperature=0.1,
            model=MODEL,
        )


        # Extract the assistant's reply
        next_version = response.choices[0].message.content

        # print("system prompt:\n", system_prompt)
        # print("user input:\n", user_input)
        # print("previous output:\n", previous_output)
        print("Messages: \n")
        print(messages)
        print("###")
        print("Next Version:\n")
        print(next_version)
        print("###################\n")

        return next_version
    except Exception as e:
        print(f"Error using LLM: {e}")
        return "Error using LLM."

def create_and_post_summary():
    """
    Main function that collects tweets, summarizes them, 
    and posts them to Twitter.
    """
    # 1. Fetch tweets for each topic
    topic_tweets = fetch_tweets_for_topics(SEARCH_TOPICS, count=10)
    
    # 2. Fetch tweets for key influencers
    influencer_tweets = fetch_tweets_for_influencers(KEY_INFLUENCERS, count=10)
    
    # 3. Combine all fetched tweets
    all_tweets = topic_tweets + influencer_tweets

    start_time = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec='milliseconds')
    start_time_compare = start_time.replace('+00:00', 'Z')
    # HARD CODE FOR MY TWITTER ACCOUNT SINCE IT WAS CREATED RECENTLY
    creation_time_str = '2025-01-17T00:34Z'
    time_format = '%Y-%m-%dT%H:%MZ'
    creation_time_dt = datetime.strptime(creation_time_str, time_format).replace(tzinfo=timezone.utc)
    start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if start_time_dt < creation_time_dt:
        # If the current start_time is too early, we update it to the creation_time
        # but still keep the final format as trailing 'Z' + milliseconds.
        new_start_time_str = creation_time_dt.isoformat(timespec='milliseconds')  # e.g. "2025-01-17T00:24:00.000+00:00"
        new_start_time_str = new_start_time_str.replace('+00:00', 'Z')           # e.g. "2025-01-17T00:24:00.000Z"
        start_time = new_start_time_str

    my_tweets = fetch_tweets_for_one_influencer(MY_TWITTER_NAME, count=10, start_time=start_time)

    # Start the event loop
    with open('prompts.json', 'r') as file:
        prompts = json.load(file)  # Load the JSON content into the 'tools' variable
        num_prompts = len(prompts)
        print("Number of imported prompts: ", num_prompts)  

    all_tweets_formatted = ""
    print("ALL TWEETS:\n")
    for tweet in all_tweets:
        print(f"-- {tweet['timestamp']}: - Twitter User {tweet['username']} - Tweet: {tweet['tweet_text']}")
        all_tweets_formatted += f"-- {tweet['timestamp']}: - Twitter User {tweet['username']} - Tweet: {tweet['tweet_text']}\n"

    my_tweets_formatted = ""
    print("MY TWEETS:\n")
    for tweet in my_tweets:
        print(f"-- {tweet['timestamp']} - Twitter User {tweet['username']} - Tweet: {tweet['tweet_text']}")
        my_tweets_formatted += f"-- {tweet['timestamp']} - Twitter User {tweet['username']} - Tweet: {tweet['tweet_text']}\n"

    #previous_output = all_tweets
    # for i in range(num_prompts):
    #     system_prompt = f"{prompts[i]['system_prompt']}\n\nMY_TWEET_HISTORY:\n{my_tweets_formatted}\nEND OF MY_TWEET_HISTORY"
    #     user_input = prompts[i]['user_prompt']
    #     previous_output = ask_llm(user_input, system_prompt, previous_output)

    system_prompt = f"""Pick the most important tweet from the list of tweets in TWEETS.  Important as in most influential to ai and defi.
    ONLY respond with the picked tweet's username and verbatim/exact tweet text.  
    NO OTHER TEXT OR CONTENT.  NO SUMMARIES!  EXAMPLE OUTPUT: Username: @elonmusk Tweet: AI is the most influential technology in the world.END OF EXAMPLE OUTPUT"""
    output = ask_llm(user_input=f"TWEETS:\n{all_tweets_formatted}", system_prompt=system_prompt)


    system_prompt = f"""Write one new less than 270 character tweet about the tweet provided as IMPORTANT_TWEET (not from MY_TWEET_HISTORY).  QUOTE THE IMPORTANT_TWEET AND IT'S REFERENCES.
    Explain how Torus can POTENTIALLY be used for, be influenced by or to influence the topics in the tweets.
    Do NOT include content from MY_TWEET_HISTORY, it is there so you do not repeat content already posted.
    MY_TWEET_HISTORY:
    {my_tweets_formatted}
    END OF MY_TWEET_HISTORY
    """
    output = ask_llm(user_input=f"IMPORTANT_TWEET:\n{output}", system_prompt=system_prompt)

    system_prompt = f"""ONLY respond with the ONE tweet from the OUTPUT given.  NO OTHER TEXT OR CONTENT AT ALL in your output."""
    output = ask_llm(user_input=f"OUTPUT:\n{output}", system_prompt=system_prompt)
     
    tweet = output

    while len(tweet) > 280:
            print("Tweet is too long. Truncating...")
            messages = [
                {"role": "system", "content": "You summarize or rephrase text to less than 280 characters.  Your ONLY output should be the same tweet text but shortened to slightly less than 280 characters."},
                {"role": "user", "content": f"{tweet}"}
            ]
            response = openai_client.chat.completions.create(
                messages=messages,
                max_tokens=500,
                temperature=0.1,
                model=MODEL,
            )
            tweet = response.choices[0].message.content
            print("New summary:\n", tweet)

    print("Tweet:\n", tweet)

    # 5. Post to Twitter (only if summary is not an error)
    if tweet and "Error" not in tweet:
        try: 
            tweet = tweet.strip('"')
        except:
            pass

        try:
            # Post the tweet
            response = client.create_tweet(text=tweet)
            print(f"[{datetime.now()}] Posted tweet:\n{tweet}\n")
        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")

def schedule_tweets_per_day():
    """
    Schedule 'create_and_post_summary()' calls throughout the day 
    based on SCHEDULED_TWEETS_PER_DAY.
    """

    # We can do something simple like schedule equally spaced times.
    # For example, if SCHEDULED_TWEETS_PER_DAY=2, we run at e.g. 10:00 and 16:00
    # This is just an example; adapt as you see fit.
    
    # If we want to space them evenly across 24 hours:
    interval = 24 / SCHEDULED_TWEETS_PER_DAY  # hours between posts

    # Clear any existing schedule
    schedule.clear()
    
    # For each post slot, schedule a job
    for i in range(SCHEDULED_TWEETS_PER_DAY):
        post_time = i * interval
        hour = int(post_time)
        minute = int((post_time - hour) * 60)
        
        # A simple daily job at a specific hour:minute
        schedule_time = f"{hour:02d}:{minute:02d}"
        schedule.every().day.at(schedule_time).do(create_and_post_summary)

def main():  

    # initial post:
    create_and_post_summary()

    # Set up the daily schedule based on SCHEDULED_TWEETS_PER_DAY
    schedule_tweets_per_day()

    print("Twitter bot is running. Waiting for scheduled tasks...")

    # Keep the script running to catch scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds

if __name__ == "__main__":
    main()
