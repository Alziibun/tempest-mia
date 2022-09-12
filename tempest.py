import sqlite3
import discord
import yaml
import datetime as dt
import asyncio
from enum import Enum
from discord.ext import commands
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

server = None
roles = dict()

# chats
officer = 942230610246774851
admin   = 942230610246774849
council = 942230610246774846
notes   = 1008223604170825788
botdev  = 1008346539879563314
apps    = 1017353554693992448
mem_log = 1017566996604391424

member_role = 1008632049558634496
visitor_role = 942230609739251734

accolades = [
	"Leveling",
	"Bygone Phantasm",
	"Wormhole",
	"Contribution"
]

devs = [90893355029921792]

active_period = 0
min_contribution = 0

level_caps = [
	( 1, 18),
	( 2, 24),
	( 3, 27),
	( 4, 30),
	( 5, 33),
	( 6, 36),
	( 7, 38),
	( 8, 40),
	( 9, 42),
	(11, 44),
	(13, 46),
	(15, 48),
	(17, 50),
	(19, 52),
	(21, 54),
	(23, 56),
	(25, 58),
	(27, 60),
	(29, 61),
	(31, 62),
	(34, 63),
	(37, 64),
	(40, 65),
	(43, 66),
	(46, 67),
	(49, 68),
	(52, 69),
	(56, 70),
	# veras
	(65, 72),
	(74, 74),
	(83, 76),
	(92, 78),
	(101, 80)
]

tof_epoch = dt.datetime(2022, 8, 10, hour=5)
tof_week_epoch = dt.datetime(2022, 8, 15, hour=5)
schedule = [
	("Monday", "**Void Rift** day 1"),
	("Tuesday", "**Frontier Clash** day 1"),
	("Wednesday", "**Void Rift** day 2"),
	("Thursday", "**Frontier day** 2"),
	("Friday", "**Void Rift** day 3"),
	("Saturday", "**Frontier Clash** day 3"),
	("Sunday", "*Nothing new today!  Time to relax~*")
]
kitchen = [
	( 5, 'Breakfast'),
	(12, 'Lunch'),
	(18, 'Dinner')
]
def init(guild: discord.Guild):
	print(f'Initiating {guild.name} as Tempest server.')
	global server, roles, officer, admin, council, notes, botdev, TANK, HEALER, DPS, apps, mem_log
	server = guild
	officer = server.get_channel(officer)
	admin = server.get_channel(admin)
	council = server.get_channel(council)
	notes = server.get_channel(notes)
	botdev = server.get_channel(botdev)
	apps = server.get_channel(apps)
	mem_log = server.get_channel(mem_log)
	global member_role, visitor_role
	member_role = server.get_role(member_role)
	visitor_role = server.get_role(visitor_role)
	with open('tempest.yaml', 'r') as file:
		data = yaml.load(file, Loader=Loader)
		_roles = data['roles']
		_act = data['activity']
		global min_contribution, active_period
		active_period = _act['period']
		min_contribution = _act['minimum']
		for k, v in _roles.items():
			roles[k] = {
				'av'  : v['access'],
				'obj' : guild.get_role(v['id'])
				}
		del data
async def wait_until_ready():
	while server is None:
		await asyncio.sleep(1)

class errors:
	DOUBLE_NAME_INPUT = "Please use either IGN or user, not both!"
	IGN_NaN = "Couldn't find someone by that name!\n> *ToF IGNs are case-sensitive.*"
	MEMBER_NaN = "This user is not in the database."

def get_roles():
	# return roles as a list
	if not len(roles): return print('Sever uninitialized.  Unable to get roles.')
	return [i['obj'] for i in roles.values()]

def get_rank(member: discord.Member):
	# find the guild rank of a discord member
	if not len(roles): return print('Server uninitialized. Unable to get roles.')
	for role in roles.values():
		if role['obj'] in member.roles:
			return role

