import sqlite3
import discord
import yaml
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

server = None
roles = dict()
def init(guild: discord.Guild):
	print(f'Initiating {guild.name} as Tempest server.')
	global server, roles
	server = guild
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
			return # can't connect to database, skip this method.

		create_members = '''
		CREATE TABLE IF NOT EXISTS members (
			id INTEGER PRIMARY KEY,
			ign TEXT,
			officer INTEGER, 
			member BOOL NOT NULL
			);
		'''

		create_inactive = '''
		CREATE TABLE IF NOT EXISTS inactive (
		id INTEGER PRIMARY KEY,
		ti1 INTEGER NOT NULL,
		ti2 INTEGER NOT NULL
		);
		'''

		cls.cur.execute(create_members)
		cls.cur.execute(create_inactive)

		cls.con.commit()
		# END OF INITIALIZATION

	@classmethod
	def commit(cls, *query):
		for q in query:
			cls.cur.execute(q)
		cls.con.commit()

	@classmethod
	def add_member(cls, member: discord.Member, ign='NULL', officer='NULL', ismember=False):
		query = f"""
		INSERT INTO
		   members (id, ign, officer, member)
		VALUES
		   ({member.id}, '{ign}', '{officer}', {ismember});
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
	def get_member(cls, member: discord.Member):
		try:
			return cls.cur.execute(f'SELECT * FROM members WHERE id={member.id}').fetchone()
		except:
			return print('Unable to find', member.name, 'in database.')

	@classmethod
	def get_member_by_ign(cls, tof: str):
		try:
			return cls.cur.execute(f"SELECT * FROM members WHERE tof='{tof}'")
		except:
			return print('Unable to find Tower of Fantasy username:', tof, 'in database.')

