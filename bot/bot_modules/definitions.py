from discord.ext.commands import Bot


class Help:
    def __init__(self):
        self.temp_help_arr = []
        self.help_dict = {}

    def create_help_dict(self):
        help_dict = {key: {"simple": simple, "example": example, "full": full_doc}
                     for command_ob in self.temp_help_arr for key, simple, example, full_doc in command_ob}
        self.help_dict = help_dict
        self.temp_help_arr = []

    def help_decorator(self, simple, example=None):
        _help = []

        def wrapper(function):
            async def f(*args, **kwargs):
                value = await function(*args, **kwargs)
                return value

            if example is None:
                _example = f"!{function.__name__}"
            else:
                _example = example
            full_doc = function.__doc__
            _help.append((function.__name__, simple, _example, full_doc))
            f.__name__ = function.__name__
            f.__doc__ = function.__doc__

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
        '10': '🔟'
}
RUDE = ['Why you bother me {0} ?!', 'Stop it {0}!', 'No, I do not like that {0}.', "Go away {0}."]
GLOBAL_SERVERS = {755063230300160030, 755065402777796663, 755083175491010590}
YOUSHISU_ID = 147795752943353856
BOT_URL = r"https://discord.com/api/oauth2/authorize?client_id=750688123008319628&permissions=470019283&scope=bot"
