from discord.ext.commands import Bot
from discord import Colour

from .loggers import define_logger
from .emojis import *

import shelve
import os

logger = define_logger("Bot", path='..', file_lvl="INFO", stream_lvl="DEBUG", extra_debug="Debug.log")
messenger = define_logger("Messenger", path='..', file_lvl="INFO", combined=False, date_in_file=True)
feedback = define_logger("Feedback", path='..', file_lvl="INFO", combined=False, date_in_file=False)


class Help:
    def __init__(self):
        self.temp_help_arr = []
        self.help_dict = {}
        self.alias_dict = {}
        self.menus = {}
        self.menus_desc = {}

    def create_help(self):
        """
        self.temp_help_arr is list of tuples
        Returns:

        """
        help_dict = {}
        alias_dict = {}
        menu_dict = self.menus.copy()
        for object in self.temp_help_arr:
            for key, simple, example, full, aliases, menu in object:
                menu = menu.lower()
                key = key.lower()

                if key in menu_dict or key in menu or menu in help_dict:
                    logger.error(f"Duplicated help, key {key} or menu {menu}")

                if menu not in menu_dict:
                    menu_dict.update({menu: [key]})

                else:
                    items = menu_dict[menu] + [key]
                    menu_dict.update({menu: items})

                help_dict.update({
                        key: {
                                "simple": simple,
                                "example": f"!{key} {example}",
                                "full": full,
                                "aliases": aliases,
                                "menu": menu,
                        }
                })

                if aliases:
                    for alias in aliases:
                        alias = alias.lower()
                        alias_dict.update({alias: {"simple": simple, "example": f"!{alias} {example}", "full": full}})

        # help_dict =

        self.help_dict = help_dict
        self.alias_dict = alias_dict
        self.temp_help_arr = []
        self.menus = menu_dict

    def help_decorator(self, simple, example=None, help_name=None, menu=None, aliases=None):
        _help = []

        def wrapper(coro):
            async def f(*args, **kwargs):
                value = await coro(*args, **kwargs)
                return value

            full_doc = coro.__doc__
            key = help_name if help_name else coro.__name__
            _menu = menu
            _menu = "rest" if not _menu else _menu.lower()

            if example is None:
                _example = ""
            else:
                _example = example

            if aliases:
                _simple = simple + "\n" + f"Aliases:" + ",".join(aliases)
            else:
                _simple = simple

            _help.append((key, _simple, _example, full_doc, aliases, _menu))
            # if aliases:
            #     for alias in aliases:
            #         _help.append((alias, _simple, f"!{alias}", full_doc, aliases))
            f.__name__ = coro.__name__
            f.__doc__ = coro.__doc__

            return f

        self.temp_help_arr.append(_help)
        return wrapper

    def add_menu(self, name, description):
        name = name.lower()
        self.menus_desc.update({name: description})


my_help = Help()

my_help.add_menu("Role", "Manage roles")
my_help.add_menu("Chat", "Global Chat")
my_help.add_menu("Moderation", "Delete messages")
my_help.add_menu("Fun", "Have fun")
my_help.add_menu("Tarkov", "Tarkov related commands")
my_help.add_menu("Rest", "No category")
my_help.add_menu("Bot", "About bot")


class Config:
    def __init__(self):
        self.color_pairs = Pair()
        self.config_dir = os.path.abspath(os.path.join(__file__, '..', '..', 'config'))
        self.clear_config_not_save = False
        os.makedirs(self.config_dir, exist_ok=True)

        self.load()

    def save(self):
        config_file = os.path.join(self.config_dir, "shelf.db")
        if self.clear_config_not_save:
            with shelve.open(config_file, flag="n") as sh:
                pass
        else:
            with shelve.open(config_file, flag="c") as sh:
                sh['color_pairs'] = self.color_pairs
                logger.debug("Config save success")

    def load(self):
        config_file = os.path.join(self.config_dir, "shelf.db")
        try:
            sh = shelve.open(config_file, flag="r")
        except Exception:
            return None
        try:
            color_pairs = sh['color_pairs']
            self.color_pairs = color_pairs
            logger.debug("Config load success")
        except Exception as err:
            logger.error(f"Error when loading config {err}")
            pass

        finally:
            sh.close()

    def add_rolemenu_color_pair(self, new_pair):
        self.color_pairs.add(new_pair)

    def check_if_in_colors(self, id):
        return self.color_pairs.check_if_in(id)


