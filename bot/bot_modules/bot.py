import numpy as np
import traceback
import requests
import asyncio
import random
import scipy
import time
import cv2
import sys
import os
import re

from discord.ext import tasks
from discord import Activity, ActivityType, Status, Embed, Colour

from .decorators import *
from .permissions import *
from .definitions import *

from .roles import *
from .eft import EFTCog


@bot.command(aliases=["invite_bot", "invite_me", 'join'])
@advanced_args_function(bot)
@log_call_function
@my_help.help_decorator("Generate bot invitation", "priv or mentions", menu='bot')
async def invite(ctx, *args, **kwargs):
    embed = Embed(title=f"Invite me!", url=BOT_URL)
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    embed.add_field(name="About", value=f"This bot is awesome")
    embed.set_thumbnail(url=bot.user.avatar_url)

    success = 0
    if "priv" in args or not ctx.message.guild:
        await ctx.author.send(f"Here is my invitation:", embed=embed)

        if ctx.message.guild:
            await ctx.send(f"✅ Invite sent to {ctx.author.mention}.")

    elif ctx.message.mentions or args:
        await ctx.message.add_reaction("⏳")

        args = list(set(args))
        for user in ctx.message.mentions:
            try:
                await user.send(f"Here is my invitation:", embed=embed)
                success += 1
            except Exception as err:
                logger.warning(f"Error during invite. To {user}: {err}")
                pass

        for user_id in args:
            try:
                user = bot.get_user(int(user_id))
                if user:
                    await user.send(f"Here is my invitation:", embed=embed)
                    success += 1
            except ValueError:
                pass

            except Exception as err:
                logger.warning(f"Error during invite. To {user_id}: {err}")
                pass

        await ctx.message.add_reaction("✅")
        await ctx.message.clear_reaction("⏳")
        await ctx.send(f"Invite sent to {success} user{'s' if success > 1 else ''}.")
    else:
        await ctx.send(f"Here is my invitation:", embed=embed)


@bot.command(aliases=["bot"])
@log_call_function
@my_help.help_decorator("General bot information", menu="Bot")
async def about(ctx):
    embed = Embed(title=f"Invite me!", url=BOT_URL)
    embed.set_author(name=f"{bot.user.name}", icon_url=bot.user.avatar_url)
    embed.add_field(name="Me", value=f"I am awesome, and got plenty of features", inline=False)
    embed.add_field(name="Customize", value=f"You are free to customise bot", inline=False)
    embed.add_field(name="Global-chat", value=f"Use this bot speak with different servers", inline=False)
    embed.add_field(name="!help", value=f"Get help menu", inline=False)
    embed.add_field(name="Current servers", value=f"{len(bot.guilds)}", inline=False)
    embed.set_thumbnail(url=bot.user.avatar_url)

    autor = bot.get_user(YOUSHISU_ID)
    embed.set_footer(text="Dev: Youshisu", icon_url=autor.avatar_url)

    await ctx.send(embed=embed)


@bot.command(aliases=['server', 'on', 'where'])
@log_call_function
@my_help.help_decorator("Servers that bot is connected to", menu="Bot")
async def servers(ctx, *args, **kwargs):
    """
    Send embed message, showing which servers are using this bot.
    Args:
        ctx:

    Returns:

    """
    servers = [(sv.name, len(sv.members), len(get_list_non_offline_members(sv.members)))
               for sv in bot.guilds]
    servers.sort(key=lambda x: (x[1], x[2]), reverse=True)
    description = f"\n".join(
            f"`{name:<25}: online: {online:<5}, all: {all_mem:<5}`" for name, all_mem, online in servers)

    embed = Embed(title=f"Invite me!", description=description, url=BOT_URL)
    embed.set_author(name=f"I am on {len(servers)} servers")
    embed.set_thumbnail(url=bot.user.avatar_url)
    autor = bot.get_user(YOUSHISU_ID)
    embed.set_footer(text="Dev: Youshisu", icon_url=autor.avatar_url)

    await ctx.send(embed=embed)


