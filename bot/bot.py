import numpy as np
import traceback
import requests
import asyncio
import logging
import random
import scipy
import time
import cv2
import sys
import os
import re

from discord.ext.commands import Bot, CommandError
# from discord.ext.commands.errors import
from discord import Activity, Game, Status, Embed, Colour


def define_logger(name="Logger", log_level="DEBUG",
                  combined=True, add_timestamp=True):
    if combined:
        file_name = "Logs.log"
    else:
        file_name = name + ".log"

    if add_timestamp:
        unique_name = str(random.random())  # Random unique
    else:
        unique_name = name
    logger = logging.getLogger(unique_name)

    # Switch log level from env variable
    if log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif log_level == "INFO":
        logger.setLevel(logging.INFO)
    elif log_level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif log_level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif log_level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.WARNING)

    # Log Handlers: Console and file
    try:
        fh = logging.FileHandler(os.path.join(r'/logs', file_name),
                                 mode='a')
    except FileNotFoundError:
        os.makedirs(r'logs', exist_ok=True)
        fh = logging.FileHandler(os.path.join(r'logs', file_name),
                                 mode='a')

    ch = logging.StreamHandler()

    # LEVEL
    fh.setLevel("INFO")

    # Log Formatting
    formatter = logging.Formatter(
            f'%(asctime)s -{name}- %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    return logger


def is_not_priv(ctx, *args, **kwargs):
    if ctx.guild:
        return True
    else:
        return False


logger = define_logger("Bot")

bot = Bot(command_prefix='!', case_insensitive=True)
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


def advanced_args(fun):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    async def wrapper(ctx, *args, **kwargs):
        good_args = list()
        # force = False
        # dry = False
        if not kwargs:
            kwargs = {"force": False, "dry": False, "sudo": False}
        for arg in args:
            if arg.startswith("-f"):
                "force, enforce parameters"
                kwargs['force'] = True
            elif arg.startswith("-d"):
                "dry run"
                kwargs['dry'] = True
            elif arg.startswith("-s") or arg.startswith("-a"):
                "sudo or admin"
                kwargs['sudo'] = True
            elif arg.startswith("-"):
                try:
                    _ = float(arg)
                    good_args.append(arg)
                except ValueError:
                    "drop unknown parameters"
                    logger.warning(f"unknown argument: {arg}")
            elif "=" in arg:
                key, val = arg.split("=")
                if key == "force" or key == "dry":
                    continue
                if key and val:
                    kwargs.update({key: val})
            else:
                good_args.append(arg)

        good_args = tuple(good_args)
        output = await fun(ctx, *good_args, **kwargs)
        return output

    wrapper.__name__ = fun.__name__
    return wrapper


def check_sudo_permission(ctx):
    logger.critical(f"NotImplemented, sudo is not checking permission yet")
    return False


def check_force_permission(ctx):
    logger.critical(f"NotImplemented, force is not checking permission yet")
    return False


def advanced_perm_check(*checking_funs):
    """
    Check channels and permissions, use -s -sudo or -a -admin to run it.
    Args:
        *checking_funs:

    Returns:
        message object returned by calling given function with given params
    """

    def decorator(fun):
        @advanced_args
        async def f(ctx, *args, sudo=False, force=False, **kwargs):
            if sudo and check_sudo_permission(ctx) or all(chk_f(ctx, *args, **kwargs) for chk_f in checking_funs):
                if force:
                    force = check_force_permission(ctx)

                output = await fun(ctx, force=force, *args, **kwargs)
                return output
            else:
                raise CommandError("No permission")

        f.__name__ = fun.__name__
        f.__doc__ = fun.__doc__
        return f

    return decorator


@bot.event
async def on_ready():
    act = Game(name="!sweeper.", url='Fancy url', type=0)
    await bot.change_presence(activity=act, status=Status.online)
    await announcement("✅ Hey, i'm now online.", [750696820736393261])
    logger.debug(f"Going online as {bot.user.name}")


@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        print("yes")
    await bot.process_commands(message)


@bot.command()
async def test(ctx, *args):
    await ctx.send("!test")


@bot.event
async def close():
    act = Game(name="Zzzzzzz....", type=2)
    await bot.change_presence(activity=act, status=Status.offline)
    await announcement("💤 Sorry, I am going offline.", [750696820736393261])
    logger.debug(f"Going offline")


async def announcement(message, chids=None):
    for ch in chids:
        channel = bot.get_channel(ch)
        await channel.send(message)
        await asyncio.sleep(0.01)


def delete_call(fun):
    """
    Decorator that removes message which triggered command.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        result = await fun(ctx, *args, **kwargs)

        try:
            await ctx.message.delete()
        except Exception as pe:
            logger.error(f"Can not delete call: {pe}")

        return result

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator


def trash_after(timeout=600):
    """
    Decorator, that remove message after given time.
    Decorated function must return message!
    Args:
        timeout: Integer, default 600

    Returns:
        message object returned by calling given function with given params


    """

    def function(fun):
        async def decorator(ctx, *args, **kwargs):

            message = await fun(ctx, *args, **kwargs)

            await message.add_reaction("❎")
            await asyncio.sleep(0.1)

            def check_reaction(reaction, user):
                return user == ctx.message.author \
                       and str(reaction.emoji) == '❎' \
                       and reaction.message.id == message.id

            try:
                if timeout < 1:
                    tm = 30
                else:
                    tm = timeout
                reaction, user = await bot.wait_for('reaction_add',
                                                    check=check_reaction,
                                                    timeout=tm)
            except asyncio.TimeoutError:
                pass

            await message.delete()

        decorator.__name__ = fun.__name__
        decorator.__doc__ = fun.__doc__
        return decorator

    return function


def log_call(fun):
    """
    Decorator, logs function.
    Args:
        timeout: Integer, default 600

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        if ctx.guild:
            guild = f"{ctx.guild.name} ({ctx.guild.id})"
        else:
            guild = 'private'
        logger.info(f"Invo: '{ctx.message.content}', Args:{args}, Kwargs:{kwargs}. {ctx.channel}, {guild}")

        message = await fun(ctx, *args, **kwargs)
        return message

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator


@bot.command(aliases=['purge'])
@advanced_perm_check()
@log_call
async def purge_all(ctx, amount, *args, **kwargs):
    """
    !purge amount, removes all messages
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

        await ctx.send(f"♻️ Removed {len(deleted)} messages", delete_after=5)


@bot.command()
@advanced_perm_check()
@log_call
@delete_call
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

        await ctx.send(f"♻️ Removed {len(deleted)} messages", delete_after=5)


@bot.command()
@advanced_perm_check()
@log_call
@delete_call
async def purge_bot(ctx, amount, *args, **kwargs):
    channel = ctx.channel
    num = int(amount)

    def is_me(m):
        return m.author.id == bot.user.id

    if num >= 1:
        deleted = await channel.purge(limit=num, check=is_me)
        logger.info(f"Removed {len(deleted)} bot messages in {ctx.channel}: {ctx.guild}")
        await ctx.send(f"♻️ Removed {len(deleted)} bot messages", delete_after=5)


@bot.command()
@advanced_perm_check(is_not_priv)
@log_call
async def slipper(ctx, dimy=10, dimx=6, *args, **kwargs):
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


@bot.command()
@advanced_args
@log_call
async def eft(ctx, *keyword, dry=False, **kwargs):
    search_url = r'https://escapefromtarkov.gamepedia.com/index.php?search='
    search_phrase = '+'.join(keyword)

    results = requests.get(search_url + search_phrase)
    print(results.text)


@bot.command()
@log_call
async def private(ctx):
    """
    Hello in private channel
    Args:
        ctx:

    Returns:

    """
    await ctx.author.send("hello")


@bot.command()
@log_call
async def spam(ctx, num=1):
    num = int(num)
    if num > 100:
        num = 100
    for x in range(num):
        await ctx.channel.send(x + 1)
        await asyncio.sleep(0.01)


@bot.command()
@delete_call
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


@bot.command(name="saveme")
@log_call
async def save_avatar(ctx):
    """
    Saves avatar in directory
    Args:
        ctx:

    Returns:

    """
    avatar_url = ctx.author.avatar_url
    name = ctx.author.name

    image = await get_picture(avatar_url)
    save_image(image, f"avatars/{name}.png")


@bot.event
async def on_command_error(ctx, command_error):
    text = ctx.message.content
    invoked = ctx.invoked_with
    text_error = str(command_error)
    server = "private_message" if not ctx.guild else f"{ctx.guild} ({ctx.guild.id})"
    if text_error.startswith("The check functions for command") or text_error.startswith("No permission"):
        logger.warning(f"No permission: '{text}', server: '{server}'")
        await ctx.message.add_reaction("⛔")
        await ctx.channel.send(f"Some permissions do not allow it to run here '{invoked}'")

    elif text_error.endswith("is not found"):
        logger.warning(f"Command not found: '{text}', server: '{server}'")
        await ctx.message.add_reaction("❓")

    elif "required positional argument" in text_error:
        await ctx.channel.send(f"Some arguments are missing: '{command_error.original}'")

    else:
        tb_text = traceback.format_exception(type(command_error), command_error, command_error.__traceback__)
        tb_text = ''.join([line for line in tb_text if f'bot{os.path.sep}' in line])
        logger.error(
                f"No reaction for this error type:\n"
                f"Command: '{ctx.message.content}', server: '{server}', \n"
                f"'{command_error}'\n"
                f"Partial traceback:\n{tb_text}")


@bot.event
async def on_member_join(member):
    logger.info(f"{member} has joined {member.guild} ({member.guild.id})")
    await member.guild.system_channel.send(f"Hello {member.mention}")


@bot.event
async def on_member_remove(member):
    logger.info(f"{member} has left {member.guild} ({member.guild.id})")
    await member.guild.system_channel.send(f"Bye {member.mention}")


@bot.command(aliases=['hi'])
@log_call
async def hello(ctx, *args):
    pool = ["Hello there {0}", "How is it going today {0} ?", "What's up {0}?", "Hey {0}",
            "Hi {0}, do you feel well today?", "Good day {0}"]
    text = random.choice(pool)
    await ctx.send(text.format(ctx.message.author.name))


@bot.command()
@delete_call
@advanced_perm_check(is_not_priv)
@log_call
async def countdown(ctx, num=10, dry=False, force=False, **kwargs):
    try:
        num = int(num)
        if num > 10 and not force:
            num = 10
        if num < 1:
            num = 1

    except ValueError as ve:
        logger.error(f"Countdown incorrect arg: {num}")
        num = 5

    # chid = 750696820736393261
    channel = ctx.channel
    if not dry:
        msg_countdown = await channel.send(f"Time left: {num}")
        for x in range(num - 1, -1, -1):
            text = f"Time left: {x}"
            await msg_countdown.edit(content=text)
        await msg_countdown.delete()
    else:
        await channel.send(f"Countdown of {num}, will delete this dryrun message....", delete_after=10)


@bot.command()
@delete_call
@log_call
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

    "Check bomb ammount"
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


@bot.command()
@log_call
async def ask(ctx, *args, **kwargs):
    raise NotImplementedError


@bot.command(aliases=['czy', 'is', 'what', 'how'])
@advanced_perm_check(is_not_priv)
@log_call
async def poll(ctx, *args, force=False, dry=False, timeout=120, **kwargs):
    """
    Multi choice poll with maximum 10 answers
    Example `!poll Question, answer1, answer2, .... answer10`
    Available delimeters: . ; ,
    You can add more time with `timeout=200`, default 120, maxiumum is 1200 (20 min)
    Use `-d` for dryrun
    Args:
        ctx:
        *args:
        dry:
        **kwargs:

    Returns:

    """
    text = ' '.join(args)
    arr_text = re.split(r"['\.?;,']", text)
    arr_text = [el.lstrip().rstrip() for el in arr_text if len(el) > 0]
    poll_color = Colour.from_rgb(250, 165, 0)
    finished_poll_color = Colour.from_rgb(30, 255, 0)

    timeout = float(timeout)
    if timeout > 1200 and not force:
        timeout = 1200

    if len(arr_text) < 3:
        await ctx.send(f"Got less than 1 questions and 2 answers, sorry")
        return None

    question, *answers = arr_text
    question = question.title() + "?"

    if dry:
        text = f"Question: {question}\n" + f"Answers {len(answers)}: {answers}\n" + f"Timeout: {timeout}"
        await ctx.send(text)
        return None

    elif len(answers) > 10:
        await ctx.send(f"Got more than 10 answers, sorry")
        return None

    await ctx.message.delete()

    answer_dict = {}

    embed = Embed(title=question, colour=poll_color)
    embed.set_author(name=ctx.author.name)
    embed.set_thumbnail(url=ctx.author.avatar_url)

    for num, ans in enumerate(answers, 1):
        emoji = EMOJIS[str(num)]
        answer_dict[emoji] = {'ans': ans, 'votes': 0}
        embed.add_field(name=emoji, value=ans, inline=False)

    poll = await ctx.send(embed=embed)

    await poll.add_reaction("🛑")
    for num in range(1, len(answers) + 1):
        await poll.add_reaction(EMOJIS[str(num)])
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
            reaction, message = await bot.wait_for('reaction_add', check=check_end_reaction, timeout=30)
            end_loop = True
        except asyncio.TimeoutError as err:
            pass
        # except KeyboardInterrupt as ki:
        #     end_loop = True
        #     k_interrupt = True
        #     print(ki)

        poll = await ctx.channel.fetch_message(poll.id)
        all_votes = 0
        vote_emojis = [EMOJIS[str(num)] for num in range(1, 11)]
        for rc in poll.reactions:
            if rc.emoji not in vote_emojis:
                continue
            me = rc.me
            count = rc.count - 1 if me else 0
            all_votes += count
            answer_dict[rc.emoji]['votes'] = count

        embed = Embed(title=question, colour=poll_color)
        embed.set_author(name=ctx.author.name)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        for number in range(1, 11):
            try:
                emoji = EMOJIS[str(number)]
                ans = answer_dict[emoji]['ans']
                votes = answer_dict[emoji]['votes']
                fraction = votes / all_votes * 100 if all_votes > 0 else 0
                embed.add_field(name=f"{emoji} -`{fraction:<3.1f} %`", value=ans, inline=False)
            except KeyError:
                break

        await poll.edit(embed=embed)
        await asyncio.sleep(0.01)
        if end_loop:
            break
    embed.color = finished_poll_color
    await poll.edit(content='✅ Poll has ended', embed=embed)
    await poll.clear_reaction("🛑")


@bot.command()
@advanced_perm_check(is_not_priv)
@log_call
async def shoot(ctx, user, num=3, *args, force=False, dry=False, **kwargs):
    LIVE_EMOJIS = ['😀', '😃', '😁', '😕', '😟', '😒', '😩', '🥺', '😭', '😢', '😬', '😶']
    DEAD_EMOJIS = ['😵', '💀', '☠️', '👻']

    num = int(num)
    if num > 10 and not force:
        num = 10

    for x in range(num):
        liv_em = random.choice(LIVE_EMOJIS)
        dead_em = random.choice(DEAD_EMOJIS)
        shoot = await ctx.send(f"{user} {liv_em} ⬛🔫 {ctx.author.mention}")
        await asyncio.sleep(random.randint(10, 30) / 10)
        await shoot.edit(content=f"{user} {dead_em} 💥🔫 {ctx.author.mention}")


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


@bot.command()
@log_call
async def test_embed(ctx, *args, **kwargs):
    pic_url = r'https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2Fpixel.nymag.com%2Fimgs%2Fdaily%2Fintelligencer%2F2014%2F12%2F08%2F08-grumpy-cat.o.jpg%2Fa_190x190.w1200.h630.jpg&f=1&nofb=1'
    description = "This is some big, ass text, for the title, description, " \
                  + "including information about picture on the right side"

    author = bot.get_user(147795752943353856)

    col = Colour.from_rgb(30, 129, 220)
    embed = Embed(title='Hello', color=col, description=f"[{description}]({pic_url})", url=pic_url)

    embed.add_field(name=EMOJIS['1'], value="tex1", inline=True)
    embed.add_field(name="f2", value="tex2", inline=True)
    embed.add_field(name="f3", value="tex3", inline=False)
    embed.add_field(name="f3", value="tex3", inline=False)
    embed.add_field(name="f3", value="tex3", inline=False)
    embed.add_field(name="f3", value="tex3", inline=False)
    embed.add_field(name="f3", value="tex3", inline=True)
    embed.set_thumbnail(url=author.avatar_url)
    embed.set_author(name="Youshisu")
    embed.set_footer(text='your text', icon_url=pic_url)
    # embed.color = (200, 90, 170)
    await ctx.send(embed=embed, content="content")


async def custom_run(token):
    logger.debug("Custom run")
    await bot.login(token)
    logger.debug("Logged in")
    await bot.connect(reconnect=True)
    logger.debug("Connected")


if __name__ == "__main__":
    try:
        with open("token.txt", "rt") as file:
            token = file.read()
    except Exception as e:
        print(f"{e}")
        sys.exit(1)

    os.makedirs("avatars", exist_ok=True)
    bot.run(token)
    # asyncio.run(custom_run(token))
    # 470285521 # permission int
