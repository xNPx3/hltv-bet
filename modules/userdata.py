import discord
import json
import asyncio
import datetime


def new_user(member, guild_id: int):
    users = load_users(guild_id)

    if str(member.id) not in users:
        users[str(member.id)] = {}
        users[str(member.id)]['name'] = member.name
        users[str(member.id)]['points'] = 1000
        users[str(member.id)]['daily'] = 1
        users[str(member.id)]['last'] = datetime.datetime(2020, 8, 3)

        dump_users(users, guild_id)


def load_users(guild_id: int):
    try:
        with open(f'data/{str(guild_id)}.json', 'r') as f:
            return json.load(f)
    except:
        with open(f'data/{str(guild_id)}.json', 'a+') as f:
            f.write('{}')
        return load_users(guild_id)


def dump_users(users, guild_id: int):
    try:
        with open(f'data/{str(guild_id)}.json', 'w') as f:
            json.dump(users, f, indent=4, sort_keys=True, default=str)
    except:
        with open(f'data/{str(guild_id)}.json', 'a+') as f:
            f.write('{}')
        dump_users(users, guild_id)