def world_wide_format(message, msg_type=None):
    """
    Format message by selection.

    Args:
        msg_type: string
            Up to 2000 characters:
                plain - text only
                tiny - icon and text
                compact - icon, text, name
                thick - text, title, footer, thumbnail

            Up to 1024 characters:
                field - field, text, thumbnail
                field_ft - field, text, footer, thumbnail

            Up to 256 characters:
                short - text, title, footer, thumbnail
                big_short - icon, text, title, footer, thumbnail

    Returns:

    """

    col = Colour.from_rgb(60, 150, 255)

    if not msg_type or msg_type not in ['plain', 'tiny', 'compact', "normal",
                                        'short', 'big_short', 'thick',
                                        'code', 'code_big']:
        msg_type = "normal"

    if msg_type == "plain":
        text = f"**{message.author.name}**: {message.content}"
        embed = None

    elif msg_type == "tiny":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=False)
        embed = Embed(colour=col)
        embed.set_footer(text=f"{message.author.name}: {message.content}", icon_url=message.author.avatar_url)
        text = None

    elif msg_type == "compact":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=False)
        embed = Embed(colour=col)
        embed.set_author(name=f"{message.author.name}:", icon_url=message.author.avatar_url)
        embed.set_footer(text=f"{message.content}")
        text = None

    elif msg_type == "normal":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=False)
        embed = Embed(colour=col, description=message.content)
        embed.set_author(name=f"{message.author.name}:", icon_url=message.author.avatar_url)
        # embed.set_footer(text=f"{message.content}")
        text = None

    elif msg_type == "short":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=True)
        embed = Embed(title=f"{message.content}", colour=col)
        embed.set_author(name=f"{message.author.name}:")
        embed.set_thumbnail(url=message.author.avatar_url)
        text = None

    elif msg_type == "big_short":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=True)
        embed = Embed(title=message.content, colour=col)
        embed.set_author(name=f"{message.author.name}:")
        embed.set_thumbnail(url=message.author.avatar_url)
        embed.set_footer(text=f"{message.guild.name}", icon_url=str(message.guild.icon_url))
        text = None

    elif msg_type == "thick":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=False)
        embed = Embed(title=f"{message.author.name}:", colour=col)
        embed.set_author(name=f"{message.guild.name}", icon_url=message.guild.icon_url)
        embed.set_footer(text=f"{message.content}")
        embed.set_thumbnail(url=message.author.avatar_url)
        text = None

    elif msg_type == "code":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=True)
        embed = Embed(colour=col, description=message.content)
        embed.set_author(name=f"{message.author.name}:", icon_url=message.author.avatar_url)
        embed.set_footer(text=f"{message.guild.name}", icon_url=str(message.guild.icon_url))
        # embed.set_thumbnail(url=message.author.avatar_url)
        text = None

    elif msg_type == "code_big":
        message.content = string_mention_converter(bot, message.guild, message.content, bold_name=True)
        embed = Embed(colour=col, description=message.content)
        embed.set_author(name=f"{message.author.name}:")
        embed.set_footer(text=f"{message.guild.name}", icon_url=str(message.guild.icon_url))
        embed.set_thumbnail(url=message.author.avatar_url)
        text = None

    elif msg_type == "custom":
        raise NotImplementedError

    else:
        raise ValueError(f"Wrong world wide message type {msg_type}")

    return text, embed