def has_access(member: discord.Member, req):
	# check if the member has the required av for the command
	return True if get_rank(member)['av'] <= req else False

class InsufficientAccessLevel(commands.CheckFailure):
	pass

def access(level=255):
	# checks version of has_access()
	async def predicate(ctx):
		ranks = []
		for role in roles.values():
			if role['av'] <= level:
				ranks.append(role['obj'].name)
		if len(ranks) > 1:
			ac_string = ', '.join(ranks[:-1])
			ac_string += ' and ' + ranks[-1]
		else:
			ac_string = ranks[0]
		if has_access(ctx.author, level):
			return True
		else:
			raise InsufficientAccessLevel(f"This command is only available for {ac_string}.")
	return commands.check(predicate)

def get_weeks():
	since_weekly_epoch = dt.datetime.now() - tof_week_epoch
	return since_weekly_epoch.day // 7

def get_days():
	# get the amount of days since the game released accounting for reset time
	now = dt.datetime.now()
	since_epoch = now - tof_epoch
	days = since_epoch.days
	reset = get_daily_reset()
	print(now.hour, days, reset.day, now.day is reset.day)
	if now.hour < 5 and now.day is reset.day:
		days -= 1
	return days + 1 # +1 prevents day 0 from existing

def get_day(day=1):
	# get the day of the server as a timedelta
	offset = tof_epoch + dt.timedelta(days = day-1)
	if day > 0:
		return offset.replace(hour=5, minute=0, second=0, microsecond=0)
	return offset

def get_daily_reset():
	today = dt.datetime.now()
	reset = dt.datetime(today.year, today.month, today.day)
	if today.hour >= 5:
		reset = reset + dt.timedelta(days=1)
	reset = reset.replace(hour=5, minute=0, second=0, microsecond=0)
	return reset

def get_weekly_reset():
	today = dt.datetime.now()
	diff = 7 -  today.weekday()
	reset = today.replace(hour=5, minute=0, second=0, microsecond=0) + dt.timedelta(days = diff)
	return reset

def get_next_cap():
	today = get_days()
	cap = level_caps[-1]
	current = level_caps[-1]
	caplist = iter(level_caps)
	last_cap = next(caplist)
	print('Today is', today)
	while today < level_caps[-1][0]:
		next_cap = next(caplist)
		print(last_cap[0], next_cap[0]-1)
		if today in [day for day in range(last_cap[0], next_cap[0])]:
			cap = next_cap
			current = last_cap
			break
		last_cap = next_cap
	return cap, current

def get_kitchen():
	today = dt.datetime.now()
	hour = today.hour
	print(hour)
	_schedule = iter(kitchen)
	prev_time = next(_schedule)
	while kitchen[0][0] < hour < kitchen[-1][0]:
		next_time = next(_schedule)
		pass
		print(prev_time[0], next_time[0])
		if hour in [t for t in range(prev_time[0], next_time[0])]:
			event = next_time[1]
			now = today.replace(hour=next_time[0], minute=0, second=0, microsecond=0)
			break
		prev_time = next_time
	else:
		event = kitchen[0][1]
		now = get_daily_reset().replace(hour=kitchen[0][0], minute=0, second=0, microsecond=0)

	return now, event
def parse_name(name):
	db = Database
	try:
		if name.startswith('d:') or name.startswith('disc:'):
			member = server.get_member_named(name.split(':')[1])
			data = db.get_member(member)
		elif name.startswith('t:') or name.startswith('tof:'):
			print(name.split(':'))
			data = db.get_member_by_ign(name.split(':')[1])
			member = server.get_member(data[0])
		else:
			data = db.get_member_by_ign(name)
			member = server.get_member(data[0])
		if not member:
			raise Exception('Database', f"{name} not found.")
	except TypeError as t:
		raise TypeError(t)
	return member, data

