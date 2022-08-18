import discord
from discord.ext import commands

class Inactivity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.guild_only()
	async def inactive(self, user: str):
		print(user)


def setup(bot):
	bot.add_cog(Inactivity(bot))