@bot.command()
@advanced_args_function(bot)
@log_call_function
@my_help.help_decorator("Show global messages examples", menu="chat")
@advanced_perm_check_function(is_bot_owner, is_server_owner)
async def global_examples(ctx, *args, **kwargs):
    """
Examples used in global chat. Default 'field'

msg_type: string
    Up to 2000 characters:
    plain: text only
    tiny: icon and text
    compact: icon, text, name
    thick: text, title, footer, picture

    Up to 1024 characters:
    field: field, text, footer, picture

    Up to 256 characters:
    short: text, title, footer, picture
    big_short: icon, text, title, footer, picture

Returns:

    """

    just_text = """Hello there, this is an example showing all messages"""
    code_text = """```py
            try:
                text, embed = world_wide_format(ctx.message, "field")
                await ctx.send("field", embed=embed)
            except Exception as err:
                await ctx.send(str(err))
        ```"""

    message = ctx.message
    message.author = bot.get_user(147795752943353856)

    message.content = "This is limited to 2000 characters. Supports syntax highlights." + code_text
    try:
        await ctx.send("plain")
        text, embed = world_wide_format(ctx.message, "plain")
        await ctx.send(text, embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    message.content = "This is limited to 2000 characters. " + just_text
    try:
        text, embed = world_wide_format(ctx.message, "tiny")
        await ctx.send("tiny", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    try:
        text, embed = world_wide_format(ctx.message, "compact")
        await ctx.send("compact", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    try:
        text, embed = world_wide_format(ctx.message, "thick")
        await ctx.send("thick", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    message.content = "This is limited to 2000 characters. Supports syntax highlights." + code_text
    try:
        text, embed = world_wide_format(ctx.message, "normal")
        await ctx.send("normal", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    try:
        text, embed = world_wide_format(ctx.message, "code")
        await ctx.send("code", embed=embed)
    except Exception as err:
        await ctx.send(str(err))
    try:
        text, embed = world_wide_format(ctx.message, "code_big")
        await ctx.send("code_big", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    message.content = just_text + "\n This is limited to 254 characters"
    try:
        text, embed = world_wide_format(ctx.message, "short")
        await ctx.send("short", embed=embed)
    except Exception as err:
        await ctx.send(str(err))

    try:
        text, embed = world_wide_format(ctx.message, "big_short")
        await ctx.send("big_short", embed=embed)
    except Exception as err:
        await ctx.send(str(err))


@bot.event
async def on_message(message):
    if not message.guild:
        recipient = message.channel.recipient.name
        if message.author.id != bot.user.id:
            messenger.info(f"(priv) {message.author} to Me: {message.content}")

    if message.author.bot:
        return None

    logger.warning(f"Prefix in on_message is constant")
    if bot.user in message.mentions and not message.content.startswith("!"):
        ch = message.channel
        text = random.choice(RUDE)
        emote = random.choice(DISRTUBED_FACES)

        await ch.send(text.format(message.author.name, emote=emote))

    servers = GLOBAL_SERVERS.copy()
    if not message.content.startswith("!") and message.channel.id in servers:
        logger.warning(f"Fixed worldwide chat")
        messenger.info(
                f"world_wide message:\n"
                f"{message.author}  from chid: {message.channel.id}, {message.guild}\n"
                f"'{message.content}'")
        servers.remove(message.channel.id)
        text, embed = world_wide_format(message, msg_type="normal")
        await _announcement(chids=servers, text=text, embed=embed)
        return None

    else:
        await bot.process_commands(message)


@bot.event
async def on_ready():
    act = Activity(type=ActivityType.watching, name=" if you need !help")
    await bot.change_presence(status=Status.idle)
    await _announcement([755715591339376662], "✅ Hey, i'm now online.")
    await bot.change_presence(activity=act, status=Status.online)
    logger.warning(f"On ready announcement is constant")
    logger.info(f"Going online as {bot.user.name}")


@bot.event
async def close():
    act = Activity(name=" to nothing", type=ActivityType.listening)
    await bot.change_presence(activity=act, status=Status.do_not_disturb)
    await _announcement([755715591339376662], "💤 Sorry, I am going offline.")

    await bot.change_presence(activity=None, status=Status.offline)

    logger.warning(f"close announcement is constant")
    logger.info(f"Going offline")


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(this_is_disabled, restrictions=is_bot_owner)
async def announce(ctx, *args, **kwargs):
    raise NotImplementedError


async def _announcement(chids=None, text=None, embed=None):
    for ch in chids:
        try:
            channel = bot.get_channel(ch)
            await channel.send(text, embed=embed)
            await asyncio.sleep(0.01)
        except Exception:
            logger.error(f"Error in annoucment: {channel} {channel.guild}")


@bot.event
async def on_command_error(ctx, command_error):
    text = ctx.message.content
    invoked = ctx.invoked_with
    text_error = str(command_error)
    server = "private_message" if not ctx.guild else f"{ctx.guild} ({ctx.guild.id})"
    logger.warning(f"Bot is always telling about restricted command")
    logger.warning(f"Bot is always telling about no permission")
    logger.warning(f"Bot is using ! as static prefix in errors")

    if text_error.startswith("The check functions for command") or text_error.startswith("No permission"):
        logger.warning(f"No permission: '{text}', server: '{server}'")
        emoji = "⛔"
        await ctx.channel.send(f"Some permissions do not allow it to run here '!{invoked}'")

    elif text_error.endswith("is not found"):
        logger.warning(f"Command not found: '{text}', server: '{server}'")
        emoji = "❓"

    elif text_error.startswith("Command raised an exception: RestrictedError"):
        logger.warning(f"Restricted usage: '{text}', server: '{server}'")
        emoji = "⛔"
        await ctx.channel.send(f"{command_error.original} '!{invoked}'")

    elif text_error.startswith("Command raised an exception: CommandWithoutPermissions"):
        logger.error(f"Command is free to all users: '{text}', server: '{server}'")
        emoji = "⛔"
        await ctx.channel.send(f"Command is not checking any permissions, sorry. '!{invoked}'")

    elif text_error.startswith("You are missing"):
        logger.warning(f"Missing permission: '{text_error}', server: '{server}'")
        emoji = "❌"
        await ctx.channel.send(f"{text_error} '!{invoked}'")

    elif "required positional argument" in text_error:
        emoji = "❌"
        await ctx.channel.send(f"Some arguments are missing: '{command_error.original}'")

    else:
        tb_text = traceback.format_exception(type(command_error), command_error, command_error.__traceback__)
        tb_text = ''.join([line for line in tb_text if f'bot{os.path.sep}' in line or f'app{os.path.sep}' in line])
        emoji = "❌"
        logger.error(
                f"No reaction for this error type:\n"
                f"Command: '{ctx.message.content}', server: '{server}', \n"
                f"'{command_error}'\n"
                f"Partial traceback:\n{tb_text}")

    try:
        await ctx.message.add_reaction(emoji=emoji)
    except Exception:
        pass


@bot.event
async def on_member_join(member):
    logger.info(f"{member} has joined {member.guild} ({member.guild.id})")

    color = Colour.from_rgb(10, 180, 50)
    embed = Embed(colour=color)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name=f"Hello, {member.name}", value=f"This server has now {len(member.guild.members)} members")
    await member.guild.system_channel.send(f"Hello {member.mention}", embed=embed)


@bot.event
async def on_member_remove(member):
    logger.info(f"{member} has left {member.guild} ({member.guild.id})")

    color = Colour.from_rgb(10, 180, 50)
    embed = Embed(colour=color)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name=f"Bye, {member.name}", value=f"This server has now {len(member.guild.members)} members")
    await member.guild.system_channel.send(f"Bye {member.mention}", embed=embed)


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_not_priv)
@log_call_function
@my_help.help_decorator("You can check how many users is on server", menu="Bot")
async def status(ctx, *args, **kwargs):
    # member = random.choice(ctx.guild.members)
    color = Colour.from_rgb(10, 180, 50)
    embed = Embed(title=f"It's {ctx.guild.name}", colour=color)

    embed.set_thumbnail(url=ctx.guild.icon_url)
    embed.add_field(name="Members:", value=f"{len(ctx.guild.members)} ")
    embed.add_field(name="Channels:", value=f"{len(ctx.guild.channels)}")

    online = len(get_list_non_offline_members(ctx.guild.members))
    embed.add_field(name="Online:", value=f"{online}")
    await ctx.send(embed=embed)


def get_list_non_offline_members(members):
    return [member for member in members if str(member.status) != 'offline']


@bot.command(aliases=['purge'])
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function([is_server_owner, is_not_priv])
@log_call_function
@my_help.help_decorator("Removes <X> messages", "<amount>", menu="moderation")
async def purge_all(ctx, amount, *args, **kwargs):
    """
    Removes messages in given channel
    Args:
        ctx:
        amount:
        *args:
        **kwargs:

    Returns:

    """
    channel = ctx.channel
    num = int(amount) + 1  # call is additional
    if num >= 1:
        def check_true(m):
            return True

        deleted = await channel.purge(limit=num, check=check_true)
        logger.info(f"Removed {len(deleted)} messages in {ctx.channel}: {ctx.guild}")

        await ctx.send(f"♻️ Removed {len(deleted)} messages", delete_after=10)


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_server_owner, is_not_priv)
@delete_call
@log_call_function
@my_help.help_decorator("Removes user <X> messages", "<user_id> <amount>", menu="Moderation")
async def purge_id(ctx, authorid, amount, *args, **kwargs):
    """
    !purge id amount, removes all messages sent by author,
    Args:
        ctx:
        amount:
        *args:
        **kwargs:

    Returns:

    """
    channel = ctx.channel
    num = int(amount)
    authorid = int(authorid)

    if num >= 1:
        def check_true(m):
            return authorid == m.author.id

        deleted = await channel.purge(limit=num, check=check_true)
        logger.info(f"Removed {len(deleted)} messages in {ctx.channel}: {ctx.guild}")

        await ctx.send(f"♻️ Removed {len(deleted)} messages", delete_after=10)


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_server_owner, is_not_priv)
@delete_call
@my_help.help_decorator("Removes only bot messages", "<amount>", menu="Moderation")
async def purge_bot(ctx, amount, *args, **kwargs):
    channel = ctx.channel
    num = int(amount)

    def is_bot(m):
        return m.author.bot

    if num >= 1:
        deleted = await channel.purge(limit=num, check=is_bot)
        logger.info(f"Removed {len(deleted)} bot messages in {ctx.channel}: {ctx.guild}")
        await ctx.send(f"♻️ Removed {len(deleted)} bot messages", delete_after=10)


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_not_priv)
@my_help.help_decorator("Interactive maze game. No borders on sides. Restart map if needed", "(<height>)", menu="fun")
async def slipper(ctx, dimy=10, dimx=6, *args, **kwargs):
    """

    Args:
        ctx:
        dimy:
        dimx:
        *args:
        **kwargs:

    Returns:

    """
    game_controls = ['⬅️', '➡', '⬆️', '⬇️', '🔁']
    translate = {'⬅️': 'left', '➡': 'right', '⬆️': 'up', '⬇️': 'down', '🔁': 'restart'}
    message = await ctx.send("Let's start the game.")
    game_num = 0
    win = False

    DIMY = int(dimy)
    DIMY = 5 if DIMY < 5 else DIMY

    DIMX = int(dimx)
    DIMX = 3 if DIMX < 3 else DIMX

    while True and game_num < 10:
        game_num += 1
        restart = False
        position = (0, 0)

        win_position = (DIMY - 1, DIMX - 1)
        board_of_string = slipper_empty_board(DIMX, DIMY)

        board_of_string[0:2, 0:2] = 0
        board_of_string[-2:, -2:] = 0

        board_of_string = np.array(board_of_string, dtype='str')
        board_of_string[-1, -1] = "O"

        draw_board = board_of_string.copy()
        draw_board[position] = "x"
        await message.edit(content=board_to_monotext(draw_board, ones='#', zeros='.'))

        for react in game_controls:
            await message.add_reaction(react)
            await asyncio.sleep(0.01)

        def check_reaction(reaction, user):
            return user == ctx.message.author \
                   and str(reaction.emoji) in game_controls \
                   and reaction.message.id == message.id

        moves = 100
        while True and moves > 0:
            await asyncio.sleep(0.01)
            valid_move = False
            win = False
            moves -= 1
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=35, check=check_reaction)
            except asyncio.TimeoutError:
                message.content += f"\nTimeout..."
                break

            await message.remove_reaction(reaction, ctx.message.author)
            move = translate[reaction.emoji]

            if move == 'restart':
                restart = True
                break

            elif move == "left":
                check = (position[0], (position[1] - 1) % DIMX)
                if board_of_string[check] != '1':
                    valid_move = True
            elif move == "right":
                check = (position[0], (position[1] + 1) % DIMX)
                if board_of_string[check] != '1':
                    valid_move = True

            elif move == "up":
                check = ((position[0] - 1), position[1])
                if min(check) >= 0 and max(check) < DIMY and board_of_string[check] != '1':
                    valid_move = True
            elif move == "down":
                check = ((position[0] + 1), position[1])
                if min(check) >= 0 and max(check) < DIMY and board_of_string[check] != '1':
                    valid_move = True
            else:
                logger.error(f"Unknown move in slipper: {move}, {reaction}")

            if valid_move:
                position = check
            else:
                text = f"{message.content}\nThis move is not valid"
                await message.edit(content=text)
                continue

            if position == win_position:
                win = True

            draw_board = board_of_string.copy()
            draw_board[position] = "x"
            await message.edit(content=board_to_monotext(draw_board, ones='#', zeros='.'))

            if win:
                break

        if not restart or win:
            break
    if win:
        game_over = message.content + f"\nCongratulations {ctx.message.author.name}! You have won!"
    else:
        game_over = message.content + f"\nGame over, you lost {ctx.message.author.name}"

    await message.edit(content=game_over)
    if win:
        await message.add_reaction("🏅")
    else:
        await message.add_reaction("🍬")

    for rc in game_controls:
        await message.clear_reaction(rc)


