import discord
import math
import datetime as time
import tempest
from tempest import Database as db
from datetime import timedelta
from discord.ext import commands

class Activity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=['ireg'])
	async def inactive(self, ctx, name: str, days: int, *, note='None provided.'):
		if not tempest.has_access(ctx.author, 3): return print('lol')
		print(note)
		"""
		- Register the {name} to the inactivity registry for {time} days.
		- Temporarily using primitive and usually unreliable discord.py functions for now
		- Temporarily using days as a default delta unless Reya needs it to be longer than that.

		"""
		# (CASE SENSITIVE) Looks for a member with the same name or nickname.  If a discriminator is provided, looks for that user directly.
		member = ctx.guild.get_member_named(name)
		data = db.get_member(member)
		ign = data[1]
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
	async def order(self, ctx, *, name: str=""):
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
	async def add(self, ctx, name: str, value: int):
		try:
			if name.startswith('d:') or name.startswith('disc:'):
				member = ctx.guild.get_member_named(name.split(':')[1])
				data = db.get_member(member)
			elif name.startswith('t:') or name.startswith('tof:'):
				data = db.get_member_by_ign(name.split(':')[1])
				member = ctx.guild.get_member(data[0])
			else:
				data = db.get_member_by_ign(name)
				member = ctx.guild.get_member(data[0])
			if not member:
				raise TypeError
		except TypeError:
			return await ctx.send('Could not find member in database.')
		db.add_contribution(member, value)
		await ctx.send(f"{data[1]}'s contributions have been recorded.")

	@commands.command(aliases=['act'])
	@commands.guild_only()
	async def activity(self, ctx, name: str=''):
		data = db.fetch_contributions(ctx.author)
		body = ''
		for day in data:
			body += f"Day: {day[3]} | {day[2]} honor.\n"
		await ctx.send(body)

def setup(bot):
	bot.add_cog(Activity(bot))