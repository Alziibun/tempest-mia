import discord
import tempest
import datetime as dt
from discord.ext import commands
from tempest import Database as db

devs = [90893355029921792]

class Developer(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	async def cog_check(self, ctx):
		if ctx.author.id in devs:
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



def setup(bot):
	bot.add_cog(Developer(bot))