def slipper_empty_board(x=10, y=10):
    area = x * y
    ammount = area // 2.5
    board = [1 if x < ammount else 0 for x in range(area)]
    random.shuffle(board)
    board = np.array(board).reshape(y, x)
    return board


def board_to_monotext(board, el_size=2, distance_between=0,
                      ones='1', zeros='0'):
    temp_board = np.array(board, dtype='str')
    mask0 = board == '0'
    mask1 = board == '1'

    temp_board[mask0] = zeros
    temp_board[mask1] = ones

    text = "\n".join([str(' ' * distance_between).join([f"{num:<{el_size}}" for num in row]) for row in temp_board])
    text = f"```\n{text}\n```"
    return text


@bot.command(aliases=['global'])
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function([is_server_owner, is_not_priv])
@my_help.help_decorator("Command to add/remove channels from global chat", "add|remove",
                        help_name="global",
                        menu="chat")
async def _global(ctx, key=None, *args, **kwargs):
    if type(key) is str and key.lower() == "add":
        GLOBAL_SERVERS.add(ctx.channel.id)
        await ctx.send("Global is now here, temporary till restart.")
    elif type(key) is str and key.lower() == "remove":
        try:
            GLOBAL_SERVERS.remove(ctx.channel.id)
        except ValueError:
            pass
        await ctx.send("Global channel has been removed")


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_server_owner, restrictions=is_not_priv)
async def spam(ctx, num=1, *args, **kwargs):
    num = int(num)
    if num > 100:
        num = 100
    for x in range(num):
        await ctx.channel.send(random.randint(0, num))
        await asyncio.sleep(0.01)


