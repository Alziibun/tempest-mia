import asyncio
import discord
import tempest
from tempest import Database as db
from discord.ext import commands


class Profile(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		if not db.con: db() # initialize if not already

	@commands.command(aliases=['p', 'pro'])
	async def profile(self, ctx, name: str=None, lookup: str='discord'):
		"""
		Shows ToF name, discord mention, guild rank and activity monitoring officer.
		"""
		# profile functions
		member = ctx.author # default if no arguments supplied
		if name:
			match lookup:
				case 't' | 'tof':
					data = db.get_member_by_ign(name)
					member = ctx.guild.get_member(data[0]) # data[0] is the member's ID
				case 'd' | 'discord':
					member = ctx.guild.get_member_named(name)
					data = db.get_member(member)
		else:
			data = db.get_member(member) # default data if no arguments applied
		""" 
		retrieve member info from database
		< Indexes : data >
		0: member ID
		1: IGN
		2: officer
		3: member BOOL
		"""
		ign = data[1]
		officer = ctx.guild.get_member(data[2])
		role = tempest.get_rank(member)['obj']
		# create the embed
		embed = discord.Embed(
			   title       = ign,
			   description = member.mention,
			   color       = role.color)
		embed.set_thumbnail(url=member.display_avatar.url)
		embed.add_field(
			   name  = 'Rank',
			   value = role.name)
		if officer:
			# if the member has a handler create a footer
			embed.set_footer(
				   text=officer.name,
				   icon_url=officer.display_avatar.url)
		await ctx.channel.send(embed=embed)

	@commands.command(aliases=['c'])
	@commands.guild_only()
	async def create(self, ctx, name: str, *, tof: str=None):
		if tempest.has_access(ctx.author, 3):
			member = ctx.guild.get_member_named(name)
			if tempest.has_access(member, 3):
				print(db.get_member(member))
			if db.get_member(member):
				db.update_ign(member, tof)
				message = await ctx.send(f"{member.name}'s IGN has been changed.")
				await message.delete(delay=5)
				await ctx.message.delete()
				return
			if not tof: return await ctx.reply(f"Tower of Fantasy IGN required. `mi-register <name> <ign>")

			db.add_member(member, tof, ismember=tempest.has_access(member, 4)) # has_access to check if the member is a guest or not
			message = await ctx.send(f"{member.display_name}'s profile has been created!")
			await message.delete(delay=5)
			await ctx.message.delete()
	@commands.command()
	@commands.guild_only()
	async def assign(self, ctx, officer: str, *, name: str):
		if tempest.has_access(ctx.author, 2):
			officer = ctx.guild.get_member_named(officer)
			member = ctx.guild.get_member(db.get_member_by_ign(name)[0])

			if member and officer:
				db.update_officer(member, officer)
				await tempest.officer.send(f"> {member.mention} was assigned to {officer.display_name}.")

	@commands.command(aliases=['delassign', 'da', 'una'])
	@commands.guild_only()
	async def unassign(self, ctx, name: str):
		if tempest.has_access(ctx.author, 2):
			member = ctx.guild.get_member_named(name)
			if not db.get_member(member):
				return await ctx.reply(f"{member.display_name}'s profile has not been created.  Use mi-register <discord name> <tof name> to register them.")
			db.update_officer(member)
			ctx.reply(f"{member.name}'s officer has been removed.")

	@commands.command(aliases=['reg'])
	@commands.guild_only()
	async def register(self, ctx, *, name):
		member = ctx.author
		if db.get_member_by_ign(name):
			reply = await ctx.reply("Your profile already exists!\nCheck it out with `mi-profile`")
			await reply.delete(delay=10)
			await ctx.message.delete(delay=10)
			return
		if db.get_member(member):
			db.update_ign(member, name)
			await ctx.message.delete()
			print(await ctx.reply("Your IGN has been updated!"))
			return
		# default operation
		db.add_member(member, name, ismember = tempest.has_access(member, 4))
		await ctx.message.delete()
		await ctx.reply("Your profile has been created!").delete(10)


class Awards(commands.Cog):
	pass

def setup(bot):
	bot.add_cog(Profile(bot))
