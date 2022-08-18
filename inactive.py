import discord
import math
import datetime as time
from tempest import Tempest, Database
from datetime import timedelta
from discord.ext import commands

class Inactivity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.tempest = Tempest( await bot.fetch_guild(942230609701511228) )

	@commands.command(aliases=['ireg'])
	@commands.guild_only()
	async def inactive(self, ctx, name: str, days: int):
		if not self.tempest.has_access(ctx.author): return print('lol')
		"""
		- Register the {name} to the inactivity registry for {time} days.
		- Temporarily using primitive and usually unreliable discord.py functions for now
		- Temporarily using days as a default delta unless Reya needs it to be longer than that.

		"""

		# (CASE SENSITIVE) Looks for a member with the same name or nickname.  If a discriminator is provided, looks for that user directly.
		member = ctx.guild.get_member_named(name)
		period = time.datetime.now() + timedelta(days=days)
		embed = discord.Embed(
			title 		= member.name,
			description = f"Discord: {member.mention}\nToF: ???") # TOF name assignments TBA
		embed.add_field(
			name  = 'Expected Return Time',
			value = f"<t:{math.floor(period.timestamp())}:R>",
			inline= False)
		embed.add_field(
			name  = "Note",
			value = "*None*") # note adding TBA
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(
			text     = ctx.author.display_name,
			icon_url = ctx.author.avatar_url)

		channel = ctx.guild.get_channel(1008223604170825788)
		await channel.send(embed=embed)

def setup(bot):
	bot.add_cog(Inactivity(bot))