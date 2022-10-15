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
    def dps(cls):
        for e in tempest.server.emojis:
            if e.id == 1021862891105816576:
                return e


    TANK         = TANK,   1006259118660665414, 1021862888442445855
    HEALER       = HEALER, 1006259266878971934, 1021862889906241598
    VOLT_DPS     = DPS,    1021863478857842738, 1021862197518925885
    ICE_DPS      = DPS,    1021863787885768795, 1021862358571827240
    FLAME_DPS    = DPS,    1021864131147595866, 1021862198991147039
    PHYSICAL_DPS = DPS,    1021864468709388398, 1021862196382269532

class Member:
    def __init__(self, member: discord.Member, role: Role=None):
        if role == None:
            try:
                self._role = Role.from_member(member)
            except:
                raise IndexError('Unable to find a role from member')
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
    def has_party(self):
        print(parties.values())
        for p in parties.values():
            if len(p.members) > 0:
                print(1)
                if self.member in p.members:
                    return True
        return False


party_matrix = [
    [TANK,   None, None, None],
    [HEALER, None, None, None],
    [DPS,    DPS,  DPS,  DPS ]]

raid_matrix = [
    [TANK,   TANK,   None, None, None, None, None, None],
    [HEALER, HEALER, None, None, None, None, None, None],
    [DPS,    DPS,    DPS,  DPS,  DPS,  DPS,  DPS,  DPS]]


class Party:
    """
    Class that handles party information.
    Usage:
    - new party
    var = Party(ctx, 'joint op')
    - adding a party to the global list
    parties[str(leader.id)] = self
    """
    def __init__(self, leader: discord.Member, activity=None, diff=1, raid=False, timeout=86400):
        if leader.id in [int(id) for id in parties]:
            raise IndexError('Party already exists.')
        self._members = []
        self.activity = activity
        self.diff = diff
        self.leader = Member(leader)
        self.raid = raid
        if self.raid:
            self._tanks = 1
            self._support = 2
            self._dps = 5
        else:
            self._tanks = 1
            self._support = 1
            self._dps = 2

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
        return [member.member for member in self._members]

    @property
    def rich_members(self):
        """
        Used for embed.  Returns the list of party members with their role emoji.
        """
        body = ''
        temp_settings = [(Role.TANK.emoji, self.tanks, self.max_tanks), (Role.HEALER.emoji, self.healers, self.max_support), (Role.dps, self.dps, self.max_dps)]
        for emoji, members, maximum in temp_settings:
            index = len(members)
            for member in members:
                body += f"{emoji} {member.mention} (**{member.ign}**)\n"
            while index < maximum:
                body += f"{emoji} *None*\n"
                index += 1
        return body
    
    @property
    def max_size(self):
        return 4 if not self.raid else 8

    @property
    def tanks(self):
        return [m for m in self._members if m.role.value is TANK]

    @property
    def max_tanks(self):
        return self._tanks

    @property
    def healers(self):
        return [m for m in self._members if m.role.value is HEALER]

    @property
    def max_support(self):
        return self._support

    @property
    def dps(self):
        return [m for m in self._members if m.role.value is DPS]

    @property
    def max_dps(self):
        return self._dps

    def set_max_roles(self, tanks=0, healers=0, dps=0):
        self._tanks = tanks
        self._healers = healers
        self._dps = dps

    @classmethod
    def from_member(cls, member: discord.Member):
        for p in parties.values():
            if member in p.members:
                return p
        assert "No party found"

    async def create_thread(self):
        self.thread = await tempest.party.create_thread(name=f"{self.leader.ign}'s party", type=discord.ChannelType.private_thread)
        opening = await self.thread.send(f"Here is your party's thread! {self.leader.mention}")
        await opening.pin()

    async def add_member(self, member: discord.Member, role=None):
        member = Member(member, role)
        if member.has_party:
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
        super().__init__(label='Join as Tank', custom_id='join-tank', emoji=Role.TANK.emoji, *args, **kwargs)
        self.party = party
        if len(party.tanks) >= party.max_tanks:
            self.disabled = True
    async def callback(self, interaction):
        await self.party.add_member(interaction.user, Role.TANK)

class JoinAsHealer(discord.ui.Button):
    def __init__(self, party: Party, *args, **kwargs):
        super().__init__(label='Join as Healer', custom_id='join-healer', emoji=Role.HEALER.emoji, *args, **kwargs)
        self.party = party
        if len(party.healers) >= party.max_support:
            self.disabled = True

    async def callback(self, interaction):
        await self.party.add_member(interaction.user, Role.HEALER)

class JoinAsDPS(discord.ui.Button):
    def __init__(self, party: Party, *args, **kwargs):
        super().__init__(label='Join as DPS', custom_id='join-dps', emoji=Role.dps, *args, **kwargs)
        self.party = party
        if len(party.dps) >= party.max_dps:
            self.disabled = True
    async def callback(self, interaction):
        await self.party.add_member(interaction.user, Role(DPS))

class LFG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('loaded LFG')


    @staticmethod
    def jo_names(ctx: discord.AutocompleteContext):
        print(ctx.value)
        return [op.name for op in JointOps if ctx.value.lower() in op.name.lower() and op.available]
    @staticmethod
    def jo_diffs(ctx: discord.AutocompleteContext):
        print(ctx.value)
        return [diff[0] for diff in difficulties if ctx.value.lower() in diff[0].lower()]

    party = SlashCommandGroup('party')
    create = party.create_subgroup(name='create')

    @create.command(name='joint_op')
    @option(name='name', description='Name of the joint op you want to create a party for.', autocomplete=jo_names)
    @option(name='difficulty', description='Select the difficulty of the join op.', autocomplete=jo_diffs)
    async def joint_op(self, ctx, name: str, difficulty: str):
        diff = [diff[0] for diff in difficulties].index(difficulty) + 1
        op = JointOps(name)
        party = Party(ctx.author, op, diff=diff)
        await party.start()


def setup(bot):
    bot.add_cog(LFG(bot))