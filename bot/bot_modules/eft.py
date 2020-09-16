from .decorators import *
from .permissions import *

from discord.ext.commands import Bot, CommandError, Cog, command


class CogTest(Cog):
    def __init__(self, bot):
        self.bot = bot
        # self._last_member = None

    @command()
    async def cog0(self, ctx):
        print("Cog0")
        pass

    @command()
    @advanced_perm_check_method()
    async def cog1(self, ctx, *args, **kwargs):
        print("Cog1")
        pass

    @command()
    @advanced_perm_check_function()
    async def cog2(self, ctx, *args, **kwargs):
        print("Cog2")
        pass

    @command()
    @advanced_args_method()
    async def cog3(self, ctx, *args, **kwargs):
        print("Cog3")
        pass

    @command()
    @advanced_args_function()
    async def cog4(self, ctx, *args, **kwargs):
        print("Cog4")
        pass