@bot.command()
@delete_call
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_bot_owner)
async def react(ctx, *args, **kwargs):
    message = await ctx.channel.send("React here")
    await message.add_reaction("✅")
    await message.add_reaction("❎")
    await message.add_reaction("♻")
    await message.add_reaction("🚫")
    await message.add_reaction("⛔")
    await asyncio.sleep(0.1)

    def check_reaction(reaction, user):
        print(f"New reaction: {reaction}")
        return user == ctx.message.author and message.id == reaction.message.id and reaction.emoji == "⛔"

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check_reaction, timeout=600)
    except asyncio.TimeoutError:
        pass

    await message.delete()


@bot.command()
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_bot_owner)
@log_duration_any
async def save(ctx, *args, **kwargs):
    """
    Saves avatar in directory
    Args:
        ctx:

    Returns:

    """
    if "all" in args:
        count = 0
        for member in ctx.guild.members:
            try:
                avatar_url = member.avatar_url
                name = member.name
                image = await get_picture(avatar_url)
                save_image(image, f"avatars/{name}.png")
                count += 1

            except Exception as err:
                logger.warning(f"@{member} has probably gif, {err}")

            await asyncio.sleep(0.1)
        text = f"Saved {count} avatars"
        logger.info(text)
        await ctx.send(text)


@bot.command(aliases=['hi', 'helo', 'hey', 'hai'])
@log_call_function
async def hello(ctx, *args):
    pool = ["Hello there {emote} {0}.",
            "How is it going today {0}? {emote}",
            "What's up {0}?", "Hey {0}. {emote}",
            "Hi {0}, do you feel well today? {emote}",
            "Good day {0}. {emote}",
            "Oh {0}! Hello. {emote}",
            "Hey {emote}. {0}"]

    text = random.choice(pool)
    emote = random.choice(HAPPY_FACES)

    await ctx.send(text.format(ctx.message.author.name, emote=emote))


