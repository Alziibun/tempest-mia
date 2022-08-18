import sqlite3
import discord
import yaml
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

class Tempest:
	roles = dict()
	def __init__(self, guild):
		print(f'Initiating {guild.name} as Tempest server.')	
		cls = self.__class__
		with open('tempest.yaml', 'r') as file:
			_roles = yaml.load(file, Loader=Loader)
			for k, v in _roles.items():
				cls.roles[k] = {
					'av'  : v['access'],
					'obj' : guild.get_role(v['id'])
					}
				print(cls.roles[k]['obj'].name, 'loaded.')
	# END OF INITILIZATION

	@classmethod
	def get_roles(cls):
		# return roles as a list
		return [i['obj'] for i in cls.roles.values()]

	@classmethod
	def get_rank(cls, member: discord.Member):
		# find the guild rank of a discord member
		for role in cls.roles.values():
			if role['obj'] in member.roles:
				return role

	@classmethod
	def has_access(cls, member: discord.Member, req):
		# check if the member has the required av for the command
		if cls.get_rank(member)['av'] <= req:
			return True
		return False

class Database:

	connection = None

	def __init__(self):
		cls = self.__class__
		try:  # attempt to connect to the sqlite database "database"
			cls.connection = sqlite3.connect("database.sqlite3")
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

		cursor = cls.connection.cursor()
		cursor.execute(create_members)
		cursor.execute(create_inactive)

		cls.connection.commit()
		# END OF INITIALIZATION

	@classmethod
	def add_member(cls, member: discord.Member, ign='NULL', officer='NULL'):
		query = f"""
		INSERT INTO
		   members (id, ign)
		VALUES
		   ({member.id}, '{ign}');
		"""
		cursor.execute(query)
		cls.connection.commit()
		print(f'Added {member.name} to database.')

	@classmethod
	def add_inactive(cls, member: discord.Member, ti1, ti2):
		query = f"""
		INSERT INTO
			members (id, ti1, ti2)
		VALUES
			({member.id}, {ti1}, {ti2})
		"""

		cursor = cls.connection.cursor()
		cursor.execute(query)
		cls.connection.commit()
