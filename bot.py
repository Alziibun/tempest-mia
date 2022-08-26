import tempest
import discord
import datetime as dt
from discord.ext import commands
from tempest import Database as db
from sqlite3 import Error
intents = discord.Intents.default()
"""
Intents are a new API structure introduced by Discord.
In order to receive certain information from Discord your bot must first declare its "intent" to fetch data from the Discord API.
It's probably something designed to crack down on scam bots or something but it just makes things more frustrating to move over to.
"""
intents.members  = True # this will allow the bot to request member information
intents.messages = True # This enables the bot to request things like message history and process DMs.
intents.message_content = True
intents.guilds   = True # Allows the bot to view the servers it belongs to.  "I'm not sure why this needs to be declared or enabled." - Alzii

extensions = ['activity', 'profiles']

bot = commands.Bot(command_prefix='mi-', intents=intents)

@bot.event # lines of code that start with @ in Python are "Decorators".  They're basically methods that act on the method being declared on the line after.
async def on_ready():
	# this is the on_ready event.  This method will call once the bot is fully logged in.
	print('Logged on as {0}!'.format(bot.user))
	tempest.init(bot.get_guild(942230609701511228))

@bot.event
async def on_member_join(member):
	# updates #welcomes-and-leaves when a member joins
	channel = bot.get_channel(942230610246774852) # #welcomes-and-leaves
	embed = discord.Embed(
		description = f'{member.mention} has **joined**.',
		color       = discord.Colour.from_rgb(0, 255, 0))
	embed.set_author(
		name        = member.name + "#" + member.discriminator,
		icon_url    = member.avatar.url)
	await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
	# updates #welcomes-and-leaves when a member leaves
	channel = bot.get_channel(942230610246774852) # #welcomes-and-leaves
	embed = discord.Embed(
		description = f'{member.mention} has **left**.',
		color       = discord.Colour.from_rgb(255, 0, 0))
	embed.set_author(
		name        = member.name + "#" + member.discriminator,
		icon_url    = member.display_avatar.url)
	data = db.get_member(member)
	try:
		if data[1] != 'NULL':
			embed.add_field(
				name  = "Tower of Fantasy",
				value = f"{data[1]}")
	except:
		print('No TOF name.')
	await channel.send(embed=embed)

@bot.command()
async def time(ctx):
	"""
	Shows the next daily reset, weekly reset and when the next level cap is.
	"""
	cap2, cap1 = tempest.get_next_cap()
	current_cap = tempest.get_day(cap1[0])
	next_cap = tempest.get_day(cap2[0])
	embed = discord.Embed(
		title='Tower of Fantasy clock',
		description = '*times are shown in **your timezone**.  Hover over the time to see the full date.*')
	embed.add_field(
		name  = 'Reset times',
		value = f"Daily reset: <t:{int(tempest.get_daily_reset().timestamp())}:R>\nWeekly reset: <t:{int(tempest.get_weekly_reset().timestamp())}:R>"
	)
	embed.add_field(
		name  = 'Level cap',
		value = f"As of <t:{int(current_cap.timestamp())}:R> the level cap is **{cap1[1]}**\nThe level cap will raise to **{cap2[1]}** <t:{int(next_cap.timestamp())}:R>."
	)
	await ctx.send(embed=embed)


@bot.command()
async def food(ctx):
	async with ctx.channel.typing():
		await ctx.send(file=discord.File("./videos/en_coco.mp4"))


if __name__ == "__main__":  # make sure nothing else runs this part except for this code file
	for ex in extensions:
		try:
			bot.load_extension(ex)
			print(ex, "loaded.")
		except Exception as e:
			exc = "{}: {}".format(type(e).__name__, e)
			print('Failed to load extension {}\n{}'.format(ex, exc))
	with open('key', 'r') as key:
		bot.run(key.readline())  # activates the bot using the token (DON'T SHARE THE TOKEN).

