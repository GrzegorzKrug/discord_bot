from discord.ext.commands import Bot
from .loggers import define_logger
from discord import Colour


class Help:
    def __init__(self):
        self.temp_help_arr = []
        self.help_dict = {}
        self.alias_dict = {}

    def create_help_dict(self):
        """
        self.temp_help_arr is list of tuples
        Returns:

        """
        help_dict = {}
        alias_dict = {}
        for object in self.temp_help_arr:
            for key, simple, example, full, aliases in object:
                help_dict.update({key: {"simple": simple, "example": example, "full": full, "aliases": aliases}})

                if aliases:
                    for alias in aliases:
                        alias_dict.update({alias: {"simple": simple, "example": example, "full": full}})

        # help_dict =

        self.help_dict = help_dict
        self.alias_dict = alias_dict
        self.temp_help_arr = []

    def help_decorator(self, simple, example=None, help_name=None, aliases=None):
        _help = []

        def wrapper(coro):
            async def f(*args, **kwargs):
                value = await coro(*args, **kwargs)
                return value

            if example is None:
                _example = f"!{coro.__name__}"
            else:
                _example = example

            if aliases:
                _simple = simple + "\n" + f"Aliases:" + ",".join(aliases)
            else:
                _simple = simple

            full_doc = coro.__doc__
            key = help_name if help_name else coro.__name__

            _help.append((key, _simple, _example, full_doc, aliases))
            # if aliases:
            #     for alias in aliases:
            #         _help.append((alias, _simple, f"!{alias}", full_doc, aliases))
            f.__name__ = coro.__name__
            f.__doc__ = coro.__doc__

            return f

        self.temp_help_arr.append(_help)
        return wrapper


my_help = Help()
bot = Bot(command_prefix='!', case_insensitive=True, help_command=None)
EMOJIS = {
        '1': '1️⃣',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣',
        '10': '🔟',
        'green_x': "❎",
        'arrow_left': "⬅️",
        'arrow_right': "➡️",
        'arrow_back_left': "↩️",
}
RUDE = ['Why you bother me {0} ?!', 'Stop it {0}!', 'No, I do not like that {0}.', "Go away {0}."]
GLOBAL_SERVERS = {755063230300160030, 755065402777796663, 755083175491010590}
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
