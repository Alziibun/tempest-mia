import discord
import shutil
import requests
import tempfile
import chromedriver_autoinstaller
import tempest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def format(entry) -> str:
    """
    Convert HTML markup into Discord markdown
    """
    parsed_string = ''
    if entry.name == 'ol':
        parsed_list = []
        index = 0
        for li in entry.contents:
            index += 1
            parsed_list.append(f"\n   {index}.  {format(li)}")
        parsed_string += ''.join(parsed_list)
    else:
        for t in entry.contents:
            match t.name:
                case 'strong':
                    parsed_string += f"**{format(t)}**"
                case 'em':
                    parsed_string += f"__{format(t)}__"
                case 'br':
                    print('breaking line')
                    parsed_string += '\n'
                case 'p':
                    parsed_string += f"{format(t)}"
                case 'li':
                    parsed_string += f"{format(t)}"
                case _:
                    parsed_string += t
    return parsed_string
class Simulacra:
    def __init__(self, character_name: str, source_page):
        if character_name in simulacra.keys():
            return
        self.url = f"https://toweroffantasy.info/simulacra/{character_name.replace(' ','-')}"
        self._soup = BeautifulSoup(source_page, 'html.parser')
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

    @property
    def abilities(self) -> dict:
        source = self._soup.find('section', attrs={'class': 'weapon-abilities'})
        headers = source.find_all('details')
        abil = dict()
        for details in headers:
            name = details.summary.h4.string.capitalize()
            weapon_abilities = dict()
            for ability in details.div.find_all('div', attrs={'class': 'weapon-ability'}):
                ability_name = ability.h3.string
                parsed_body = ''
                input_string = str()
                if ability.find('ul', attrs={'class': 'ability-inputs'}):
                    input_string = f"{' + '.join([f'`{input.kbd.string}`' for input in ability.ul.contents if input.name == 'li'])}"
                    for t in ability.contents[2:]:
                        parsed_body += format(t)
                else:
                    for t in ability.contents[1:]:
                        parsed_body += format(t)
                weapon_abilities.update({f"{ability_name}": {'inputs': input_string, 'description': parsed_body}})
            abil.update({f"{name}": weapon_abilities})
        return abil


    @classmethod
    @property
    def all_characters(cls) -> list:
        characters = []
        menu = simulacra_page.find('menu', attrs={"class":"modal-menu simulacra"})
        for li in menu.find_all('li'):
            characters.append(li.h3.string)
        return characters

    @classmethod
    async def setup(cls):
        with webdriver.Chrome() as driver:
            driver.get("https://toweroffantasy.info/simulacra")
            wait = WebDriverWait(driver, 10)
            root = driver.current_window_handle
            assert len(driver.window_handles) == 1
            for name in cls.all_characters:
                driver.switch_to.new_window('tab')
                driver.get(f"https://toweroffantasy.info/simulacra/{name.replace(' ','-')}")
                wait.until(EC.title_is(f"{name} | Tower of Fantasy Index"))
                simulacra[name] = Simulacra(name, driver.page_source)


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
        url=simul.url
    )
    for starring, desc in simul.advancements:
        embed.add_field(name=starring, value=desc, inline=False)
    embed.set_author(name=simul.name, icon_url=avatar_file)
    embed.set_thumbnail(url=weapon_file)
    return embed, files

def ability_embed(name: str, category: str):
    simul = simulacra[name]
    selection = simul.abilities[category]
    embed = discord.Embed(title=category)
    for skill_name, val in selection.items():
        inputs = val['inputs']
        description = val['description']
        if category in ['Skill', 'Discharge']:
            embed.title += f": {skill_name}"
            embed.description = f"{description}"
        else:
            embed.add_field(name=skill_name, value=f"{f'Input: {inputs}' if inputs else ''}\n>>> {description}", inline=False)
    return embed


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def autocomplete_simulacra(ctx: discord.AutocompleteContext):
        return [sim for sim in simulacra if ctx.value.lower() in sim.lower()]

    @commands.slash_command()
    @option(name='name', description='Search for a Simulacra\'s advancements from tofindex site', autocomplete=autocomplete_simulacra)
    async def advancements(self, ctx,  name: str):
        embed, files = advancement_embed(name)
        await ctx.respond(files=files, embed=embed, ephemeral=False)


    @commands.slash_command()
    @option(name='name', description='Name of the Simulacra', autocomplete=autocomplete_simulacra)
    @option(name='category', description='Skill category selection', choices=[
        discord.OptionChoice('Normal attacks', value='Normal'),
        discord.OptionChoice('Dodge', value='Dodge'),
        discord.OptionChoice('Skill', value='Skill'),
        discord.OptionChoice('Discharge', value='Discharge')])
    async def abilities(self, ctx, name: str, category):
        embed, files = character_embed(name)
        abil_embed = ability_embed(name, category)
        await ctx.respond(files=files, embeds=[embed, abil_embed], ephemeral=False)

    @commands.Cog.listener()
    async def on_ready(self):
        await Simulacra.setup()


def setup(bot):
    #simulacra['Frigg'] = Simulacra('Frigg')
    bot.add_cog(Info(bot))