class Pair:
    def __init__(self):
        self.pairs = dict()

    def add(self, new_pair):
        assert len(new_pair) == 2, "New pair should have exactly 2 elements"
        self.pairs.update({new_pair[0]: new_pair[1]})
        self.pairs.update({new_pair[1]: new_pair[0]})

    def get_pair(self, id):
        return id, self.pairs.get(id, None)

    def check_if_in(self, id):
        """
        Checks in which message is pair
        Args:
            id:

        Returns:

        """
        return id in self.pairs

    def __str__(self):
        return str(self.pairs.items())


my_config = Config()

bot = Bot(command_prefix='!', case_insensitive=True, help_command=None)
ROLE_COLORS = {
        'Lavender': {'color': (200, 150, 255), 'emoji': EMOJIS['purple_heart']},
        'Purple': {'color': (220, 0, 250), 'emoji': EMOJIS['grapes']},
        'Violet': {'color': (160, 0, 255), 'emoji': EMOJIS['eggplant']},
        'DarkBlue': {'color': (50, 100, 200), 'emoji': EMOJIS['whale2']},
        'Blue': {'color': (50, 150, 255), 'emoji': EMOJIS['blue_heart']},
        'LtBlue': {'color': (120, 180, 255), 'emoji': EMOJIS['fish']},
        'Cyan': {'color': (0, 255, 255), 'emoji': EMOJIS['butterfly']},

        'LtGreen': {'color': (110, 255, 100), 'emoji': EMOJIS['sauropod']},
        'Green': {'color': (0, 255, 0), 'emoji': EMOJIS['green_heart']},
        'Camo': {'color': (50, 180, 90), 'emoji': EMOJIS['crocodile']},
        'Neon': {'color': (150, 255, 30), 'emoji': EMOJIS['parrot']},

        'LemonGrass': {'color': (215, 255, 100), 'emoji': EMOJIS['dragon']},
        'LtYellow': {'color': (255, 240, 100), 'emoji': EMOJIS['banana']},
        'Yellow': {'color': (255, 255, 0), 'emoji': EMOJIS['yellow_heart']},
        'Gold': {'color': (241, 196, 15), 'emoji': EMOJIS['cheese']},
        'Orange': {'color': (255, 150, 0), 'emoji': EMOJIS['orange_heart']},

        'LtRed': {'color': (255, 80, 80), 'emoji': EMOJIS['tulip']},
        'Red': {'color': (255, 0, 0), 'emoji': EMOJIS['heart']},
        'Rose': {'color': (255, 70, 150), 'emoji': EMOJIS['rose']},
        'Pink': {'color': (255, 150, 235), 'emoji': EMOJIS['hibiscus']},

        'Maroon': {'color': (170, 0, 50), 'emoji': EMOJIS['maple_leaf']},
        'BlackBerry': {'color': (150, 30, 130), 'emoji': EMOJIS['fleur_de_lis']},

        'Black': {'color': (1, 1, 1), 'emoji': EMOJIS['black_heart']},
        'Gray': {'color': (150, 160, 170), 'emoji': EMOJIS['wolf']},
        'White': {'color': (255, 255, 255), 'emoji': EMOJIS['swan']},
}

SPECIAL_ROLE_COLORS = {
        'Invisible': (50, 50, 60),
}

RUDE = ['Why you bother me {0}? {emote}',
        'Stop it {0}. {emote}',
        'No {emote}, I do not like that {0}.',
        "Do not ping me {0}. {emote}",
        "Use commands if you need something {0}. {emote}",
        "Staph it. Get some help {0}. {emote}"]

GLOBAL_SERVERS = {}
YOUSHISU_ID = 147795752943353856

SYSTEM_CHANNEL = 759782856980824094
FEEDBACK_CHANNAEL = 759782801792434237

BOT_URL = r"https://discord.com/api/oauth2/authorize?client_id=750688123008319628&permissions=470019283&scope=bot"
BOT_TEST_URL = r"https://discord.com/api/oauth2/authorize?client_id=757339370368794696&permissions=470019283&scope=bot"
BOT_COLOR = Colour.from_rgb(30, 255, 0)


async def send_approve(ctx):
    await ctx.message.add_reaction('✅')


async def send_disapprove(ctx):
    await ctx.message.add_reaction('❌')
