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
				aurora = tempest.roles['aurora']['obj']
				if tempest.member_role in member.roles and aurora not in member.roles:
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

	activity = SlashCommandGroup('activity', 'Manage member activity', checks=[tempest.access(3).predicate])

	@activity.command(description="Edit a member's contribution record")
	@option('ign', description='**CASE SENSITIVE!** Search for the member by their IGN.', autocomplete=db.autocomplete_ign)
	@option('points', description="Provide the member's **CURRENT** weekly contribution score.  Mi-a will do the rest for you")
	async def edit(self, ctx, ign: str, points: int):
		data = db.get_member_by_ign(ign)
		if not data:
			await ctx.respond(f"Unable to find member by the name of `{ign}`.  They may not exist in the database.\n> Hint: Tower of Fantasy IGNs are case-sensitive.", ephemeral=True)
		else:
			print('ACTIVITY EDI1T:', ctx.author.display_name, 'adding contribution to', ign, ':', points)
			member = tempest.server.get_member(data[1])
			db.set_contribution(member, points)
			await ctx.respond(f"{ign}'s contributions have been recorded.", ephemeral=True)

	@activity.command(description="View a members activity record")
	@option('user', description='Search the activity of a member by their Discord.')
	@option('ign', description='CASE SENSITIVE!  Search by TOF username.', autocomplete=db.autocomplete_ign)
	async def view(self, ctx, user:discord.Member=None, ign: str=None):
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
		aurora = tempest.server.get_role(1008641018826067968)
		officers = [officer for officer in officer_role.members]
		members = [member for member in tempest.server.members if aurora not in member.roles and tempest.member_role in member.roles and not tempest.has_access(member, 3)]
		division  = len(members) // len(officers)
		remainder = len(members) % len(officers)
		random.shuffle(members)
		index = 0
		officer_dict = dict()
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
		await ctx.respond('jumpled officersssss')


	async def almost_reset(self):
		today = time.datetime.now()
		reset = tempest.get_daily_reset()
		before = reset - time.timedelta(hours=1)
		print(before, reset)
		if before <= today > reset:
			return True
		return False

	async def remind_officers(self):
		await tempest.botdev.send('Task test.')

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
		all_members = db.cur.execute('SELECT memberid FROM members ORDER BY key').fetchall()
		if len(all_members):
			for id in all_members:
				await asyncio.sleep(1)
				member = tempest.server.get_member(id)
				total = db.totals_by_period(member, current_period[0])
				if total < tempest.min_contribution:
					yield member, total

	async def period_report(self):
		period_settings = current_period
		start = tempest.get_day(period_settings[1])
		end   = tempest.get_day(period_settings[2])
		member_list = []
		ign_list = []
		totals = []
		for member, total in self.activity_checks():
			data = db.get_member(member)
			member_list.append(member.mention)
			totals.append(total)
			ign_list.append(data[2])

		if len(member_list):
			embed = discord.Embed(
				title='Active-Period Report',
				description=f'*Below are a list of members who did not make the activity requirements this period.*\nStart: <t:{int(start.timestamp())}:D>\nEnd: <t:{int(end.timestamp())}:D>')
			embed.add_field(name='Discord', value='\n'.join(member_list))
			embed.add_field(name='ToF name', value='\n'.join(ign_list))
			embed.add_field(name='Contribution', value='\n'.join(totals))
			await tempest.officer.send(embed=embed)

	@activity.command()
	@tempest.access(3)
	async def report(self, ctx):
		await self.period_report()


	@tasks.loop(hours=1.0)
	async def main(self):
		print('| [PERIOD] validating period')
		if not await self.validate_period():
			await tempest.botdev.send('A new activity period has begun.')
		global current_period
		current_period = db.fetch_current_period()
		if await self.almost_reset():
			await self.remind_officers()

	@main.before_loop
	async def before_main(self):
		print('hello')
		await self.bot.wait_until_ready()
		await tempest.wait_until_ready()
		print('Tempest and Bot ready.')
		global current_period
		current_period = db.fetch_current_period()
		await self.wait_until_hour()
		if await self.almost_reset():
			await self.remind_officers()
		# when the hour is fresh



def setup(bot):
	bot.add_cog(Activity(bot))