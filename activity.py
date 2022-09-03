import discord
import math
import datetime as time
import tempest
import asyncio
from tempest import Database as db
from datetime import timedelta
from discord.ext import tasks, commands

class Activity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.logging_reminder.start()

	@commands.command(aliases=['ireg'])
	@tempest.access(3)
	async def inactive(self, ctx, name: str, days: int, *, note='None provided.'):
		"""
		Write an inactivity note.
		"""
		"""
		- Register the {name} to the inactivity registry for {time} days.
		- Temporarily using primitive and usually unreliable discord.py functions for now
		- Temporarily using days as a default delta unless Reya needs it to be longer than that.
		"""
		# (CASE SENSITIVE) Looks for a member with the same name or nickname.  If a discriminator is provided, looks for that user directly.
		member = ctx.guild.get_member_named(name)
		data = db.get_member(member)
		ign = data[2]
		period = time.datetime.now() + timedelta(days=days)
		embed = discord.Embed(
			title 		= ign,
			description = member.mention) # TOF name assignments TBA
		embed.add_field(
			name  = 'Expected Return Time',
			value = f"<t:{math.floor(period.timestamp())}:R>",
			inline= False)
		embed.add_field(
			name  = "Note",
			value = f"*{note}*") # note adding TBA
		embed.set_thumbnail(url=member.avatar.url)
		embed.set_footer(
			text     = ctx.author.display_name,
			icon_url = ctx.author.avatar.url)
		channel = ctx.guild.get_channel(1008223604170825788)
		await channel.send(embed=embed)

	@commands.command(aliases=['o'])
	@tempest.access(3)
	async def order(self, ctx, *, name: str=""):
		"""
		Displays all members handled by the officer.
		"""
		member = ctx.author
		if name:
			member = ctx.guild.get_member_named(name)
		print(member)
		data = db.fetch_members_by_officer(member)
		if not data:
			await ctx.reply('Unable to locate officer ID in the database.')
		li_ign = []
		li_disc = []
		for row in data:
			try:
				li_ign.append(row[1])
			except Exception as e:
				print(e)
				li_ign.append('ERROR')

		for row in data:
			try:
				li_disc.append(ctx.guild.get_member(row[0]).mention)
			except Exception as e:
				print(e)
				li_disc.append('ERROR')
		embed = discord.Embed(
			title = f"{member.name}'s assignments"
		)
		embed.set_thumbnail(url=member.display_avatar.url)
		embed.add_field(
			name = "Discord",
			value = '\n'.join(li_disc)
		)
		embed.add_field(
			name = "Tower of Fantasy",
			value = '\n'.join(li_ign)
		)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.guild_only()
	@tempest.access(3)
	async def add(self, ctx, name: str, value: int):
		try:
			member, data = tempest.parse_name(name)
		except TypeError:
			return await ctx.send('Could not find member in database.')
		except Exception as e:
			print(e)
		db.add_contribution(member, value)
		await ctx.send(f"{data[1]}'s contributions have been recorded.")

	@commands.command(aliases=['act'])
	@commands.guild_only()
	@tempest.access(3)
	async def activity(self, ctx, name: str=''):
		member, data = tempest.parse_name(name)
		data = db.fetch_contributions()
		body = ''
		for day in data:
			body += f"Day: {day[3]} | {day[2]} honor.\n"
		await ctx.send(body)

	async def almost_reset(self):
		today = time.datetime.now()
		reset = tempest.get_daily_reset()
		before = reset - time.timedelta(hours=1)
		if before <= today > reset:
			return True
		return False

	async def remind_officers(self):
		await tempest.botdev.send('Task test.')
		pass

	@tasks.loop(hours=1.0)
	async def logging_reminder(self):
		if await self.almost_reset():
			await self.remind_officers()
		print('hour passed')

	@logging_reminder.before_loop
	async def wait_until_hour(self):
		print('awaiting bot')
		await self.bot.wait_until_ready()
		print('bot ready')
		today = time.datetime.now()
		future = time.datetime(today.year, today.month, today.day, today.hour)
		future += time.timedelta(hours=1)
		diff = future-today
		print(f'{diff.total_seconds()} seconds until new hour to begin reminder.')
		await tempest.wait_until_ready()
		await asyncio.sleep( diff.total_seconds() )
		if await self.almost_reset():
			await self.remind_officers()
		# when the hour is fresh




def setup(bot):
	bot.add_cog(Activity(bot))