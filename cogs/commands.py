import modules.hltv as hltv
import modules.userdata as userdata
import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
import asyncio
import json
import random
from itertools import islice
from datetime import datetime, timedelta


class Help(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page)
            await destination.send(embed=emby)


class Commands(commands.Cog, name='Commands'):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = Help()
        bot.help_command.cog = self

    @commands.command()
    async def matches(self, ctx, page=0):
        msg = ""

        with open('matches.json', 'r') as f:
            matchlist = json.load(f)
        
        for m in islice(matchlist, page*10, page*10+10):
            dt = datetime.strptime(
                f"{matchlist[m]['date']} {matchlist[m]['time']}", "%Y-%m-%d %H:%M")
            msg += f"{matchlist[m]['id']} | {matchlist[m]['team1']} - {matchlist[m]['team2']} | {matchlist[m]['team1_odds']} - {matchlist[m]['team2_odds']} | {matchlist[m]['length']} | <t:{round(dt.timestamp())}>\n"

        if msg != "":
            await ctx.send(msg)
        else:
            await ctx.send("There aren't any upcoming matches right now.")

    @commands.command()
    async def bet(self, ctx, match_id: int, points: int, team: int):
        users = userdata.load_users(ctx.guild.id)

        with open('matches.json', 'r') as f:
            matchlist = json.load(f)
        if not str(match_id) in matchlist:
            await ctx.send("Invalid match ID.")
            return
        elif points < 1:
            await ctx.send("You cannot bet more than 1 points.")
            return
        elif points > users[str(ctx.author.id)]['points']:
            await ctx.send("You cannot bet more than you have.")
            return
        elif (team > 2) or (team < 1):
            await ctx.send("Please select team 1 or 2.")
            return

        def getBets(guild_id: int):
            try:
                with open(f'bets/{str(guild_id)}.json', 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                with open(f'bets/{str(guild_id)}.json', 'w') as f:
                    json.dump({}, f, indent=4, sort_keys=True, default=str)
                return getBets(guild_id)

        def setBet(bets):
            try:
                bets[str(match_id)]['team' + str(team)
                                    ][str(ctx.author.id)] = points
                users[str(ctx.author.id)]['points'] -= points
            except KeyError:
                bets[str(match_id)] = {}
                bets[str(match_id)]['team1'] = {}
                bets[str(match_id)]['team2'] = {}
                setBet(bets)

        bets = getBets(ctx.guild.id)
        setBet(bets)

        try:
            with open(f'bets/{str(ctx.guild.id)}.json', 'w') as f:
                json.dump(bets, f, indent=4, sort_keys=True, default=str)
            userdata.dump_users(users, ctx.guild.id)
        except Exception as ex:
            print(ex)

        await ctx.send("Bet saved successfully.")

    @commands.command()
    async def results(self, ctx, link):
        await ctx.send(hltv.get_results(link))

    @commands.command()
    async def daily(self, ctx):
        users = userdata.load_users(ctx.guild.id)

        points = random.randint(10, 100)
        diff = datetime.now() - \
            datetime.fromisoformat(users[str(ctx.author.id)]['last'])
        if (diff >= timedelta(hours=24)) and (diff <= timedelta(hours=48)):
            daily = users[str(ctx.author.id)]['daily'] + 1
        elif diff > timedelta(hours=48):
            daily = 1
        else:
            await ctx.send(f"Wait until <t:{int((datetime.fromisoformat(users[str(ctx.author.id)]['last']) + timedelta(hours=24)).timestamp())}>.")
            return

        users[str(ctx.author.id)]['points'] += points * daily
        users[str(ctx.author.id)]['daily'] = daily
        users[str(ctx.author.id)]['last'] = datetime.now()
        userdata.dump_users(users, ctx.guild.id)

        await ctx.send(f"You got {points * daily} points. Daily streak: {daily}")

    @commands.command()
    async def points(self, ctx):
        users = userdata.load_users(ctx.guild.id)
        p = users[str(ctx.author.id)]['points']
        await ctx.send(f"You have `{p}` points.")


def setup(bot):
    bot.add_cog(Commands(bot))
