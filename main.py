import discord
import json
import os
import logging
import datetime
import modules.userdata as userdata
import modules.hltv as hltv
import asyncio
import math
from discord.ext import tasks, commands

with open('config.json', 'r') as fp:
    config = json.load(fp)

client = commands.Bot(command_prefix=['!'], help_command=None)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}_discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@tasks.loop(hours=12)
async def fetch_matches():
    with open(f'matches.json', 'w') as f:
        json.dump(hltv.get_matches(), f, indent=4, sort_keys=True, default=str)


@tasks.loop(hours=1)
async def _bets():
    with open('matches.json', 'r') as f:
        matches = json.load(f)

    for m, v in matches.items():  # matches
        dt = datetime.datetime.fromisoformat(f"{v['date']} {v['time']}")
        if dt.timestamp() < datetime.datetime.now().timestamp():
            res = hltv.get_results(v['link'])  # results from started games

            if res['ended']:  # if ended
                for fn in os.listdir('./bets'):  # all json files in bets folder
                    if fn.endswith('.json'):
                        with open('./bets/' + fn, 'r') as f:
                            bets = json.load(f)  # load bets file

                    guild_id = int(fn.replace('.json', ''))
                    users = userdata.load_users(guild_id)

                    if res['team1_score'] > res['team2_score']:  # team1 wins
                        try:
                            for user, bet in bets[m]['team1'].items():  # bets for team1
                                p = math.ceil(bet * v['team1_odds'])
                                users[user]['points'] += p
                                print(f'{user} got {p} points')
                        except KeyError:
                            pass
                    elif res['team1_score'] < res['team2_score']:  # team2 wins
                        try:
                            for user, bet in bets[m]['team2'].items():  # bets for team2
                                p = math.ceil(bet * v['team2_odds'])
                                users[user]['points'] += p
                                print(f'{user} got {p} points')
                        except KeyError:
                            pass
                    else:  # draw
                        try:
                            for user, bet in bets[m]['team1'].items():
                                users[user]['points'] += bet
                        except KeyError:
                            pass
                        try:
                            for user, bet in bets[m]['team2'].items():
                                users[user]['points'] += bet
                        except KeyError:
                            pass

                    userdata.dump_users(users, guild_id)

        await asyncio.sleep(2)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    _bets.start()
    await asyncio.sleep(2)
    fetch_matches.start()


@client.event
async def on_message(message):
    if message.author.bot == False:
        userdata.new_user(message.author, message.guild.id)
        await client.process_commands(message)

print("Starting...")
client.run(config['bot_token'])
