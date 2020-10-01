import requests
import aiohttp
import pandas as pd
import bs4
import os

from discord.ext.commands import Cog, command
from discord import Colour, Embed

from .permissions import *
from .decorators import *
from .definitions import *


class EFTCog(Cog):
    def __init__(self):
        self.bot = bot
        self.eft_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', "eft"))
        os.makedirs(self.eft_dir, exist_ok=True)

    @command(aliases=['eftammoget'])
    @advanced_args_method()
    @log_call_method
    @advanced_perm_check_method(restrictions=is_bot_owner)
    @log_duration_any
    async def eftgetammo(self, ctx, *args, **kwargs):
        """
        Request and process ammo spreadsheet in current shape.
        https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#
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
            await ctx.send(f"Request failed, code: {res.status_code}")
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
                grenade_list = self.process_table_row(row_elements[granades_at_column:])
                serie = pd.Series(grenade_list, index=header_granades)
                underbarrel_df = underbarrel_df.append(serie, ignore_index=True)

        ammo_df = ammo_df.loc[:, ~(ammo_df.columns == "")]

        version_text = soup.find(attrs={"class": "name"}).text
        version = re.findall(r"[\d\.]+", version_text)
        version = "".join(version)
        with open(os.path.join(self.eft_dir, "ammo_version.txt"), "wt") as file:
            file.write(version)
            logger.debug(f"Saved ammo version")

        ammo_df.to_csv(os.path.join(self.eft_dir, "ammo.csv"))
        logger.debug(f"Saved ammo.csv")

        underbarrel_df = underbarrel_df.loc[:, ~(underbarrel_df.columns == "")]
        underbarrel_df.to_csv(os.path.join(self.eft_dir, "grenade_ammo.csv"))
        logger.debug(f"Saved grenade_ammo.csv")

        logger.info(f"Saved all tarkov ammo.")
        await send_approve(ctx)

    @staticmethod
    def process_table_row(_row_elements, split_caliber=False, tracer_pos=None):
        row_elements = _row_elements.copy()
        row_elements = [cell.text.title() for cell in row_elements]
        row_elements[0] = row_elements[0].replace('"', '').replace(r"/", "x").replace(r"X", "x").lower()
        if split_caliber:

            try:
                caliber, name = re.split(r" ?[a-z]* ?mm ?", row_elements[0])
            except ValueError:
                caliber, *name = re.split(r' +\b', row_elements[0])
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
    @my_help.help_decorator("Show ammo stats from EFT.", "<caliber>|<name>|grenades|tracer (<sorting>)", menu="Tarkov")
    @check_query_method
    async def ammo(self, ctx, query=None, priority=None, *args, **kwargs):
        """
        Available queries: <caliber>, <name>, grenades, tracer
        Available sorting: damage, penetration, accuracy, recoil.

        Args:
            ctx:
            query:
            priority:
            *args:
            **kwargs:

        Returns:

        """
        if not query:
            calibers = pd.read_csv(os.path.join(self.eft_dir, "ammo.csv"), dtype=str)["Caliber"].unique()
            await ctx.send(f"Tell me **caliber ** or ammo **name**, example !ammo 5.56. \n"
                           f"Available calibers:\n"
                           f"{', '.join(f'`{ob}`' for ob in calibers)}")
            await ctx.message.delete()
            return None

        query = query.lower()

        if priority:
            priority = priority.lower()

        if "gran" in query:
            await ctx.message.author.send("Correct spelling is `Gr`**`E`**`nade`")
            query = "gren"

        if "gren" in query or "bar" in query or 'unde' in query:
            granade_df = pd.read_csv(os.path.join(self.eft_dir, "grenade_ammo.csv"), dtype=str)
            embed = self.create_embed_grenade(granade_df, priority="Damage")

        else:
            ammo_df = pd.read_csv(os.path.join(self.eft_dir, "ammo.csv")).round(2)

            if "trac" in query:
                ammo_df = ammo_df[ammo_df['Tracer'] == "Yes"]
            elif "all" in query:
                pass
            else:
                if query == "45" or query == ".45":
                    ammo_df = ammo_df[ammo_df["Caliber"] == ".45"]
                else:
                    ammo_df = ammo_df[
                        ammo_df["Caliber"].str.contains(query.lower()) |
                        ammo_df["Name"].str.contains(query.title())
                        ]

            embed = self.create_embed_ammo(ammo_df, priority=priority)

        try:
            with open(os.path.join(self.eft_dir, "ammo_version.txt"), "rt") as file:
                version = file.read()
        except FileNotFoundError:
            version = "unkown"

        if not embed:
            await ctx.send("Nothing matching found.")
        else:
            author = bot.get_user(YOUSHISU_ID)
            embed.set_author(name=f"Version: {version}")
            embed.set_footer(text='Made by Youshisu', icon_url=author.avatar_url)
            await ctx.send(embed=embed)
            await send_approve(ctx)

    def create_embed_ammo(self, data, priority=None):
        spread_sheet_url = r"https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#"
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

        embed.add_field(name="Sorted by", value=sort_text, inline=True)
        embed.add_field(name="Compared bullets", value=str(len(data)), inline=True)
        for key in keys[2:]:
            if not key:
                continue
            row_arr = list(data[key])
            row_text = joiner.join(str(ob).ljust(ammo_txtlen) for ob in row_arr)
            embed.add_field(name=key, value=f"`{row_text}`", inline=False)

        return embed

    def create_embed_grenade(self, data, priority=None):
        spread_sheet_url = r"https://docs.google.com/spreadsheets/d/1_l-gYeSt2MqIw62EdMZt_wefG0yO9L7dTaRM74c2J1w/htmlview#"
        ammo_txtlen = 5
        col = Colour.from_rgb(30, 129, 220)

        joiner = " | "
        keys = data.columns
        data = data.copy()
        if len(data) < 1:
            return None

        data = data.sort_values(['Damage'], ascending=False)

        embed = Embed(title=f'Under-barrel grenades', color=col,
                      description=f"[Ammo chart link]({spread_sheet_url})")

        for key in keys[1:]:
            if not key:
                continue
            row_arr = list(data[key])
            row_text = joiner.join(str(ob).ljust(ammo_txtlen) for ob in row_arr)
            embed.add_field(name=key, value=f"`{row_text}`", inline=False)

        return embed
