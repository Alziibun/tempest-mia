import asyncio

import tempest
import discord
import datetime as dt
from discord.ext import tasks

from discord.ext import commands, bridge
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

extensions = ['activity', 'membership', 'dev', 'party', 'tofindex', 'selfrole']

bot = commands.Bot(command_prefix='mi-', intents=intents, debug_guilds=[942230609701511228])

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
		icon_url    = member.display_avatar.url if member.display_avatar else None)
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
		if data[2] != 'NULL':
			embed.add_field(
				name  = "Tower of Fantasy",
				value = f"{data[2]}")
	except:
		print('No TOF name.')
	await channel.send(embed=embed)

def time_embeds():
	today = dt.datetime.now()
	cap2, cap1 = tempest.get_next_cap()
	current_cap = tempest.get_day(cap1[0])
	next_cap = tempest.get_day(cap2[0])
	next_meal, meal_name = tempest.get_kitchen()
	day_name, ch_name = tempest.schedule[today.weekday()]
	embed = discord.Embed(
		title='Tower of Fantasy clock',
		description = '*times are shown in **your timezone**.  Hover over the time to see the full date.*')
	embed.add_field(
		name  = 'Reset times',
		value = f"Daily reset: <t:{int(tempest.get_daily_reset().timestamp())}:R>\nWeekly reset: <t:{int(tempest.get_weekly_reset().timestamp())}:R>"
	)
	if cap1[1] != cap2[1]:
		embed.add_field(
			name  = 'Level cap',
			value = f"As of <t:{int(current_cap.timestamp())}:R> the level cap is **{cap1[1]}**\nThe level cap will raise to **{cap2[1]}** <t:{int(next_cap.timestamp())}:R>."
		)
	else:
		embed.add_field(
			name = 'Level cap',
			value = f"As of <t:{int(current_cap.timestamp())}:R> the level cap is **{cap1[1]}**"
		)
	embed.add_field(
		name  = 'Mi-a\'s Kitchen',
		value = f"Mi-a will be serving __{meal_name}__ <t:{int(next_meal.timestamp())}:R>!",
		inline= False
	)
	void_rift = []
	frontier_clash = []
	for day, challenge in tempest.schedule:
		txt = f"**{day}**" if day is day_name else day
		match challenge:
			case "Frontier Clash":
				frontier_clash.append(txt)
			case "Void Rift":
				void_rift.append(txt)
	challenges = discord.Embed(title = 'Challenge Calendar')
	challenges.add_field(name='Void Rift', value=' // '.join(void_rift))
	challenges.add_field(name='Frontier Clash', value=' // '.join(frontier_clash))
	return [embed, challenges]

@bot.command()
@tempest.access()
async def time(ctx):
	"""
	Shows the next daily reset, weekly reset and when the next level cap is.
	"""
	await ctx.send(embed=time_embeds()[0])

@bot.command()
async def food(ctx):
	async with ctx.channel.typing():
		await ctx.send(file=discord.File("./videos/en_coco.mp4"))

def is_developer():
	async def predicate(ctx):
		if ctx.author.id in tempest.devs:
			return True
		return False
	return commands.check(predicate)

@bot.slash_command()
@is_developer()
async def load(ctx, extension):
	try:
		bot.load_extension(extension)
		await ctx.respond(f'Loaded {extension}')
	except Exception as e:
		exc = "{}: {}".format(type(e).__name__, e)
		await ctx.respond('Failed to load extension {}\n{}'.format(ex, exc))

@bot.slash_command()
@is_developer()
async def unload(ctx, extension):
	try:
		bot.unload_extension(extension)
		await ctx.respond(f"Unloaded {extension}")
	except Exception as e:
		exc = "{}: {}".format(type(e).__name__, e)
		await ctx.respond('Failed to unload extension {}\n{}'.format(ex, exc))

@bot.slash_command()
@is_developer()
async def reload(ctx, extension: str):
	try:
		bot.unload_extension(extension)
		await asyncio.sleep(1)
		bot.load_extension(extension)
		await ctx.respond(f'Reloaded {extension}.')
	except Exception as e:
		print(e)


class Help(commands.HelpCommand):
	async def send_bot_help(self, mapping):
		embed = discord.Embed(title = 'Commands')
		for cog, commands in mapping.items():
			verified_commands = await self.filter_commands(commands, sort=True)
			command_signatures = [self.get_command_signature(c) for c in verified_commands]
			if command_signatures:
				cog_name = getattr(cog, "qualified_name", "Mi-sc.")
				embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)
		channel = self.get_destination()
		await channel.send(embed=embed)
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CheckFailure):
	if isinstance(error, tempest.InsufficientAccessLevel):
		await ctx.send(error)
	else:
		raise error

time_channel = 1021750136596082738
message = 1021751047548575835
@tasks.loop(hours=1)
async def update_clock():
	update_pending = True
	while update_pending:
		try:
			await message.edit(embeds=time_embeds())
			print('Clock updated')
			update_pending = False
		except Exception as e:
			print(e)
			await asyncio.sleep(5)

@update_clock.before_loop
async def before_clock():
	await bot.wait_until_ready()
	await tempest.wait_until_ready()
	global time_channel, message
	time_channel = tempest.server.get_channel(time_channel)
	message = await time_channel.fetch_message(message)

update_clock.start()
if __name__ == "__main__":  # make sure nothing else runs this part except for this code file
	bot.help_command = Help()
	for ex in extensions:
		try:
			bot.load_extension(ex)
			print(ex, "loaded.")
		except Exception as e:
			exc = "{}: {}".format(type(e).__name__, e)
			print('Failed to load extension {}\n{}'.format(ex, exc))
	with open('key', 'r') as key:
		bot.run(key.readline())  # activates the bot using the token (DON'T SHARE THE TOKEN).

