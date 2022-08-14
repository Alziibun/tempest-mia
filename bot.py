import discord
from discord.ext import commands

intents = discord.Intents.default()
"""
Intents are a new API structure introduced by Discord.
In order to receive certain information from Discord your bot must first declare its "intent" to fetch data from the Discord API.
It's probably something designed to crack down on scam bots or something but it just makes things more frustrating to move over to.
"""
intents.members  = True # this will allow the bot to request member information
intents.messages = True # This enables the bot to request things like message history and process DMs.
intents.guilds   = True # Allows the bot to view the servers it belongs to.  "I'm not sure why this needs to be declared or enabled." - Alzii

bot = commands.Bot(command_prefix='mi-', intents=intents)

@bot.event # lines of code that start with @ in Python are "Decorators".  They're basically methods that act on the method being declared on the line after.
async def on_ready():
	# this is the on_ready event.  This method will call once the bot is fully logged in.
	print('Logged on as {0}!'.format(bot.user))


@bot.command()
async def yo(context):

	"""
	Here's an example of a bot command with the "cogs" structure.
	----
	Using the decorator "@bot.command()" we can make a method into a bot command smoothly.

	The name of the method is the name of the command, so for example typing "mi-yo" will tell the bot to use this command.
	(Mi-) is our prefix, (yo) is the command name

	The first argument is context, which is a requirement for every command in this structure.  
	To read more: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context
	"""
	await context.reply('Hello!') # the bot will reply "Hello!"


if __name__ == "__main__":  # make sure nothing else runs this part except for this code file

	with open('key', 'r') as key:
		bot.run(key.read())  # activates the bot using the token (DON'T SHARE THE TOKEN).
