from discord.ext.commands import Bot
from discord import Colour

from .loggers import define_logger
from .emojis import *

import os

production = bool(os.getenv('PRODUCTION', None))

if production:
    logger = define_logger("Bot", path='..', file_lvl="INFO", stream_lvl="DEBUG")
else:
    logger = define_logger("Bot", path='..', file_lvl="INFO", stream_lvl="DEBUG", extra_debug="Debug.log")

messenger = define_logger("Messenger", path='..', file_lvl="INFO", combined=False, date_in_file=True)
feedback = define_logger("Feedback", path='..', file_lvl="INFO", combined=False, date_in_file=False)

bot = Bot(command_prefix='!', case_insensitive=True, help_command=None)


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
            for key, simple, example, full, aliases, menu, actions in object:
                menu = menu.lower()
                key = key.lower()

                if key in menu_dict or key in menu or menu in help_dict:
                    logger.error(f"Duplicated help, key {key} or menu {menu}")

                if menu not in menu_dict:
                    menu_dict.update({menu: [key]})

                else:
                    items = menu_dict[menu] + [key]
                    menu_dict.update({menu: items})

                if actions:
                    _example = "action"
                else:
                    _example = example

                help_dict.update({
                        key: {
                                "simple": simple,
                                "example": f"!{key} {_example}",
                                "full": full,
                                "aliases": aliases,
                                "menu": menu,
                                "actions": actions,
                        }
                })

                if aliases:
                    for alias in aliases:
                        _aliases = set(aliases.copy())
                        _aliases.add(key)
                        _aliases.remove(alias)
                        # logger.debug(f"Adding aliases: {_aliases}")
                        alias = alias.lower()
                        alias_dict.update({
                                alias: {
                                        "simple": simple,
                                        "example": f"!{alias} {_example}",
                                        "full": full,
                                        "actions": actions,
                                        "aliases": _aliases,
                                        "menu": menu,
                                }
                        })

        # help_dict =

        self.help_dict = help_dict
        self.alias_dict = alias_dict
        self.temp_help_arr = []
        self.menus = menu_dict
        logger.debug(help_dict)

    def help_decorator(self, simple, example=None, help_name=None, menu=None, aliases=None, actions=None):
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

            # if aliases:
            #     _simple = simple + "\n" + f"Aliases:" + ",".join(aliases)
            # else:
            #     _simple = simple

            _help.append((key, simple, _example, full_doc, aliases, _menu, actions))
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

ROLE_COLORS = {
        'Lavender': {'color': (200, 150, 255), 'emoji': EMOJIS['purple_heart']},
        'Purple': {'color': (220, 0, 250), 'emoji': EMOJIS['grapes']},
        'Violet': {'color': (160, 0, 255), 'emoji': EMOJIS['eggplant']},
        'BlackBerry': {'color': (150, 30, 130), 'emoji': EMOJIS['fleur_de_lis']},
        'DarkBlue': {'color': (50, 100, 200), 'emoji': EMOJIS['whale2']},
        'Blue': {'color': (0, 70, 255), 'emoji': EMOJIS['blue_heart']},
        'LtBlue': {'color': (60, 200, 255), 'emoji': EMOJIS['fish']},
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

        'Pink': {'color': (255, 150, 235), 'emoji': EMOJIS['hibiscus']},
        'Rose': {'color': (255, 70, 150), 'emoji': EMOJIS['rose']},    
        'LtRed': {'color': (255, 80, 80), 'emoji': EMOJIS['tulip']},
        'Red': {'color': (255, 0, 0), 'emoji': EMOJIS['heart']},               
        'Maroon': {'color': (170, 0, 50), 'emoji': EMOJIS['maple_leaf']},            

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
