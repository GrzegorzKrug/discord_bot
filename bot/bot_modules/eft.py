import requests
import aiohttp
import pandas as pd
import bs4

from discord.ext.commands import Cog, command
from discord import Colour, Embed

from .permissions import *
from .decorators import *
from .definitions import *


class CogTest(Cog):
    def __init__(self):
        self.bot = bot

    @command()
    @advanced_perm_check_method()
    @my_help.help_decorator("cog1 test")
    async def cog1(self, ctx, *args, text=None, **kwargs):
        print("Cog1")
        await ctx.send(f"txt: {text}")

    @command()
    @advanced_args_method()
    @log_call_method
    async def eft(self, ctx, *keyword, dry=False, **kwargs):
        search_url = r'https://escapefromtarkov.gamepedia.com/index.php?search='
        if len(keyword) < 1:
            await ctx.send("What? 🤔")
            return None
        search_phrase = '+'.join(keyword)
        url = search_url + search_phrase
        logger.debug(f"Eft url: {url}")
        # results = requests.get(url)
        # print(results.text)

    @command(aliases=['eftammoget'])
    @advanced_perm_check_method(is_bot_owner)
    @log_call_method
    @log_duration_any
    async def eftgetammo(self, ctx, *args, **kwargs):
        """
        Request and process ammo spreadsheet in current shape.
        Args:
            ctx:
            *args:
            **kwargs:

        Returns:

        """
        spread_sheet_url = r"https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#"
        # res = aiohttp.request("get", spread_sheet_url)
        res = requests.get(spread_sheet_url)
        if res.status_code != 200:
            await ctx.send(f"Request failed: {res.status_code}")
            return None

        data_row_start = 3
        ammo_data_end_at_column = 13
        granades_at_column = 14
        granades_rows_ammount = 6

        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        table = soup.find(attrs={"class": "waffle"}).find("tbody").find_all("tr")

        header = bs4.BeautifulSoup(str(table[0]), 'html.parser').find_all("td")
        header = [cell.text for cell in header]

        header_ammo = ["Caliber"] + header[:ammo_data_end_at_column]
        header_granades = header[granades_at_column:]

        ammo_df = pd.DataFrame(columns=header_ammo)
        underbarrel_df = pd.DataFrame(columns=header_granades)

        table = table[data_row_start:]
        for r_id, row in enumerate(table):
            row_soup = bs4.BeautifulSoup(str(row), 'html.parser')
            row_elements = row_soup.find_all("td")

            ammo_list = self.process_table_row(row_elements[:ammo_data_end_at_column],
                                               split_caliber=True,
                                               tracer_pos=-1)
            serie = pd.Series(ammo_list, index=header_ammo)
            ammo_df = ammo_df.append(serie, ignore_index=True)

            if r_id < granades_rows_ammount:
                granade_list = self.process_table_row(row_elements[granades_at_column:])
                serie = pd.Series(granade_list, index=header_granades)
                underbarrel_df = underbarrel_df.append(serie, ignore_index=True)

        ammo_df = ammo_df.loc[:, ~(ammo_df.columns == "")]
        ammo_df.to_csv("ammo.csv")

        underbarrel_df = underbarrel_df.loc[:, ~(underbarrel_df.columns == "")]
        underbarrel_df.to_csv("granade_ammo.csv")

        logger.info(f"Saved tarkov ammo.")
        await send_approve(ctx)

    @staticmethod
    def process_table_row(_row_elements, split_caliber=False, tracer_pos=None):
        row_elements = _row_elements.copy()
        row_elements = [cell.text.title() for cell in row_elements]
        row_elements[0] = row_elements[0].replace('"', '').replace(r"/", "x").replace(r"X", "x").lower()
        if split_caliber:
            try:
                caliber, name = re.split(r"[a-z]* ?mm ?", row_elements[0])
            except ValueError:
                caliber, *name = re.split(r' \b', row_elements[0])
                name = ' '.join(name)
            name = name.title()
            caliber = caliber.lower()
            row_elements = [caliber, name] + row_elements[1:]

        if tracer_pos:
            row_elements[tracer_pos] = "Yes" if row_elements[tracer_pos] == "✔" else "No"

        return row_elements

    @command()
    @advanced_args_method()
    @log_call_method
    @my_help.help_decorator("Show ammo stats from EFT.", "!ammo caliber|name|granades|tracer (sorting)")
    @check_query_method
    async def ammo(self, ctx, query=None, priority=None, *args, **kwargs):
        """
        Available queries: <caliber>, <name>, granades, tracer
        Available sortings: damage, penetration, accuracy, recoil.

        Args:
            ctx:
            query:
            priority:
            *args:
            **kwargs:

        Returns:

        """
        if not query:
            calibers = pd.read_csv("ammo.csv", dtype=str)["Caliber"].unique()
            await ctx.send(f"Tell me **caliber ** or ammo **name**, example !ammo 5.56. \n"
                           f"Available calibers:\n"
                           f"{', '.join(f'*{ob}*' for ob in calibers)}")
            await ctx.message.delete()
            return None

        query = query.lower()

        if priority:
            priority = priority.lower()

        if "gran" in query or "bar" in query or 'unde' in query:
            granade_df = pd.read_csv("granade_ammo.csv", dtype=str)
            embed = self.create_embed_granade(granade_df, priority="Damage")

        else:
            ammo_df = pd.read_csv("ammo.csv").round(2)

            if "trac" in query:
                ammo_df = ammo_df[ammo_df['Tracer'] == "Yes"]
            elif "all" in query:
                pass
            else:
                ammo_df = ammo_df[
                    ammo_df["Caliber"].str.contains(query.lower()) |
                    ammo_df["Name"].str.contains(query.title())
                    ]

            embed = self.create_embed_ammo(ammo_df, priority=priority)
        if not embed:
            await ctx.send("Nothing matching found.")
        else:
            await ctx.send(embed=embed)
            await send_approve(ctx)

    def create_embed_ammo(self, data, priority=None):
        spread_sheet_url = r"https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#"
        author = bot.get_user(147795752943353856)
        ammo_txtlen = 5
        col = Colour.from_rgb(30, 129, 220)

        joiner = " | "
        keys = data.columns
        data = data.copy()

        if len(data) < 1:
            return None

        if priority and "dam" in priority:
            data = data.sort_values(['Damage', 'Penetration Pwr'], ascending=False)
            sort_text = "Damage"
        elif priority and "acc" in priority:
            sort_text = "Accuracy"
            data = data.sort_values(['Accuracy %', 'Penetration Pwr'], ascending=False)
        elif priority and "reco" in priority:
            sort_text = "Recoil"
            data = data.sort_values(['Recoil %', 'Penetration Pwr'], ascending=False)
        else:
            sort_text = "Penetration"
            data = data.sort_values(['Penetration Pwr', 'Pen. Chance', 'Damage'], ascending=False)

        calibers = ', '.join(data["Caliber"].unique())

        embed = Embed(title=f'{calibers}', color=col,
                      description=f"[Ammo chart link]({spread_sheet_url})")
        embed.set_author(name="Ammo table")
        embed.add_field(name="Sorted by", value=sort_text, inline=True)
        embed.add_field(name="Compared bullets", value=str(len(data)), inline=True)
        for key in keys[2:]:
            if not key:
                continue
            row_arr = list(data[key])
            row_text = joiner.join(str(ob).ljust(ammo_txtlen) for ob in row_arr)
            embed.add_field(name=key, value=f"`{row_text}`", inline=False)

        embed.set_footer(text='By  Youshisu', icon_url=author.avatar_url)
        return embed

    def create_embed_granade(self, data, priority=None):
        spread_sheet_url = r"https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#"
        author = bot.get_user(147795752943353856)
        ammo_txtlen = 5
        col = Colour.from_rgb(30, 129, 220)

        joiner = " | "
        keys = data.columns
        data = data.copy()
        if len(data) < 1:
            return None

        data = data.sort_values(['Damage'], ascending=False)

        embed = Embed(title=f'Under-barrels', color=col,
                      description=f"[Ammo chart link]({spread_sheet_url})")
        embed.set_author(name="Ammo table")

        for key in keys[1:]:
            if not key:
                continue
            row_arr = list(data[key])
            row_text = joiner.join(str(ob).ljust(ammo_txtlen) for ob in row_arr)
            embed.add_field(name=key, value=f"`{row_text}`", inline=False)

        embed.set_footer(text='By  Youshisu', icon_url=author.avatar_url)
        return embed
