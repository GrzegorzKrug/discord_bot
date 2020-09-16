from discord.ext.commands import Bot, CommandError, Cog, command
from .permissions import *
from .decorators import *
from .definitions import bot, my_help


class CogTest(Cog):
    def __init__(self):
        self.bot = bot

    @command()
    @advanced_perm_check_method(bot)
    @my_help.help_decorator("cog1 test")
    async def cog1(self, ctx, *args, text=None, **kwargs):
        print("Cog1")
        await ctx.send(f"txt: {text}")
