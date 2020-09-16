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