@bot.command(aliases=['h', 'help'])
@advanced_args_function(bot)
@log_call_function
@my_help.help_decorator("Help function", "(cmd) (full)", help_name="help", menu="bot")
async def _help(ctx, cmd_key=None, *args, full=None, perm=None, **kwargs):
    """
    Show embed help. Decorated with buttons.
    Args:
        ctx:
        cmd_key:
        *args:
        full:
        **kwargs:

    Returns:

    """
    if 'full' in args or type(full) is str and full.lower() == 'true':
        full = True
    if 'perm' in args or type(perm) is str and perm.lower() == 'true':
        await ctx.send("Permission help not implemented")

    content, embed, is_menu, menu_size, pages_count, this_page = get_help_embed(cmd_key, full=full)
    help_message = await ctx.send(content=content, embed=embed)
    was_menu = False
    emoji_nums = {EMOJIS[num]: num for num in range(1, menu_size + 1)}

    await help_message.add_reaction(EMOJIS["arrow_back_left"])

    if pages_count:
        await help_message.add_reaction(EMOJIS["arrow_left"])
        await help_message.add_reaction(EMOJIS["arrow_right"])

    def wait_for_interaction(reaction, user):
        return user == ctx.message.author \
               and str(reaction.emoji) in emojis \
               and reaction.message.id == help_message.id

    while True:
        emojis = [EMOJIS['green_x'],
                  EMOJIS['arrow_left'],
                  EMOJIS['arrow_right'],
                  EMOJIS['arrow_back_left']] + [EMOJIS[num] for num in range(1, menu_size + 1)]

        # for _ms in range(1, menu_size + 1):
        #     await help_message.add_reaction(EMOJIS[_ms])
        # for _ms in range(menu_size + 1, 11):
        #     await help_message.clear_reaction(EMOJIS[_ms])

        try:
            reaction, user = await bot.wait_for("reaction_add", check=wait_for_interaction, timeout=600)
        except asyncio.TimeoutError:
            break

        try:
            await reaction.remove(user)
        except Exception:
            pass

        em = str(reaction.emoji)
        page = 0

        if em == EMOJIS["arrow_left"]:
            pass
        elif em == EMOJIS["arrow_right"]:
            pass
        elif em == EMOJIS["arrow_back_left"]:
            page = 0
        elif em in emoji_nums:
            pass
        else:
            pass

        if was_menu:
            menu = None
        elif cmd_key:
            menu = my_help.help_dict.get(cmd_key, None)
            if menu:
                menu = menu.get("menu")

        ret = get_help_embed(menu, page=page)
        content, embed, is_menu, menu_size, pages_count, this_page = ret
        was_menu = is_menu
        await help_message.edit(content=content, embed=embed)


def get_help_embed(cmd_key=None, full=None, page=0):
    embed = Embed(colour=Colour.from_rgb(60, 255, 150))
    embed.set_author(name=f"{bot.user.name} help menu")
    is_menu = False
    menu_size = 0
    pages_count = 0
    this_page = 0

    if cmd_key:
        cmd_key = cmd_key.lower()
        command = my_help.help_dict.get(cmd_key, None) or my_help.alias_dict.get(cmd_key, None)
    else:
        command = None

    if cmd_key and not command:
        content = f"Not found {cmd_key}"
    else:
        content = ""

    if command:
        "1 Command"
        if full:
            value = command['full']
            if not value:
                value = command['simple']
            embed.add_field(name=command['example'], value=f"```{value}```")
        else:
            embed.add_field(name=command['example'], value=command['simple'])
        content = ""

    elif cmd_key in my_help.menus:
        "1 Menu Page"
        content = ""
        is_menu = True
        commands_in_menu = my_help.menus.get(cmd_key, None)
        embed.set_author(name=cmd_key.title())
        for cmd in commands_in_menu:
            command = my_help.help_dict[cmd]
            inline = False if len(command["simple"]) > 25 or len(command["example"]) > 25 else True
            embed.add_field(name=command["example"], value=command["simple"], inline=inline)

    else:
        "Full Menu"
        menus = my_help.menus.items()
        is_menu = True
        for num, (menu, commands) in enumerate(menus):
            if not menu:
                continue
            inline = True

            menu = menu.title()
            desc = my_help.menus_desc.get(menu.lower(), "No description")
            embed.add_field(name=menu, value=f"`{EMOJIS[num + 1]}` {desc}", inline=inline)

    embed.set_thumbnail(url=bot.user.avatar_url)

    return content, embed, is_menu, menu_size, pages_count, this_page


