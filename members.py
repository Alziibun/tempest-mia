import discord
import tempest
from tempest import Database as db
from discord.ext import commands

class Membership(commands.Cog):
    def __init__(self):
        self.bot = bot


    @bot.command(aliases=['ru'])
    async def recruit(self, ctx,  *, name: str):
        if tempest.has_access(ctx.author, 3):
            if '<@' in name:
                name = name[2:-1] # clips off <@ and > from ID
                member = ctx.guild.get_member(int(name))
            else:
                member = ctx.guild.get_member_named(name)




def setup(bot):
    bot.add_cog(Membership(bot))