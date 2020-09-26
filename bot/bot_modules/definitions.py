from discord.ext.commands import Bot
from .loggers import define_logger
from discord import Colour


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
my_help.add_menu("Bot", "About bot")
my_help.add_menu("Role", "Manage roles")
my_help.add_menu("Chat", "Global Chat")
my_help.add_menu("Moderation", "Delete messages")
my_help.add_menu("Fun", "Have fun")
my_help.add_menu("Tarkov", "Tarkov related commands")
my_help.add_menu("Rest", "No category")

bot = Bot(command_prefix='!', case_insensitive=True, help_command=None)
EMOJIS = {
        1: '1️⃣',
        2: '2️⃣',
        3: '3️⃣',
        4: '4️⃣',
        5: '5️⃣',
        6: '6️⃣',
        7: '7️⃣',
        8: '8️⃣',
        9: '9️⃣',
        10: '🔟',
        'green_x': "❎",
        "green_ok": "✅",
        'arrow_left': "⬅️",
        'arrow_right': "➡️",
        'arrow_back_left': "↩️",
        "thinking": "🤔",
        "question": "❓",
        "red_x": "❌",
        "blocked": "⛔",

}

HAPPY_FACES = ["😀", "🙂", "😌", "😍", "🥰", "😜", "😊", "😎", "🤠", "🤗", "🤩", "🥳", "😉", "🤪", "😋", "😛"]
DISRTUBED_FACES = ["😒", "😞", "😔", "🧐", "😕", "😫", "😩", "🥺", "😤", "😠", "😳", "🤔", "🤫", "😟"]

ROLE_COLORS = {'Blue': (50, 150, 255),
               'LtBlue': (80, 180, 255),
               'Cyan': (0, 255, 255),
               'Green': (0, 255, 0),
               'Camo': (50, 180, 90),
               'Neon': (180, 255, 50),
               'Gold': (255, 240, 100),
               'Yellow': (255, 255, 0),
               'Orange': (255, 150, 0),
               'Pink': (255, 150, 255),
               'Rose': (255, 70, 150),
               'BlackBerry': (160, 50, 100),
               'Purple': (230, 0, 200),
               'Red': (255, 0, 0),
               'Black': (1, 1, 1),
               'Gray': (150, 160, 170),
               'White': (255, 255, 255),

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

GLOBAL_SERVERS = {755065402777796663}
YOUSHISU_ID = 147795752943353856
BOT_URL = r"https://discord.com/api/oauth2/authorize?client_id=750688123008319628&permissions=470019283&scope=bot"
BOT_TEST_URL = r"https://discord.com/api/oauth2/authorize?client_id=757339370368794696&permissions=470019283&scope=bot"
BOT_COLOR = Colour.from_rgb(30, 255, 0)


async def send_approve(ctx):
    await ctx.message.add_reaction('✅')


async def send_disapprove(ctx):
    await ctx.message.add_reaction('❌')


logger = define_logger("Bot", path='..', file_lvl="INFO", stream_lvl="DEBUG", extra_debug="Debug.log")
messenger = define_logger("Messenger", path='..', file_lvl="INFO", combined=False, date_in_file=True)
feedback = define_logger("Feedback", path='..', file_lvl="INFO", combined=False, date_in_file=False)
