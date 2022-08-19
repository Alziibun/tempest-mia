import discord
import tempest
from tempest import Database as db
from discord.ext import commands

print('from profiles.py', db)

class Profile(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		if not db.con: db() # initialize if not already

	@commands.command(aliases=['p', 'pro'])
	@commands.guild_only()
	async def profile(self, ctx, name: str=None, func: str=None, field: str=None, value=None):		
		if not name:
			member = ctx.author
		else:
			member = ctx.guild.get_member_named(name)

		data = db.get_member(member)
		print(data)

	@commands.command(aliases=['reg'])
	@commands.guild_only()
	async def register(self, ctx, name: str, tof: str=None):
		member = ctx.guild.get_member_named(name)
		print(db.get_member(member))
		if db.get_member(member):
			return await ctx.reply(f"{member.display_name} is already registered.  Please use mi-??? to edit their information.")
		if not tof: return await ctx.reply(f"Tower of Fantasy IGN required. `mi-register <name> <ign>") 

		db.add_member(member, tof, ismember=tempest.has_access(member, 4)) # has_access to check if the member is a guest or not
		await ctx.reply(f"{member.display_name}'s profile has been created!")

	@commands.command()
	@commands.guild_only()
	async def assign(self, ctx, officer: str, name: str):
		officer = ctx.guild.get_member_named(officer)







def setup(bot):
	bot.add_cog(Profile(bot))