async def promote(member):
	ranks = [role['obj'] for name, role in roles.items()]
	member_rank = get_rank(member)['obj']
	rank_index = ranks.index(member_rank)
	if rank_index > 1:
		if visitor_role in member.roles:
			await member.remove_roles(visitor_role, reason='Promotion to member')
			await member.add_roles(member_role, ranks[-2], reason='Promotion to member')
			Database.set_join_date(member, get_days())
			print('Promoted')
		else:
			await member.remove_roles(member_rank, reason=f'Promotion to {ranks[rank_index-1].name}')
			await member.add_roles(ranks[rank_index-1], reason=f'Promotion to {ranks[rank_index-1].name}')
			print('Promoted')

async def demote(member):
	rank = get_rank(member)['obj']
	if mem_role in member.roles:
		await member.remove_roles(rank, mem_role, reason='Demotion to visitor')
		await member.add_roles(visitor_role, reason='Demotion to visitor')
		print('Reduced to visitor.')


class Database:
	con = None
	cur = None
	def __init__(self):
		cls = self.__class__
		try:  # attempt to connect to the sqlite database "database"
			cls.con = sqlite3.connect("database.sqlite3")
			cls.cur = cls.con.cursor()
			print('Connected to database.')
		except Error as e:
			print(f'Unable to connect to database. {e}')
		# END OF INITIALIZATION

	@classmethod
	def commit(cls, *query):
		for q in query:
			cls.cur.execute(q)
		cls.con.commit()

	@classmethod
	def add_member(cls, member: discord.Member=0, ign='NULL', officer=0):
		if member:
			id = member.id
		else:
			id = 0
		query = f"""
		INSERT INTO
		   members (id, ign, officer)
		VALUES
		   ({id}, '{ign}', {officer});
		"""
		
		cls.commit(query)
		print(f'Added {member.name} to database.')

	@classmethod
	def set_join_date(cls, member: discord.Member, date: int=None):
		if date is None:
			date = get_days()
		query = f"""
		UPDATE members
		SET join_time = {date}
		WHERE id = {member.id}
		"""
		cls.commit(query)


	@classmethod
	def add_inactive(cls, member: discord.Member, ti1, ti2):
		
		query = f"""
		INSERT INTO
			members (id, ti1, ti2)
		VALUES
			({member.id}, {ti1}, {ti2})
		"""

		cls.commit(query)
		print(f'Inactivity registered to database.')

	@classmethod
	def add_accolade(cls, member: discord.Member, accolade: int):
		query = f"""
		INSERT INTO
			members (id,
		"""

	@classmethod
	def get_member(cls, member: discord.Member):
		# returns a Tuple from the members database relevant to the {member}
		try:
			return cls.cur.execute(f'SELECT * FROM members WHERE id={member.id}').fetchone()
		except:
			return print('Unable to find', member.name, 'in database.')

	@classmethod
	def get_member_by_ign(cls, tof: str):
		# returns a Tuple from the members database using a member's TOF IGN
		try:
			return cls.cur.execute(f"SELECT * FROM members WHERE ign='{tof}'").fetchone()
		except:
			return print('Unable to find Tower of Fantasy username:', tof, 'in database.')

	@classmethod
	def update_officer(cls, member: discord.Member, officer: discord.Member=0):
		query = f"""
		UPDATE members
		SET officer = {officer.id}
		WHERE id = {member.id}
		"""
		cls.commit(query)
		print('Updated entry for', member.name)

	@classmethod
	def update_ign(cls, member: discord.Member, ign: str):
		query = f"""
		UPDATE members
		SET ign = '{ign}'
		WHERE id = {member.id}
		"""
		print(query)
		cls.commit(query)
		print('Updated ign for', member.name)

	@classmethod
	def set_contribution(cls, member: discord.Member, value: int):
		# check if contribution exists for today
		today = get_days()
		result = cls.cur.execute(f"SELECT * FROM contributions WHERE memberid = {member.id} ORDER BY day").fetchall()
		recent_day = 0
		total = 0
		day1, dayx = cls.this_week()
		print(day1, dayx)
		for key, id, points, day in result:
			print(day, get_days())
			recent_day = day
			if day1 <= get_day(day) < dayx and day != today:
				# total up all points from the week earlier
				total += points
		diff = value - total
		if diff < 0:
			print(diff)
			raise ValueError('Members cannot gain negative contribution.')

		result = cls.cur.execute(f"SELECT * FROM contributions WHERE memberid = {member.id} ORDER BY day").fetchall()
		relative = []
		if len(result):
			relative = [row[1] for row in result]
			print(today==recent_day, today, recent_day)
		if member.id in relative and today == recent_day:
			query = f"""
			UPDATE contributions
			SET points = {diff}
			WHERE day = {today}
			"""
			print('Updating contributions')
		else:
			query = f"""
			INSERT INTO
				contributions (memberid, points, day)
			VALUES
				({member.id}, {diff}, {today})
			"""
			print('Adding contribution')
		cls.commit(query)

	@classmethod
	def fetch_current_period(cls):
		return cls.cur.execute("SELECT * FROM periods WHERE id = (SELECT MAX(id) FROM periods)").fetchone()
	@classmethod
	def new_period(cls, day1, day2):
		# create a new activity period
		result = cls.fetch_current_period()
		if day1 > result[0]:
			query = f"""
			INSERT INTO
				periods (first_day, last_day)
			VALUES
				({day1}, {day2})
			"""
			cls.commit(query)
	@classmethod
	def this_week(cls):
		today = dt.datetime.now()
		offset = get_days() - today.weekday()
		real = get_day(day=offset)
		return real, get_weekly_reset()

	@classmethod
	def totals_by_period(cls, member: discord.Member, period_id):
		sel = cls.cur.execute(f"SELECT first_day, last_day FROM periods WHERE id={period_id}").fetchone()
		conts = cls.cur.execute(f'SELECT * FROM contributions WHERE memberid={member.id} ORDER BY day').fetchall()
		total = 0
		for key, id, points, day in conts:
			if sel[0] <= day <= sel[1]:
				total += points
		print('Totaled', total)
		return total

	@classmethod
	def fetch_application(cls, member: discord.Member):
		return cls.cur.execute(f'SELECT * FROM apps WHERE member_id={member.id}').fetchone()

	@classmethod
	def new_application(cls, member: discord.Member, ign: str):
		query = f"""
		INSERT INTO apps
			(member_id, ign)
		VALUES
			({member.id}, '{ign}')
		"""
		cls.commit(query)
		app = cls.fetch_application(member)
		return app[0] # application ID

	@classmethod
	def set_app_message(cls, app_id, message: discord.Message):
		query = f"""
		UPDATE apps
		SET message_id = {message.id}
		WHERE app_id = {app_id}
		"""
		cls.commit(query)

	@classmethod
	def delete_application(cls, member: discord.Member):
		query = f"""
		DELETE FROM apps
		WHERE member_id = {member.id}
		"""
		cls.commit(query)

	#     FETCHING

	@classmethod
	def fetch_all_applications(cls):
		return cls.cur.execute('SELECT * FROM apps').fetchall()

	@classmethod
	def fetch_contributions(cls, member: discord.Member):
		result = cls.cur.execute(f"SELECT * FROM contributions WHERE memberid={member.id} ORDER BY day").fetchall()
		return result

	@classmethod
	def fetch_members_by_officer(cls, officer: discord.Member):
		# returns a list of rows (tuple) related to an officer
		try:
			return cls.cur.execute(f"SELECT * FROM members WHERE officer={officer.id}").fetchall()
		except:
			return print('Unable to locate officer by ID')


	@classmethod
	@property
	def schema(cls):
		table_names = cls.cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
		table_names = [row[0] for row in table_names]
		for table in table_names:
			pragma = cls.con.execute(f"PRAGMA table_info('{table}')").fetchall()
			yield table, pragma