@bot.command()
@delete_call
@log_call_function
@my_help.help_decorator("Sweeper game, don't blow it up", "(<size>) (<bombs>)")
async def sweeper(ctx, *args):
    """
    Generates sweeper game, !sweeper (size) (bombs)
    Args:
        ctx:
        *args:

    Returns:

    """
    if len(args) == 0:
        size = 7
        bombs = None
    elif len(args) == 1:
        size = args[0]
        size = int(size)
        bombs = None
    elif len(args) == 2:
        size, bombs = args
        size = int(size)
        bombs = int(bombs)
    else:
        logger.error(f"Sweeper args does not match{args}")
        return 0

    "Check table size, 2k characters limit"
    if size < 1:
        size = 2
    elif size > 14:
        size = 14

    "Check bomb amount"
    fields = size * size
    if bombs is None or bombs < 0:
        bombs = size * size // 3.5
    elif bombs >= fields:
        bombs = fields - 1

    bomb_list = [1 if fi < bombs else 0 for fi in range(fields)]
    random.shuffle(bomb_list)
    temp_arr = np.array(bomb_list).reshape(size, size)
    bomb_arr = np.zeros((size + 2, size + 2), dtype=int)
    for rind, row in enumerate(temp_arr):
        rind += 1
        for cin, num in enumerate(row):
            cin += 1
            if num:
                bomb_arr[rind - 1:rind + 2, cin - 1:cin + 2] += 1
        await asyncio.sleep(0.01)

    bomb_arr = bomb_arr[1:-1, 1:-1]
    mask = temp_arr == 1
    bomb_arr[mask] = -1
    hidden_text = '\n'.join(
            "".join(f"||`{num:^2}`||" if num >= 0 else f"||`{'X':^2}`||" for num in row)
            for row in bomb_arr)
    text = f"Sweeper {size}x{size}, bombs: {bombs:.0f}  ({bombs / fields * 100:.0f}%)"
    sweeper_text = f"{text}\n{hidden_text}"
    message = await ctx.send(sweeper_text)
    return message


@bot.command(aliases=['czy', 'is', 'what', 'how'])
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_not_priv)
@my_help.help_decorator("Poll with maximum 10 answers. Minimum 2 answers, maximum 10. timeout is optional",
                        "<question>? <ans1>, ..., <ans10> (timeout=<sec>)")
async def poll(ctx, *args, force=False, dry=False, timeout=2 * 60, **kwargs):
    """
    Multi choice poll with maximum 10 answers
    Example `!poll Question, answer1, answer2, .... answer10`
    Available delimiters: . ; ,
    You can add more time with `timeout=200`, default 180, maximum is 3600 (1hour)
    Use `-d` for dryrun
    Args:
        ctx:
        *args:
        dry:
        **kwargs:

    Returns:

    """

    text = ' '.join(args)
    arr_text = re.split(r"[ '.?;,]", text)
    arr_text = [el.lstrip().rstrip() for el in arr_text if len(el) > 0]
    poll_color = Colour.from_rgb(250, 165, 0)
    finished_poll_color = Colour.from_rgb(30, 255, 0)

    timeout = float(timeout)
    if timeout > 60 * 60 and not force:
        timeout = 60 * 60

    update_interval = 30 if 30 < timeout else timeout

    if len(arr_text) < 3:
        await ctx.send(f"Got less than 1 questions and 2 answers, use some delimiter ?;,")
        return None

    question, *answers = arr_text
    question = question.title() + "?"

    if dry:
        text = f"Question: {question}\n" + f"Answers {len(answers)}: {answers}\n" + f"Timeout: {timeout}"
        await ctx.send(text)
        return None

    elif len(answers) > 10:
        confirm_message = await ctx.send(
                f"Got more than 10 answers, sorry. If you want poll with 10 answers, press reaction.",
                delete_after=60)
        await confirm_message.add_reaction(EMOJIS["green_ok"])

        def wait_for_confirm(reaction, _cur_user):
            return str(reaction.emoji) == EMOJIS["green_ok"] \
                   and _cur_user.id == ctx.author.id \
                   and reaction.message.id == confirm_message.id

        try:
            reaction, user = await bot.wait_for("reaction_add", check=wait_for_confirm, timeout=60)
            answers = answers[0:10]
            await confirm_message.delete()
        except asyncio.TimeoutError:
            return None
    try:
        await ctx.message.delete()
    except Exception:
        pass

    answer_dict = {}

    embed = Embed(title=question, colour=poll_color)
    embed.set_author(name=ctx.author.name)
    embed.set_thumbnail(url=ctx.author.avatar_url)

    for num, ans in enumerate(answers, 1):
        emoji = EMOJIS[num]
        answer_dict[emoji] = {'ans': ans.title(), 'votes': 0}
        embed.add_field(name=emoji, value=ans, inline=False)

    poll = await ctx.send(embed=embed)

    await poll.add_reaction("🛑")
    for num in range(1, len(answers) + 1):
        await poll.add_reaction(EMOJIS[num])
        await asyncio.sleep(0.01)

    def check_end_reaction(reaction, user):
        b1 = reaction.emoji == "🛑"
        b2 = reaction.message.id == poll.id
        b3 = user == ctx.message.author
        return b1 and b2 and b3

    end_time = time.time() + timeout
    k_interrupt = False
    while time.time() <= end_time:
        end_loop = False
        try:
            reaction, message = await bot.wait_for('reaction_add', check=check_end_reaction, timeout=update_interval)
            end_loop = True
        except asyncio.TimeoutError as err:
            pass
        # except KeyboardInterrupt as ki:
        #     end_loop = True
        #     k_interrupt = True
        #     print(ki)

        poll = await ctx.channel.fetch_message(poll.id)
        # all_votes = 0
        all_users = []
        vote_emojis = [EMOJIS[num] for num in range(1, 11)]
        for rc in poll.reactions:
            if rc.emoji not in vote_emojis:
                continue
            users = [user async for user in rc.users()]
            all_users += users
            me = rc.me
            count = rc.count - 1 if me else 0
            # all_votes += count
            answer_dict[rc.emoji]['votes'] = count

        all_users_count = len(set(all_users)) - 1
        embed = Embed(title=question, colour=poll_color)
        embed.set_author(name=ctx.author.name)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=f"Time left: {(end_time - time.time()) / 60:4.1f} min")
        for number in range(1, 11):
            try:
                emoji = EMOJIS[number]
                ans = answer_dict[emoji]['ans']
                votes = answer_dict[emoji]['votes']
                # fraction = votes / all_votes * 100 if all_votes > 0 else 0
                fraction = votes / all_users_count * 100 if all_users_count > 0 else 0
                embed.add_field(name=f"{emoji} -`{fraction:<3.1f} %`", value=ans, inline=False)
            except KeyError:
                break

        await poll.edit(embed=embed)
        await asyncio.sleep(0.01)
        if end_loop:
            break

    embed.colour = finished_poll_color
    embed.set_footer(text="")
    await poll.edit(content='🔒 Poll has ended', embed=embed)
    await poll.clear_reaction("🛑")


