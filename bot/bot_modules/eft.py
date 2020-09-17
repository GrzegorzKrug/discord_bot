from discord.ext.commands import  Cog, command
from .permissions import *
from .decorators import *
from .definitions import bot, my_help


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

    @command()
    @advanced_perm_check_method(is_bot_owner)
    @log_call_method
    async def ammo(self, ctx, *args, **kwargs):
        pass
