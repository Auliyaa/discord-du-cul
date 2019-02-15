# Work with Python 3.6
import discord
import tweepy
from tweepy import Cursor

import asyncio
import datetime
import time
import argparse

# Get the next sleep period (in seconds) towards our next wakeup
def next_sleep_time_sec():
    # The hour at which the bot should trigger
    wake_hour=19

    now = time.time()

    next_wake_ts = time.mktime(datetime.date.today().timetuple())
    next_wake_ts += wake_hour*3600

    # We are beyond 19h in the current day, the next wakup will be tomorrow
    while now > next_wake_ts:
        next_wake_ts += 24*3600

    return next_wake_ts - now

# Thin wrapper around a tweeter status
class twitter_status_t():
    def __init__(self, status):
        self.status = status
        self.retweet_count = status.retweet_count

    def header(self):
        return '%s :ok_hand: | %s :blue_heart:' % (str(self.status.retweet_count), str(self.status.favorite_count))

    def body(self):
        return self.status.text

# Tweeter client connection infos & tweets retrieval
class twitter_cx_t():
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def connect(self):
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        self.client = tweepy.API(self.auth)

    def fetch_next_statuses(self):
        res=[]

        today = datetime.date.today()

        for status in Cursor(self.client.user_timeline, id=('BotDuCul')).items():
            status_age_sec = (datetime.datetime.now() - status.created_at).total_seconds()
            # Stop at anything older than 1 day
            if status_age_sec >= 24*3600:
                break
            res.append(twitter_status_t(status))

        # Only keep 5 most retweeted posts in the last day
        res.sort(key=lambda x: x.retweet_count, reverse=True)
        return res[:5]


# Parse CLI arguments
arg_parser = argparse.ArgumentParser(description='Le bot du cul :).')
arg_parser.add_argument('--twitter-consumer-key', type=str, required=True)
arg_parser.add_argument('--twitter-consumer-secret', type=str, required=True)
arg_parser.add_argument('--twitter-access-token', type=str, required=True)
arg_parser.add_argument('--twitter-access-token-secret', type=str, required=True)
arg_parser.add_argument('--discord-token', type=str, required=True)
arg_parser.add_argument('--discord-server', type=str, required=True)
arg_parser.add_argument('--discord-channel', type=str, required=True)
args = arg_parser.parse_args()

# Connect our twitter client
try:
    twitter = twitter_cx_t(args.twitter_consumer_key, args.twitter_consumer_secret, args.twitter_access_token, args.twitter_access_token_secret)
    twitter.connect()
except e:
    print('Failed to connect to the Twitter API: %s' % e)
    exit(1)

try:
    discord_client = discord.Client()
except e:
    print('Failed to connect to the Discord API: %s' % e)
    exit(1)

@discord_client.event
async def on_ready():
    global discord_client
    global twitter
    global args

    print('-- Logged in as: %s (%s)' % (discord_client.user.name, discord_client.user.id))
    while not discord_client.is_closed:
        # Find the requested text channel ID
        channel = discord.utils.get(discord_client.get_all_channels(), name=args.discord_channel, server__name=args.discord_server)

        # Build announcement message
        embed = discord.Embed(title='Discord du Cul', description='Top 5 of the day', color=0x70471b)
        embed.set_footer(text='See you tomorrow!', icon_url='https://pbs.twimg.com/profile_images/967359058071179264/s-2RcYJ__400x400.jpg')
        embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Studio_Jean_Jacques_Lequeu.jpg/220px-Studio_Jean_Jacques_Lequeu.jpg')
        message = '... And now! The Due queue Report!'
        for status in twitter.fetch_next_statuses():
            embed.add_field(name=status.body(), value=status.header(), inline=False)

        await discord_client.send_message(channel, message, embed=embed, tts=True)
        await asyncio.sleep(5)
        await discord_client.send_message(channel, ':heart: :poop:')
		
        # Wait for the next announcement
        await asyncio.sleep(next_sleep_time_sec())
		
discord_client.run(args.discord_token)
