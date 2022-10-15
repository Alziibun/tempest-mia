import discord
import math
import datetime as time
import tempest
import asyncio
import random
from tempest import Database as db
from datetime import timedelta
from discord.commands import SlashCommandGroup
from discord.ext import tasks, commands
from discord import option

current_period = None

class RapidEditingControls(discord.ui.View):
	pass
class ContEditForm(discord.ui.Modal):
	pass

class Activity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.main.start()

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
		officer = ctx.author
		if name:
			officer = ctx.guild.get_member_named(name)
		data = db.fetch_members_by_officer(officer)
		if not data:
			await ctx.reply('Unable to locate officer ID in the database.')
		li_ign = []
		li_disc = []
		li_cont = []
		for row in data:
			member = ctx.guild.get_member(row[1])
			if member:
				if tempest.has_access(member, 4):
					li_ign.append(row[2] if row[2] is not None else 'UNKNOWN')
					li_disc.append(member.mention)
					try:
						li_cont.append(f"`{db.totals_by_period(member, current_period[0])}`")
					except:
						li_cont.append('`0`')
			else:
				pass #li_disc.append('ERROR')

		print(li_ign)
		embed = discord.Embed()
		embed.set_author(name=f"{officer.name}'s assignments", icon_url=officer.display_avatar.url)
		embed.add_field(
			name = "Tower of Fantasy",
			value = '\n'.join(li_ign)
		)
		embed.add_field(
			name = 'Contributions',
			value = '\n'.join(li_cont)
		)
		embed.add_field(
			name="Discord",
			value='\n'.join(li_disc)
		)
		await ctx.send(embed=embed)

	@staticmethod
	def igns(ctx: discord.AutocompleteContext):
		print('huh')
		dblist = db.igns
		return [name for name in dblist if ctx.value.lower() in name.lower()]

	@commands.slash_command(description="Edit a member's contribution record")
	@option('ign', description='**CASE SENSITIVE!** Search for the member by their IGN.', autocomplete=igns)
	@option('points', description="Provide the member's **CURRENT** weekly contribution score.  Mi-a will do the rest for you")
	@tempest.access(3)
	async def activity_edit(self, ctx, ign: str, points: int):
		data = db.get_member_by_ign(ign)
		if not data:
			await ctx.respond(f"Unable to find member by the name of `{ign}`.  They may not exist in the database.\n> Hint: Tower of Fantasy IGNs are case-sensitive.", ephemeral=True)
		else:
			print('ACTIVITY EDI1T:', ctx.author.display_name, 'adding contribution to', ign, ':', points)
			member = tempest.server.get_member(data[1])
			try: db.set_contribution(member, points)
			except ValueError as e:
				await ctx.respond(f"Error: `{e}`\nYou are recording for day `{tempest.get_days()}`\nThe valid recording days for this period are `{current_period[1]}-{current_period[2]}`.")
			await ctx.respond(f"{ign}'s contributions have been recorded.", ephemeral=True)

	@commands.slash_command(description="View a members activity record")
	@option('user', description='Search the activity of a member by their Discord.')
	@option('ign', description='CASE SENSITIVE!  Search by TOF username.', autocomplete=igns)
	@tempest.access(4)
	async def activity_view(self, ctx, user:discord.Member=None, ign: str=None):
		if ign and user:
			return await ctx.respond('Use either TOF ign or Discord name.  Not both.', ephemeral=True)
		elif ign:
			data = db.get_member_by_ign(ign)
			if not data:
				return await ctx.respond(f'Unable to find `{ign}` in the database.\n> Hint: ToF names are case-sensitive.')
		elif user:
			data = db.get_member(user)
			if not data:
				return await ctx.respond(f"Unable to find {user.mention}")
		else:
			data = db.get_member(ctx.author)
			if not data:
				return await ctx.respond(f"Can't find your profile.")
		member = tempest.server.get_member(data[1])
		first_day = current_period[1]
		last_day = current_period[2]
		embed = discord.Embed(title=f"{data[2]}'s activity", description=member.mention)
		conts = db.fetch_contributions(member)
		print(conts)
		values = list()
		print(first_day, last_day)
		for k, id, points, day in conts:
			print(k, id, points, day)
			if first_day <= day <= last_day:
				values.append(f"[`DAY {day}`] points: `{points}`")
		embed.add_field(name=f'Contributions (Day {first_day} - {last_day})', value='\n'.join(values))
		print(current_period)
		embed.add_field(name="Total Contribution (this period)", value=db.totals_by_period(member, current_period[0]), inline=False)
		await ctx.respond(embed=embed)

	@commands.slash_command(description='Randomize all officer assignments.')
	@tempest.access(2)
	async def jumble(self, ctx):
		officer_role = tempest.server.get_role(942230609756061777)
		officers = [officer for officer in officer_role.members]
		without_officers = []
		for data in db.con.execute("SELECT * FROM members"):
			m = tempest.server.get_member(data[1])
			o = tempest.server.get_member(data[3])
			if m and o:
				if not tempest.has_access(o, 3) and tempest.has_access(m, 4) and not tempest.has_access(m, 3):
					without_officers.append(m)
			elif m and not o:
				if tempest.has_access(m, 4) and not tempest.has_access(m, 3):
					without_officers.append(m)

		division  = len(without_officers) // len(officers)
		remainder = len(without_officers) % len(officers)
		members = without_officers
		random.shuffle(members)
		index = 0
		print('member count', len(members))
		while index < len(officers):
			for i in range(division):
				member = members.pop()
				print(member.name)
				db.update_officer(member, officers[index])
			index += 1
		else:
			if remainder > 0:
				print(remainder)
		await ctx.respond('Assignments have been jumbled and filled.')


	async def almost_reset(self):
		today = time.datetime.now()
		reset = tempest.get_daily_reset()
		reset = reset.replace(hour=4)
		if today <= reset:
			return True
		return False

	async def validate_period(self):
		data  = db.fetch_current_period()
		today = tempest.get_days()
		start = data[1]
		end   = data[2]
		print(start, today, end)
		if start <= today <= end:
			return True # the period is still valid
		else:
			next = today + tempest.active_period - 1 # today is included in the time period, subtract day by 1
			db.new_period(today, next)
			return False # a new period was started

	async def wait_until_hour(self):
		today = time.datetime.now()
		future = time.datetime(today.year, today.month, today.day, today.hour)
		future += time.timedelta(hours=1)
		diff = future - today
		print('Waiting until the next hour')
		await asyncio.sleep( diff.total_seconds() )


	async def activity_checks(self):
		print('hello')
		all_members = db.con.execute('SELECT id FROM members ORDER BY key').fetchall()
		if len(all_members):
			for id in all_members:
				member = tempest.server.get_member(id[0])
				if member and tempest.has_access(member, 4) and not tempest.has_access(member, 3):
					data = db.get_member(member)
					try:
						officer = tempest.server.get_member(data[3])
						if data[2] is None or not tempest.has_access(officer, 3): continue
						total = db.totals_by_period(member, current_period[0])
						if total < tempest.min_contribution:
							print('ACTIVITY CHECK:', member.name, total, officer.display_name)
							yield member, officer, total
					except Exception as e:
						print(e)

	async def period_report(self):
		period_settings = current_period
		start = tempest.get_day(period_settings[1])
		end   = tempest.get_day(period_settings[2])
		info = dict()
		index = 0
		async for member, officer, total in self.activity_checks():
			index += 1
			data = db.get_member(member)
			if not len(info[str(officer.id)]):
				info[str(officer.id)] = ''
			info[str(officer.id)] += f"[`{total}`] {data[2]}, {member.mention}"

		embed = discord.Embed(
			title = 'Active-Period Report',
			description='*Below are a list of members who have failed to meet activity checks.*'
		)
		for key, value in info.items():
			officer = tempest.server.get_member(int(key))
			embed.add_field(name=officer.display_name, value=value)
		print(index)
		await tempest.officer.send(embed=embed)

	@commands.slash_command()
	@tempest.access(2)
	async def report(self, ctx):
		await self.period_report()
		await ctx.response.defer()


	@tasks.loop(hours=1.0)
	async def main(self):
		print('| [PERIOD] validating period')
		if not await self.validate_period():
			await self.period_report()
		global current_period
		current_period = db.fetch_current_period()

	@main.before_loop
	async def before_main(self):
		print('hello')
		await self.bot.wait_until_ready()
		await tempest.wait_until_ready()
		print('Tempest and Bot ready.')
		global current_period
		current_period = db.fetch_current_period()
		await self.wait_until_hour()
		# when the hour is fresh



def setup(bot):
	bot.add_cog(Activity(bot))