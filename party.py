import discord
import tempest
import datetime
import asyncio
from tempest import Database as db
from enum import Enum
from discord.ext import commands
from discord.commands import SlashCommandGroup
from discord import option

Monday    = 0
Tuesday   = 1
Wednesday = 2
Thursday  = 3
Friday    = 4
Saturday  = 5
Sunday    = 6

parties = dict()
difficulties = [
('I',    20),
('II',   25),
('III',  31),
('IV',   37),
('V',    43),
('VI',   50),
('VII',  60),
('VIII', 70)]

class Activity(Enum):
    def __new__(cls,  name: str, diffs: list, times: set=None, rewards: dict=None, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = name
        return obj
    def __init__(self, name: str, diffs: list, times: set=None, rewards: dict=None):
        self._diffs = diffs
        self._times = times
        self._rewards = rewards

    @property
    def available(self):
        if self._times is not None:
            today = datetime.datetime.now().weekday()
            if today not in self._times:
                return False
        return True

    @property
    def rewards(self):
        if self._rewards is not None:
            entry_list = []
            for section in self._rewards:
                entry = f"**{section.capitalize()}**: {', '.join(self._rewards[section].values())}"
                entry_list.append(entry)
            body = '\n'.join(entry_list)
            return body
        else:
            return None

    @property
    def name(self):
        return self.value

    def full_name(self, diff=1):
        return f"{self.name} {self._diffs[diff-1][0]}"

    def get_level_requirement(self, diff=1):
        return self._diffs[diff-1][1]

class JointOps(Activity):
    SPACETIME_TRAINING_GROUND = "Spacetime Training Ground", difficulties, (Friday, Saturday),  dict(matrices=['Huma', 'Samir', 'Robarg', 'Bai Ling'], gear=['Arm', 'Chest'])
    DEEPSEA_STRONGHOLD = "Deepsea Stronghold",               difficulties, (Tuesday, Saturday), dict(matrices=['KING', 'Crow', 'Frost Bot', 'Echo'], gear=['Pants', 'Gloves'])
    DEEPSEA_PROVING_GROUND = "Deepsea Proving Ground",       difficulties, (Thursday, Sunday),  dict(matrices=['Meryl', 'Zero', 'Apophis', 'Hilda'], gear=['Boots', 'Belt'])
    QUARANTINE_AREA = "Quarantine Area",                     difficulties, (Monday, Friday),    dict(matrices=['Tsubasa', 'Shiro', 'Barbarossa', 'Pepper'], gear=['Arm', 'Chest'])
    HYENAS_ARENA = "Hyenas Arena",                           difficulties, (Wednesday, Sunday), dict(matrices=['Cocoritter', 'Shiro', 'Sobek', 'Ene'], gear=['Shoulder', 'Helmet'])

class Raids(Activity):
    MIDLEVEL_CONTROL_ROOM = "Midlevel Control Room", [('Normal', 60)]
    PHANTASMIC_ZENITH = "Phantasmic Zenith",         [('Normal', 66)]
    SHATTERED_REALM = "Shattered Realm",             [('Normal', 70)]

class FrontierClash(Activity):
    FRONTIER_CLASH = 'Frontier Clash', [('Normal', 41), ('Hard', 50)]

class VoidRift(Activity):
    VOID_RIFT = 'Void Rift', [('Normal', 41)]

TANK = 'Tank'
HEALER = 'Support'
DPS = 'DPS'
class Role(Enum):
    def __new__(cls, role_name: str, role_id: int, emoji_id: int, *args, **kwargs):
        obj = object.__new__(cls)
        role = role_name
        obj._value_ = role
        return obj
    def __init__(self, role_name: str, role_id: int, emoji_id: int, *args, **kwargs):
        self._emoji = emoji_id
        self.id = role_id
        print(self.name, self.value, self.id, self._emoji)

    @property
    def role(self):
        return tempest.server.get_role(self.id)

    @property
    def emoji(self):
        for e in tempest.server.emojis:
            if e.id == self._emoji:
                return e

    @classmethod
    def from_member(cls, member: discord.Member):
        for name, role in cls.__members__.items():
            if role.role in member.roles:
                return role

    @classmethod
    @property


    TANK         = TANK,   1006259118660665414, 1021862888442445855
    HEALER       = HEALER, 1006259266878971934, 1021862889906241598
    VOLT_DPS     = DPS,    1021863478857842738, 1021862197518925885
    ICE_DPS      = DPS,    1021863787885768795, 1021862358571827240
    FLAME_DPS    = DPS,    1021864131147595866, 1021862198991147039
    PHYSICAL_DPS = DPS,    1021864468709388398, 1021862196382269532

class Member:
    def __init__(self, member: discord.Member, role: Role=None):
        if role == None:
            for i in [TANK, HEALER, DPS]:
                if i.role in member.roles:
                    self._role = i
        else:
            self._role = role
        self._member = member
        print(member.name, self._role)

    @property
    def role(self):
        # Role class
        return self._role

    @property
    def roles(self):
        return self.member.roles

    @property
    def member(self):
        return self._member

    @property
    def id(self):
        # discord.Member.id
        return self._member.id

    @property
    def mention(self):
        # discord.Member.mention
        return self._member.mention

    @property
    def ign(self):
        data = db.get_member(self.member)
        return data[2] # ign

    @property
    def party(self):
        for p in parties.values():
            if self.member in p.members:
                return True
        return False


class Party:
    """
    Class that handles party information.
    Usage:
    - new party
    var = Party(ctx, 'joint op')
    - adding a party to the global list
    parties[str(leader.id)] = self
    """
    def __init__(self, leader: discord.Member, activity=None, diff=1, timeout=86400, req_healer=1, req_dps=2, req_tank=1):
        if leader.id in [int(id) for id in parties]:
            raise IndexError('Party already exists.')
        self._members = []
        self.activity = activity
        self.diff = diff
        self.leader = Member(leader)

        self.req_healer = req_healer
        self.req_dps = req_dps
        self.req_tank = req_tank

        self.message = None
        self.view = None
        self.thread = None
        parties[str(leader.id)] = self
        print('PARTY:', leader.display_name, 'created a party.')

    @property
    def members(self):
        """
        Return a list of members as discord.Member references
        """
        return [member.member for member in self.members]

    @property
    def rich_members(self):
        """
        Used for embed.  Returns the list of party members with their role emoji.
        """
        body = ''
        tanks = 0
        dps = 0
        healers = 0

        # tanks
        for member in self._members:
            if member.role is TANK:
                tanks += 1
                body += f"{str(member.role.emoji)} {member.mention} ({member.ign})\n"
        while tanks < self.req_tank:
            body += f"{str(TANK.emoji)} *None*\n"
            tanks += 1

        # healers
        for member in self._members:
            if member.role is HEALER:
                healers += 1
                body += f"{str(member.role.emoji)} {member.mention} ({member.ign})\n"
        while healers < self.req_healer:
            body += f"{str(HEALER.emoji)} *None*\n"
            healers += 1

        # dps
        for member in self._members:
            if member.role is DPS:
                dps += 1
                body += f"{str(member.role.emoji)} {member.mention} ({member.ign})\n"
        while dps < self.req_dps:
            body += f"{str(DPS.emoji)} *None*\n"
            dps += 1

        return body

    @property
    def tanks(self):
        return len([m for m in self._members if m.role is TANK])

    @property
    def healers(self):
        return len([m for m in self._members if m.role is HEALER])

    @property
    def dps(self):
        return len([m for m in self._members if m.role is DPS])

    async def create_thread(self):
        self.thread = await tempest.party.create_thread(name=f"{self.leader.member.display_name}'s party", type=discord.ChannelType.private_thread)
        opening = await self.thread.send(f"Here is your party's thread! {self.leader.mention}")
        await opening.pin()

    async def add_member(self, member: discord.Member, role=None):
        member = Member(member, role)
        if member.party:
            return
        self._members.append(member)
        print('Added', member.member.display_name, 'to', self.leader.ign,'party.')
        message = await self.thread.send(f"{str(member.role.emoji)} {member.mention} joined the party! {self.leader.mention}")
        await asyncio.sleep(2)
        await message.edit(f"{str(member.role.emoji)} {member.mention} joined the party!")
        await self.create_listing()

    async def start(self):
        await self.create_thread()
        await self.add_member(self.leader.member)

    async def end(self):
        id = len([thread for thread in tempest.party.threads if thread.archived or thread.locked])
        await self.thread.edit(name = f"PARTY ARCHIVE {id} : {self.leader.ign}", archived = True, locked = True)
        await self.message.delete()
        print(self.leader.ign, 'party was ended.')


    def remove_member(self, member: discord.Member):
        for m in self.members:
            if m.member == member:
                del m

    async def create_listing(self):
        embed = discord.Embed(
            title=f"{self.activity.full_name(self.diff)}",
            description= f"**Level requirement**: {self.activity.get_level_requirement(self.diff)}"
        )
        embed.set_author(name=self.leader.ign, icon_url=self.leader.member.display_avatar.url)
        embed.add_field(name='Members', value=self.rich_members)
        view = discord.ui.View(timeout=None)
        view.add_item(JoinAsTank(self))
        view.add_item(JoinAsDPS(self))
        view.add_item(JoinAsHealer(self))
        if self.message is None:
            self.message = await tempest.party.send(embed=embed, view=view)
        else:
            print('edit message')
            await self.message.edit(embed=embed, view=view)

class JoinAsTank(discord.ui.Button):
    def __init__(self, party: Party, *args, **kwargs):
        super().__init__(label='Join as Tank', custom_id='join-tank', emoji=TANK.emoji, *args, **kwargs)
        self.party = party
        if party.tanks >= party.req_tank:
            self.disabled = True
    async def callback(self, interaction):
        await self.party.add_member(interaction.user, TANK)

class JoinAsHealer(discord.ui.Button):
    def __init__(self, party: Party, *args, **kwargs):
        super().__init__(label='Join as Healer', custom_id='join-healer', emoji=HEALER.emoji, *args, **kwargs)
        self.party = party
        if party.healers >= party.req_healer:
            self.disabled = True

    async def callback(self, interaction):
        await self.party.add_member(interaction.user, HEALER)

class JoinAsDPS(discord.ui.Button):
    def __init__(self, party: Party, *args, **kwargs):
        super().__init__(label='Join as DPS', custom_id='join-dps', emoji=DPS.emoji, *args, **kwargs)
        self.party = party
        if party.dps >= party.req_dps:
            self.disabled = True

    async def callback(self, interaction):
        await self.party.add_member(interaction.user, DPS)

class LFG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('LFG properly loaded')


    party = SlashCommandGroup('party', 'Manage your party')
    create = party.create_subgroup('create', 'Create a party')

    @staticmethod
    def get_joint_ops(ctx: discord.AutocompleteContext):
        print(ctx.value)
        return [op.name for op in JointOps if ctx.value.lower() in op.name.lower() and op.available]

    @staticmethod
    def joint_op_diffs(ctx: discord.AutocompleteContext):
        print(ctx.value)
        return [diff[0] for diff in difficulties if ctx.value.lower() in diff[0].lower()]

    @party.command()
    async def end(self, ctx: discord.ApplicationContext):
        if parties.get(ctx.author.id):
            await ctx.response.defer()
            await parties[ctx.author.id].end()

    @create.command(name='joint_op')
    @option(name='name', description='Name of the joint op you want to create a party for.')
    @option(name='difficulty', description='Select the difficulty of the join op.')
    async def create_joint_op(self, ctx, name, difficulty):
        diff = [diff[0] for diff in difficulties].index(difficulty) + 1
        #try:
        op = JointOps(name)
        party = Party(ctx.author, op, diff=diff)
        await party.start()
        #except:
        #    return await ctx.respond("Couldn't find an operation by that name.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        await tempest.wait_until_ready()
        print("Starting roles")
        global TANK, HEALER, DPS
        TANK   = Role(tempest.server, TANK)
        HEALER = Role(tempest.server, HEALER)
        DPS    = Role(tempest.server, DPS)


def setup(bot):
    bot.add_cog(LFG(bot))