import asyncio
import discord
import tempest
from tempest import Database as db
from discord.ext import commands, bridge
from discord.commands import SlashCommandGroup
from discord import option


class ProfileEditor(discord.ui.Modal):
	def __init__(self, member: discord.Member, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.member = member
		data = db.get_member(member)
		ign = data[2] if data else None
		self.add_item(discord.ui.InputText(label='Tower of Fantasy IGN', min_length=2, max_length=32, required=True, value = ign))

	async def callback(self, interaction):
		ign = self.children[0].value
		if db.get_member(self.member):
			db.update_ign(self.member, ign)
		else:
			db.add_member(self.member, ign=ign)
		await interaction.response.send_message(f"`{self.member.display_name}`'s profile was updated/created.")


class Profile(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		if not db.con: db() # initialize if not already

	@commands.user_command(name='Edit Profile')
	@tempest.access(3)
	async def profile_user_edit(self, ctx, member: discord.Member):
		editor = ProfileEditor(title=f"{member.name}'s settings", member=member)
		await ctx.send_modal(editor)


	profile = SlashCommandGroup('profile', 'View/edit user profile')

	@profile.command(name='view', description='test')
	@option('ign', description='Search for a profile by ToF ign.')
	@option('user', description='Search for a profile by Discord user.')
	async def profile_view(self, ctx, ign: str=None, user: discord.Member=None):
		"""
		Shows ToF name, discord mention, guild rank and activity monitoring officer.
		"""
		data = None
		if ign and user:
			return await ctx.respond(tempest.errors.DOUBLE_NAME_INPUT)
		elif ign:
			data = db.get_member_by_ign(ign)
			if not data:
				return await ctx.respond(tempest.errors.IGN_NaN)
		elif user:
			data = db.get_member(user)
			if not data:
				return await ctx.respond(tempest.errors.MEMBER_NaN)
		else:
			data = db.get_member(ctx.author)
			user = ctx.author
		if not data:
			return await ctx.respond(tempest.errors.MEMBER_NaN)
		ign = data[2]
		officer = ctx.guild.get_member(data[3])
		role = tempest.get_rank(user)['obj']
		# create the embed
		embed = discord.Embed(
			   title       = ign,
			   description = user.mention,
			   color       = role.color)
		embed.set_thumbnail(url=user.display_avatar.url)
		embed.add_field(
			   name  = 'Rank',
			   value = role.name)
		if officer:
			# if the member has a handler create a footer
			embed.set_footer(
				   text=officer.name,
				   icon_url=officer.display_avatar.url)
		await ctx.respond(embed=embed)

	@profile.command(name='edit', description="Edit profile variables for a member.")
	@option('user', description="Edit a discord user's profile")
	async def profile_edit(self, ctx, user: discord.Member=None):
		"""
		Creates a profile for a member associating their ToF username.
		"""

		member = user if user else ctx.author
		if member is ctx.author or tempest.has_access(ctx.author, 3):
			editor = ProfileEditor(title=f"{member.name}'s settings", member=member)
			await ctx.send_modal(editor)
		else:
			ctx.respond('You may only edit your own profile.', ephemeral=True)


	@commands.slash_command(description='Assign an officer to a member.')
	@tempest.access(2)
	@option('officer', description='The officer to be assigned.')
	@option('name', description='The IGN of the member.')
	async def assign(self, ctx, officer: discord.Member, *, name: str):
		member = ctx.guild.get_member(db.get_member_by_ign(name)[0])
		if member:
			db.update_officer(member, officer)
			await tempest.officer.send(f"> {member.mention} was assigned to {officer.display_name}.")
		else:
			await ctx.respond('Unable to find a member by that IGN.  It\'s possible they have not been registered on the database.', ephemeral=True)


	@commands.command(aliases=['delassign', 'da', 'una'])
	@commands.guild_only()
	@tempest.access(2)
	async def unassign(self, ctx, name: str):
		member = ctx.guild.get_member_named(name)
		if not db.get_member(member):
			return await ctx.reply(f"{member.display_name}'s profile has not been created.  Use mi-register <discord name> <tof name> to register them.")
		db.update_officer(member)
		ctx.reply(f"{member.name}'s officer has been removed.")

	@commands.command(aliases=['reg'])
	@commands.guild_only()
	@tempest.access()
	async def register(self, ctx, *, name):
		"""
		Associate your Discord account with your ToF username.
		"""
		member = ctx.author
		if db.get_member_by_ign(name):
			reply = await ctx.reply("Your profile already exists!\nCheck it out with `mi-profile`")
			await reply.delete(delay=10)
			await ctx.message.delete(delay=10)
			return
		if db.get_member(member):
			db.update_ign(member, name)
			await ctx.message.delete(delay=10)
			reply = await ctx.reply("Your IGN has been updated!")
			await reply.delete(delay=10)
			return
		# default operation
		db.add_member(member, name)
		reply = await ctx.reply("Your profile has been created!")
		await ctx.message.delete(delay=10)
		await reply.delete(delay=10)


class ApplicationControls(discord.ui.View):
	def __init__(self, member_id, *args, **kwargs):
		super().__init__(timeout=None, *args, **kwargs)
		data = db.fetch_application(tempest.server.get_member(member_id))
		self.member_id = data[1]
		self.ign = data[2]
		print('View created', self.ign, self.member_id)

	@discord.ui.button(label='Accept', custom_id='accept-1', style=discord.ButtonStyle.success)
	async def button_callback(self, button, interaction):
		if interaction.message:
			await interaction.message.delete()
		member = tempest.server.get_member(self.member_id)
		db.delete_application(member)
		await tempest.promote(interaction.user, member)
		print(f"MEMBERSHIP: {member.display_name}'s application was accepted by {interaction.user.display_name}")
		await tempest.apps.send(f"✅ {member.mention}'s (**{self.ign}**) application was accepted")

class Application(discord.ui.Modal):
	def __init__(self, *args, **kwags) -> None:
		super().__init__(*args, **kwags)

		self.add_item(discord.ui.InputText(label='Tower of Fantasy name', min_length=2, max_length=32, required=True))
		self.add_item(discord.ui.InputText(label='Level', min_length=1, max_length=2, required=True))
		self.add_item(discord.ui.InputText(label='Note/Activity', max_length=200, style=discord.InputTextStyle.long, required=False))

	async def callback(self, interaction: discord.Interaction):
		ign = self.children[0].value
		level = self.children[1].value
		note = self.children[2].value
		member = interaction.user

		try:
			app_id = db.new_application(member, ign)
		except Exception as e:
			return await interaction.response.send_message(e)
		if db.get_member(member):
			db.update_ign(member, ign)
		else:
			db.add_member(member, ign)
		embed = discord.Embed(title=f"{ign}'s application", description=member.mention)
		embed.add_field(name='Level', value=level)
		if note:
			embed.add_field(name='Note', value=note)
		embed.set_thumbnail(url=member.display_avatar.url)
		view = ApplicationControls(member.id)
		message = await tempest.apps.send(embed=embed, view=view)
		db.set_app_message(app_id, message)

		body = """
		Thank you for applying to join Tempest.  Please make sure to apply to Tempest in-game!
		"""
		await interaction.response.send_message(body, ephemeral=True)

class Membership(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		if not db.con: db()

	@commands.slash_command()
	async def apply(self, ctx: discord.ApplicationContext):
		app = Application(title='Test Application')
		app_fetch = db.fetch_application(ctx.author)
		if app_fetch:
			await ctx.respond('Your application is currently being processed.', ephemeral=True)
		elif tempest.has_access(ctx.author, 4):
			await ctx.respond('You\'re already a member!', ephemeral=True)
		else:
			await ctx.send_modal(app)
		pass

	@commands.user_command(name="Promote")
	@tempest.access(2)
	async def promote_member(self, ctx, member: discord.Member):
		try:
			await tempest.promote(ctx.author, member)
		except Exception as e:
			return print(e)
		await ctx.respond(f"{member.display_name} was promoted.", ephemeral=True)

	@commands.user_command(name='Demote to Visitor')
	@tempest.access(2)
	async def demote_to_visitor(self, ctx, member: discord.Member):
		try:
			await tempest.demote(ctx.author, member)
		except Exception as e:
			return print(e)
		await ctx.respond(f"{member.display_name} was reduced to visitor.", ephemeral=True)


	@commands.Cog.listener()
	async def on_ready(self):
		print('persisting views')
		data = db.fetch_all_applications()
		for app_id, member_id, ign, message_id in data:
			try:
				self.bot.add_view(ApplicationControls(member_id), message_id=message_id)
			except AttributeError:
				print('Could not find member', ign)

class Awards(commands.Cog):
	pass

def setup(bot):
	bot.add_cog(Profile(bot))
	bot.add_cog(Membership(bot))
