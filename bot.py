# I don't want to mess up the code, Alzii
import sqlite3
import discord
import yaml  # external lib: pip install pyyaml
from discord.ext import commands
from sqlite3 import Error
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

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



class Tempest:
	def __init__(self):
		with open('tempest.yaml', 'r') as file:
			roles = yaml.load(file)

class Database:

	connection = None

	def __init__(self):
		cls = self.__class__
		try:  # attempt to connect to the sqlite database "database"
			cls.connection = sqlite3.connect("database.sqlite3")
			print('Connected to database.')
		except Error as e:
			print(f'Unable to connect to database. {e}')
			return # can't connect to database, skip this method.

		create_members = '''
		CREATE TABLE IF NOT EXISTS members (
			id INTEGER PRIMARY KEY,
			ign TEXT,
			officer INTEGER, 
			member BOOL NOT NULL
			);
		'''

		create_inactive = '''
		CREATE TABLE IF NOT EXISTS inactive (
		id INTEGER PRIMARY KEY,
		ti1 INTEGER NOT NULL,
		ti2 INTEGER NOT NULL
		);
		'''

		cursor = cls.connection.cursor()
		cursor.execute(create_members)
		cursor.execute(create_inactive)

		cls.connection.commit()
		# EOI

	@classmethod
	def add_member(cls, member, ign='NULL', officer='NULL'):
		query = f"""
		INSERT INTO
		   members (id, member)
		VALUES
		   ({member.id}, '{ign}');
		"""


db = None
@bot.event # lines of code that start with @ in Python are "Decorators".  They're basically methods that act on the method being declared on the line after.
async def on_ready():
	# this is the on_ready event.  This method will call once the bot is fully logged in.
	print('Logged on as {0}!'.format(bot.user))
	global db
	db = Database()


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
		bot.run(key.readline())  # activates the bot using the token (DON'T SHARE THE TOKEN).
