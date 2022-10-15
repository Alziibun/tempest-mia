import asyncio

import discord
import tempest
import datetime as dt
from discord.ext import commands
from tempest import Database as db



class Developer(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		if not db.con: db()

	async def cog_check(self, ctx):
		if ctx.author.id in tempest.devs:
			return True
		return False

	@commands.command()
	async def commit(self, ctx, *, query: str):
		"""
		Commit to database
		"""
		try:
			query = query.strip('` ')
			query = query.replace('sql', '')
			db.commit(query)
			await ctx.send('Commit successful.')
		except Exception as e:
			await ctx.reply(f'Commit failed.\nError: {e}')

	@commands.command()
	async def schema(self, ctx):
		"""
		Display database schema.
		"""
		embeds = []
		for table_name, pragma in db.schema:
			_embed = discord.Embed(title=f'{table_name} schema')
			col_name = ''
			col_type = ''
			col_default = ''
			for col in pragma:
				# if key is primary, embolden it
				col_name    += "{1}{0}{1}\n".format(col[1], '**' if bool(col[5]) else '')
				# write the type as code block
				col_type    += f"`{'*' if col[3] else ''}{col[2]}`\n"
				# write the default value of the column
				col_default += f"{'`' + col[4] + '`' if col[4] is not None else '*None*'}\n"
			_embed.add_field(name = "Name", value = col_name)
			_embed.add_field(name = 'Type', value = col_type)
			_embed.add_field(name = 'Default', value = col_default)
			embeds.append(_embed)
			print(table_name)
		await ctx.send(embeds=embeds)

	@commands.command()
	async def view(self, ctx, dbname: str):
		"""
		Shows database info
		"""
		embed = discord.Embed(title=dbname)
		for col in db.con.execute(f'PRAGMA table_info("{dbname}")').fetchall():
			vals = [f"{val[0]}" for val in db.con.execute(f"SELECT {col[1]} FROM {dbname}").fetchall()]
			embed.add_field(name = col[1], value='\n'.join(vals))
		await ctx.send(embed=embed)


	@commands.slash_command()
	async def promote(self, ctx, user: discord.Member):
		await tempest.promote(user)




def setup(bot):
	bot.add_cog(Developer(bot))