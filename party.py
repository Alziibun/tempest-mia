import discord
import tempest
from discord.ext import commands

Monday    = 0
Tuesday   = 1
Wednesday = 2
Thursday  = 3
Friday    = 4
Saturday  = 5
Sunday    = 6


TANK = 1006259118660665414, 1006942269582102609
HEALER = 1006259266878971934, 1006942271872180355
DPS = 1006259071151780051, 1006942270366429216

parties = dict()
joint_ops = dict(
    difficulty = [
            ('I',    20),
            ('II',   25),
            ('III',  31),
            ('IV',   37),
            ('V',    43),
            ('VI',   50),
            ('VII',  60),
            ('VIII', 70)
        ],
    locale  = {
        "Spacetime Training Ground" : {
            times    : (4, 5),
            matrices : ['Huma', 'Samir', 'Robarg', 'Bai Ling'],
            gear     : ['Arm', 'Chest']
        },
        "Deepsea Stronghold"        : {
            times    : (1, 5),
            matrices : ['KING', 'Crow', 'Frost Bot', 'Echo'],
            gear     : ['Pants', 'Gloves']
        },
        "Deepsea Proving Ground"    : {
            times    : (3, 6),
            matrices : ['Meryl', 'Zero', 'Apophis', 'Hilda'],
            gear     : ['Boots', 'Belt']
        },
        "Quarantine Area"           : {
            times    : (0, 5),
            matrices : ['Tsubasa', 'Shiro', 'Barbarossa', 'Pepper'],
            gear     : ['Arm', 'Chest']
        },
        "Hyenas Arena"              : {
            times    : (2, 6),
            matrices : ['Cocoritter', 'Shiro', 'Sobek', 'Ene'],
            gear     : ['Shoulder', 'Helmet']
        }
    }
)

class Role:
    def __init__(self, server: discord.Guild, role_id, emote_id):
        self._role = server.get_role(role_id)
        for e in server.emojis:
            if e.id == emote_id:
                self._emoji = e

    @property
    def emoji(self):
        # discord.Emoji
        return self._emoji

    @property
    def role(self):
        # discord.Role
        return self._role

class Member:
    def __init__(self, member: discord.Member, role: Role):
        self._role = role
        self._member = member

    @property
    def role(self):
        # Role class
        return self._role

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

class Party:
    """
    Class that handles party information.
    Usage:
    - new party
    var = Party(ctx, 'joint op')
    - adding a party to the global list
    parties[str(leader.id)] = self
    """
    def __init__(self, ctx, activity=None):
        server = ctx.guild
        leader = ctx.author
        global TANK, HEALER, DPS
        TANK   = Role(server, TANK[0], TANK[1])
        HEALER = Role(server, HEALER[0], HEALER[1])
        DPS    = Role(server, DPS[0], DPS[1])
        if leader.id in [int(id) for id in parties]:
            raise IndexError('Party already exists.')
        self._members = []
        self._activity = activity
        self._leader = leader
        parties[str(leader.id)] = self
        self.add_member(leader)

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
        for member in self._members:
            body += f"{str(member.role.emoji)} {member.mention}\n"
        return body

    @property
    def leader(self):
        return self._leader

    def add_member(self, member: discord.Member,role=None):
        if not role:
            for i in [TANK, HEALER, DPS]:
                if i.role in member.roles:
                    self._members += Member(member, i)

    def remove_member(self, member: discord.Member):
        for m in self.members:
            if m == member:
                del m





class LFG(commands.Cog):
    def __init__(self):
        self.bot = bot
        global TANK, HEALER, DPS


    @commands.group(invoke_without_command=True)
    async def party(self, ctx):
        """
        Manage your party.
        """
        pass

    @party.command()
    async def create(self, ctx, *, activity: str=None):
        """
        Create a party.
        """
        # creates an embed and adds it to a channel that doesn't exist
        match activity.split():
            case ['j', *args]:
                p = Party(ctx, activity)




def setup(bot):
    bot.add_cog(LFG(bot))