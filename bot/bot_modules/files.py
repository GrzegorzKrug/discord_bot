import asyncio
import glob
import sys
import os

from .definitions import *
from .permissions import *
from .decorators import *

from discord import File


@bot.command(aliases=['log'])
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_bot_owner)
@log_call_function
@approve_fun
async def logs(ctx, action=None, val=None, *args, **kwargs):
    user = bot.get_user(YOUSHISU_ID)
    log_dir = os.path.abspath(
            os.path.join(__file__, "..", "..", "..", "logs")
    )
    all_files = glob.glob(log_dir + os.path.sep + "*.log", recursive=True)
    if not action or type(action) is str and action.lower() == "show":
        "Show log list"

        if val:
            files = [file for file in all_files if val.lower() in os.path.basename(file).lower()]
        else:
            files = all_files

        text = "\n".join(f"`{num:<4}` "
                         f"`{os.stat(file).st_size / 1024 / 1024:>5.2f} MB `"
                         f"{os.path.basename(file)}" for num, file in
                         enumerate(files))
        if text:
            await user.send(text)
        else:
            await user.send("No log files available yet.")
        return None

    elif type(action) is str and action.lower() == "send":
        "Show log list"
        if val:
            files = [file for file in all_files if val.lower() in os.path.basename(file).lower()]
        else:
            files = all_files

        for file in files:
            try:
                f = File(file, filename=os.path.basename(file))
                await user.send(file=f)
            except FileNotFoundError as er:
                await user.send(f"File not found: {er}")

    elif type(action) is str and action.lower() == "clear":
        "Delete log files with confirmation"

        if val == "old":
            files = all_files
            raise NotImplementedError

        elif val == "all":
            files = all_files
            raise NotImplementedError
        else:
            await user.send("Select old or all")
            return None

        message = await user.send(f"Please confirm delete of {len(files)} logs files.")
        await message.add_reaction(EMOJIS["green_ok"])

        def confirm_delete(reaction, _u):
            return str(reaction.emoji) == EMOJIS['green_ok'] and message.id == reaction.message.id and _u.id == user.id

        try:
            reaction, user = await bot.wait_for("reaction_add", check=confirm_delete, timeout=60)
        except asyncio.TimeoutError:
            await user.send("No confirmation in time")
            return None

        count = 0
        for file in files:
            try:
                os.remove(file)
                count += 1
            except Exception as err:
                await user.send(f"During delete of {file}, exception occurred: {err}")

        await user.send(f"Deleted {count} log files")