@bot.command(aliases=['murder'])
@advanced_args_function(bot)
@log_call_function
@advanced_perm_check_function(is_not_priv)
@my_help.help_decorator("Kill somebody", "<@user> (<num>)", menu="fun", aliases=['murder'])
async def shoot(ctx, *args, force=False, dry=False, **kwargs):
    """
    Send message that mention somebody up to 10 times, and show gun with faces.
    Args:
        ctx:
        *args:
        force:
        dry:
        **kwargs:

    Returns:

    """
    LIVE_EMOJIS = ['😀', '😃', '😁', '😕', '😟', '😒', '😩', '🥺', '😭', '😢', '😬', '😶']
    DEAD_EMOJIS = ['😵', '💀', '☠️', '👻']
    BLADES = ["🗡️", "🔪"]

    try:
        user = ctx.message.mentions[0].mention
        try:
            num = args[0]
        except IndexError:
            num = 1
    except IndexError:
        try:
            user = args[0]
        except IndexError:
            await ctx.send("🤔")
            return None

        try:
            num = args[1]
        except IndexError:
            num = 1

    num = int(num)
    if num > 10 and not force:
        num = 10

    for x in range(num):
        liv_em = random.choice(LIVE_EMOJIS)
        dead_em = random.choice(DEAD_EMOJIS)
        blade = random.choice(BLADES)
        pre = "⬛🔫" if ctx.invoked_with == "shoot" else blade
        post = "💥🔫" if ctx.invoked_with == "shoot" else blade

        shoot = await ctx.send(f"{user} {liv_em} {pre} {ctx.author.mention}")
        await asyncio.sleep(random.randint(10, 30) / 10)

        await shoot.edit(content=f"{user} {dead_em} {post} {ctx.author.mention}")


async def get_picture(url_pic):
    re = requests.get(url_pic)
    if re.status_code == 200:
        # re.raw = True
        im_bytes = re.content
        im_arr = np.frombuffer(im_bytes, np.uint8)
        image = cv2.imdecode(im_arr, cv2.IMREAD_COLOR)
        return image
    else:
        print(f"Invalid status code when fetching picture: "
              "{re.status_code} from {url_pic}")


def morph_image_to_gray(image):
    """Converts rgb image to gray"""
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image


def save_image(image, path):
    path = os.path.abspath(path)
    logger.debug(f"Saving image to: {path}")
    cv2.imwrite(path, image)


@bot.command(aliases=['feedback', 'report', 'problem', 'suggestion', 'suggest', 'idea'])
@advanced_args_function(bot)
@log_call_function
@my_help.help_decorator("Send feedback to author, problems or new ideas, depending on which command was used.",
                        "<text>",
                        aliases=['feedback', 'report', 'problem', 'suggestion', 'suggest', 'idea'],
                        help_name="feedback")
async def _user_feedback(ctx, *args, text, **kwargs):
    """
    Send text message to the developer.
    Available commands:
        !report <text>
        !problem <text>
        !suggestion <text>
        !suggest <text>
        !idea <text>
        !feedback <text>

    Args:
        ctx:
        *args:
        text:
        **kwargs:

    Returns:

    """
    feedback_channel = 758358711382573056 if bot.user.name == "YasiuBot" else 757975910233145448
    invoked = ctx.invoked_with
    if invoked == "feedback":
        text = f"{ctx.author}, {ctx.guild}, has sent feedback: {text}"
        feedback.info(text)

    elif invoked == "report" or invoked == "problem":
        text = f"{ctx.author}, {ctx.guild}, has reported this problem: {text}"
        feedback.warning(text)

    elif invoked == "suggestion" or invoked == "suggest" or invoked == "tip" or invoked == "idea":
        text = f"{ctx.author}, {ctx.guild}, has a suggestion: {text}"
        feedback.warning(text)

    else:
        text = f"{ctx.author}, {ctx.guild}, send message: {text}"
        feedback.warning(text)

    channel = bot.get_channel(feedback_channel)
    await channel.send(text)


os.makedirs("avatars", exist_ok=True)
my_help.create_help()
bot.add_cog(EFTCog())
