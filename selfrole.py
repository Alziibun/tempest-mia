import discord
import tempest
import re
from discord import Option
from discord.ext import commands



selfrole = {
    'LFG' : [
        # discord role id     emoji id
        1007754185367888014,
        1023208476446556221,
        1023209294042239006,
        1023209333527433216,
        1023709699943702619,
        1024070454270500864,
        1024070490681262130,
    ],
    'Role' : [
        1006259266878971934,
        1006259118660665414,
        1021863478857842738,
        1021863787885768795,
        1021864131147595866,
        1021864468709388398
    ],
    'Character' : [
        942230609701511236,
        942230609718292571,
        942230609701511235,
        942230609701511237,
        942230609701511232,
        942230609739251733,
        942230609701511229,
        942230609718292579,
        942232911707533312,
        1005734016957296722,
        942230609701511234,
        1005734019821998120,
        942230609739251732,
        1006060204045111306,
        942230609701511231,
        942230609718292570,
        942230609701511233,
        1006060346437550151,
        942232923862605874,
        1011254142167154750,
        1024074269707214908
    ]
}

def get_character_options():
    for roleid in selfrole['Character']:
        role = tempest.server.get_role(roleid)
        emoji = None
        for e in tempest.server.emojis:
            name = re.sub(r'[^a-zA-Z]+', '', role.name.lower())
            if name == e.name.lower():
                emoji = e
                break
        yield role, emoji

def get_role_options():
    for roleid in selfrole['Role']:
        role = tempest.server.get_role(roleid)
        role_name = role.name.split(' ')[0].lower()
        emoji = [emoji for emoji in tempest.server.emojis if emoji.name == re.sub(r'[^a-zA-Z]+', '', role_name.lower())][0]
        yield role, emoji

def get_lfg_options():
    for roleid in selfrole['LFG']:
        role = tempest.server.get_role(roleid)
        yield role

class LFGSelect(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(placeholder='Select each LFG role you would like', min_values=1, max_values=len(selfrole['LFG']), row=1, *args, **kwargs)
        for role in get_lfg_options():
            name = role.name.split('] ')[1]
            self.add_option(label=name, value=str(role.id))


    async def callback(self, interaction: discord.Interaction):
        for roleid in selfrole['LFG']:
            role = tempest.server.get_role(roleid)
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
        for roleid in self.values:
            role = tempest.server.get_role(int(roleid))
            await interaction.user.add_roles(role)
        await interaction.response.send_message('Your roles have been changed.', ephemeral=True)

class CharacterSelect(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(placeholder='Select up to 3 Simulacra from the list', min_values=1, max_values=3, row=2, *args, **kwargs)
        for role, emoji in get_character_options():
            name = role.name
            self.add_option(label=name, emoji=emoji, value=str(role.id))

    async def callback(self, interaction: discord.Interaction):
        for roleid in selfrole['Character']:
            role = tempest.server.get_role(roleid)
            print(roleid, role)
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
        for roleid in self.values:
            role = tempest.server.get_role(int(roleid))
            await interaction.user.add_roles(role)
        await interaction.response.send_message('Your roles have been changed.', ephemeral=True)


class RoleSelect(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(placeholder='Select a role from the list', row=3, *args, **kwargs)
        for role, emoji in get_role_options():
            name = role.name
            self.add_option(label=name, emoji=emoji, value=str(role.id))

    async def callback(self, interaction: discord.Interaction):
        for roleid in selfrole['Role']:
            role = tempest.server.get_role(roleid)
            print(roleid, role)
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
        for roleid in self.values:
            role = tempest.server.get_role(int(roleid))
            await interaction.user.add_roles(role)
        await interaction.response.send_message('Your roles have been changed.', ephemeral=True)

class Selfrole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def selfrole(self, ctx):
        view = discord.ui.View()
        view.add_item(LFGSelect())
        view.add_item(CharacterSelect())
        view.add_item(RoleSelect())
        await ctx.respond('Use the following menus to select your roles.\n*Your roles will be wiped once selected so choose all the ones that you want to have*', view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(Selfrole(bot))


