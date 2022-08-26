import sqlite3
import discord
import yaml
import datetime as dt
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

accolades = [
	"Leveling",
	"Bygone Phantasm",
	"Wormhole",
	"Contribution"
]

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

tof_epoch = dt.datetime(2022, 8, 10, hour=20)
tof_week_epoch = dt.datetime(2022, 8, 15, hour=5)
def init(guild: discord.Guild):
	print(f'Initiating {guild.name} as Tempest server.')
	global server, roles, officer, admin, council, notes
	server = guild
	officer = server.get_channel(officer)
	admin = server.get_channel(admin)
	council = server.get_channel(council)
	notes = server.get_channel(notes)
	with open('tempest.yaml', 'r') as file:
		_roles = yaml.load(file, Loader=Loader)
		for k, v in _roles.items():
			roles[k] = {
				'av'  : v['access'],
				'obj' : guild.get_role(v['id'])
				}

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
		rank = get_rank(ctx.author)
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
	if now.hour >= 5:
		days += 1
	return days + 1

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
	diff = today.weekday() - ( today.weekday() - 6) - 1
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
		print(last_cap[0], next_cap[0])
		if today in [day for day in range(last_cap[0], next_cap[0])]:
			cap = next_cap
			current = last_cap
			break
		last_cap = next_cap
	return cap, current


def parse_name(name):
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
			raise Exception('Database', f"{name} not found.")
	except TypeError as t:
		raise TypeError(t)
	return member, data

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
	def add_member(cls, member: discord.Member, ign='NULL', officer=0, ismember: bool=False):
		query = f"""
		INSERT INTO
		   members (id, ign, officer, member)
		VALUES
		   ({member.id}, '{ign}', {officer}, {bool(ismember)});
		"""
		
		cls.commit(query)
		print(f'Added {member.name} to database.')

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
	def fetch_members_by_officer(cls, officer: discord.Member):
		# returns a list of rows (tuple) related to an officer
		try:
			return cls.cur.execute(f"SELECT * FROM members WHERE officer={officer.id}").fetchall()
		except:
			return print('Unable to locate officer by ID')

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
	def add_contribution(cls, member: discord.Member, value: int):
		# check if contribution exists for today
		today = get_days()
		result = cls.cur.execute(f"SELECT * FROM contributions WHERE day={today}").fetchall()
		relative = []
		if len(result):
			relative = [row[1] for row in result]
		if member.id in relative:
			row = result[relative.index(member.id)]
			query = f"""
			UPDATE contributions
			SET points = {row[2] + value}
			WHERE day = {today}
			"""
			print('Updating contributions')
		else:
			query = f"""
			INSERT INTO
				contributions (memberid, points, day)
			VALUES
				({member.id}, {value}, {today})
			"""
			print('Adding contribution')
		cls.commit(query)

	@classmethod
	def fetch_contributions(cls, member: discord.Member):
		result = cls.cur.execute(f"SELECT * FROM contributions WHERE memberid={member.id} ORDER BY day").fetchall()
		return result

	@classmethod
	@property
	def schema(cls):
		table_names = cls.cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
		table_names = [row[0] for row in table_names]
		for table in table_names:
			pragma = cls.con.execute(f"PRAGMA table_info('{table}')").fetchall()
			yield table, pragma