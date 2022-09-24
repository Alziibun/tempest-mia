import discord
import shutil
import requests
import tempfile
import chromedriver_autoinstaller
import tempest
from selenium import webdriver
from bs4 import BeautifulSoup
from PIL import Image
from discord.ext import commands
from discord.commands import SlashCommandGroup
from discord import option

chromedriver_autoinstaller.install()
tofindex = 'https://toweroffantasy.info'
index_page = BeautifulSoup(requests.get(tofindex).text, 'html.parser')
simulacra_page = BeautifulSoup(requests.get(tofindex + '/simulacra').text, 'html.parser')
simulacra = dict()

elements = dict(
    ice = 1021862358571827240,
    flame = 1021862198991147039,
    volt = 1021862197518925885,
    physical = 1021862196382269532,
    aberration = 1021862195082039336
)

resonances = dict(
    dps = 1021862891105816576,
    defense = 1021862888442445855,
    support = 1021862889906241598
)

class Simulacra:
    def __init__(self, character_name: str):
        if character_name in simulacra.keys():
            return
        self._url = f"https://toweroffantasy.info/simulacra/{character_name.replace(' ', '-').lower()}"
        print(self._url)
        driver = webdriver.Chrome()
        driver.get(self._url)
        self._html = driver.page_source
        self._soup = BeautifulSoup(self._html, 'html.parser')
        self._name = character_name
        self._weapon = Weapon(self._soup)
        print('Initialized', character_name)
        print('Weapon:', self.weapon.name)
        print('CN Exclusive:', self.is_exclusive)
        print('')

    @property
    def name(self) -> str:
        return self._name

    @property
    def weapon(self):
        return self._weapon

    @property
    def is_exclusive(self) -> bool:
        # is this character china exclusive?
        if self._soup.find('section', attrs={'class':'china-exclusive'}):
            return True
        else:
            return False

    @property
    def avatar(self):
        div = self._soup.find('div', attrs={'class':'header-img-wrapper'})
        url = tofindex + div.img['src']
        filename = div.img['src'].split('/')[-1]
        response = requests.get(url, stream=True)
        with tempfile.TemporaryFile() as tmp:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, tmp)
            img = Image.open(tmp).convert('RGBA')
            filename = filename.replace('.webp', '.png')
            img.save(f'img/avatars/avatar_{filename}', 'png')
        return f'img/avatars/avatar_{filename}'

    @property
    def advancements(self):
        section = self._soup.find('section', attrs={'class':'advancements'})
        for tr in section.table.tbody.find_all('tr'):
            header = ''.join(tr.th.descendants)
            content = ''
            for d in tr.td.p.contents:
                print(d)
                match d.name:
                    case 'strong':
                        content += f"**{d.string}**"
                    case 'br':
                        content += '\n'
                    case 'em':
                        content += f"`{d.string}`"
                    case _:
                        content += d
            yield header, content


    @classmethod
    @property
    def all_characters(cls) -> list:
        characters = []
        menu = simulacra_page.find('menu', attrs={"class":"modal-menu simulacra"})
        for li in menu.find_all('li'):
            characters.append(li.h3.string)
        return characters

class Weapon:
    def __init__(self, soup: BeautifulSoup):
        self._soup = soup
        self._tag = soup.find('div', attrs={'class':'weapon-header'})
        self._info = soup.find('div', attrs={'class':'weapon-info'})
        self._image = soup.find('img', attrs={'class':'weapon-image'})
        self._main_stats = soup.find('div', attrs={'class':'weapon-stat-grid'})
        self.stats = self._main_stats.find_all('div', attrs={'class': 'weapon-stat'})

    @property
    def name(self) -> str:
        return self._info.h3.string

    @property
    def base_stats(self):
        pass

    @property
    def element(self):
        stat = self.stats[1]
        return stat.div.h4.string

    @property
    def resonance(self):
        stat = self.stats[0]
        return stat.div.h4.string

    @property
    def img(self):
        url = tofindex + self._image['src']
        filename = self._image['src'].split('/')[-1]
        response = requests.get(url, stream=True)
        with tempfile.TemporaryFile() as tmp:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, tmp)
            img = Image.open(tmp).convert('RGBA')
            filename = filename.replace('.webp', '.png')
            img.save(f'img/weapons/weapon_{filename}', 'png')
        return f'img/weapons/weapon_{filename}'

def advancement_embed(name):
    simul = simulacra[name]
    avatar = simul.avatar
    weapon = simul.weapon.img
    avatar_file = f"attachment://{avatar.split('/')[-1]}"
    weapon_file = f"attachment://{weapon.split('/')[-1]}"
    element = [emoji for emoji in tempest.server.emojis if emoji.id == elements[simul.weapon.element]][0]
    resonance = [emoji for emoji in tempest.server.emojis if emoji.id == resonances[simul.weapon.resonance]][0]
    files = [discord.File(avatar), discord.File(weapon)]
    embed = discord.Embed(
        title=f"{resonance} {element} {simul.weapon.name}",
        url=simul._url
    )
    for starring, desc in simul.advancements:
        embed.add_field(name=starring, value=desc, inline=False)
    embed.set_author(name=simul.name, icon_url=avatar_file)
    embed.set_thumbnail(url=weapon_file)
    return embed, files

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def autocomplete_simulacra(self, ctx: discord.AutocompleteContext):
        print('huh')
        return [sim for sim in simulacra if ctx.value.lower() in sim.lower()]

    sim = SlashCommandGroup('simulacra', 'Information about ToF Simulacra')

    @sim.command(name='advancement')
    @option(name='name', description='Search for a Simulacra\'s information from tofindex site', autocomplete=autocomplete_simulacra)
    async def advancement(self, ctx,  name: str):
        embed, files = advancement_embed(name)
        await ctx.respond(files=files, embed=embed, ephemeral=False)

    @commands.Cog.listener()
    async def on_ready(self):
        for name in Simulacra.all_characters:
            simulacra[name] = Simulacra(name)

def setup(bot):
    #simulacra['Frigg'] = Simulacra('Frigg')
    bot.add_cog(Info(bot))

