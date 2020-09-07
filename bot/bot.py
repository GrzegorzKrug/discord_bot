import numpy as np
import requests
import asyncio
import logging
import random
import scipy
import cv2
import sys
import os

from discord.ext.commands import Bot, check, CommandError
from collections import namedtuple


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
                    var = float(arg)
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
        return f

    return decorator


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    # print('Logged on as {0}!'.format(self.user))


@bot.event
async def on_message(message):
    await bot.process_commands(message)


# @bot.event
# async def activity():
#     print("activated")
#     pass


def delete_call(fun):
    """
    Decorator that removes message which triggered command.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    async def wrapper(ctx, *args, **kwargs):

        try:
            await ctx.message.delete()
        except Exception as pe:
            logger.error(f"Permission error: {pe}")

        result = await fun(ctx, *args, **kwargs)
        return result

    wrapper.__name__ = fun.__name__
    return wrapper


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
        async def wrapper(ctx, *args, **kwargs):

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

        wrapper.__name__ = fun.__name__
        return wrapper

    return function


@bot.command()
@trash_after()
@delete_call
async def test(ctx, *args, dry=False, force=False, **kwargs):
    logger.debug("Test 1 ok ?")
    message = await ctx.channel.send("Test 1 ok ?")
    return message


@bot.command(aliases=['purge'])
@advanced_perm_check()
@delete_call
async def purge_all(ctx, num=1, *args, **kwargs):
    channel = ctx.channel
    num = int(num)

    def is_me(m):
        return True

    logger.info(f"Removing {num} messages in {ctx.channel}: {ctx.guild}")
    await channel.purge(limit=num, check=is_me)


@bot.command()
@advanced_perm_check()
@delete_call
async def purge_bot(ctx, num=1, *args, **kwargs):
    channel = ctx.channel
    num = int(num)

    def is_me(m):
        return m.author.id == bot.user.id

    logger.info(f"Removing {num} bot messages in {ctx.channel}: {ctx.guild}")
    await channel.purge(limit=num, check=is_me)


@bot.command()
@advanced_perm_check(is_not_priv)
async def slipper(ctx, dim=10, *args, **kwargs):
    game_controls = ['⬅️', '➡', '⬆️', '⬇️', '🔁']
    translate = {'⬅️': 'left', '➡': 'right', '⬆️': 'up', '⬇️': 'down', '🔁': 'restart'}
    message = await ctx.send("Let's start the game.")
    game_num = 0
    DIM = int(dim)
    DIM = 5 if DIM < 2 else DIM

    while True and game_num < 5:
        game_num += 1
        restart = False
        position = (0, 0)
        win_position = (DIM - 1, DIM - 1)

        board_of_string = slipper_empty_board(DIM)
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
                reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check_reaction)
            except asyncio.TimeoutError:
                game_over = message.content + f"\nTimeout, you lost {ctx.message.author.name}"
                await message.edit(content=game_over)
                return message

            await message.remove_reaction(reaction, ctx.message.author)
            move = translate[reaction.emoji]

            if move == 'restart':
                restart = True
                break

            elif move == "left":
                check = (position[0], (position[1] - 1) % DIM)
                if board_of_string[check] != '1':
                    valid_move = True
            elif move == "right":
                check = (position[0], (position[1] + 1) % DIM)
                if board_of_string[check] != '1':
                    valid_move = True

            elif move == "up":
                check = ((position[0] - 1), position[1])
                if min(check) >= 0 and max(check) < DIM and board_of_string[check] != '1':
                    valid_move = True
            elif move == "down":
                check = ((position[0] + 1), position[1])
                if min(check) >= 0 and max(check) < DIM and board_of_string[check] != '1':
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
    await message.add_reaction("🏅")
    for rc in game_controls:
        await message.clear_reaction(rc)


def slipper_empty_board(a=10):
    area = a * a
    ammount = area // 2.5
    board = [1 if x < ammount else 0 for x in range(area)]
    random.shuffle(board)
    board = np.array(board).reshape(a, a)
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
async def private(ctx):
    await ctx.author.send("hello")


@bot.command()
async def spam(ctx, num=1):
    num = int(num)
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
async def save_avatar(ctx):
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
        # await asyncio.sleep(10)
        # await ctx.message.clear_reaction("❓")

    else:
        logger.error(f"Unpredicted Error: '{command_error}, cmd: {text}', server: '{server}'")


@bot.command(aliases=['hi'])
async def hello(ctx):
    pool = ["Hello there {0}", "How is it going today {0} ?", "What's up {0}?", "Hey {0}",
            "Hi {0}, do you feel well today?", "Good day {0}"]
    text = random.choice(pool)
    await ctx.send(text.format(ctx.message.author.name))


@bot.command()
@delete_call
@advanced_perm_check(is_not_priv)
async def countdown(ctx, num=10, dry=False, force=False, **kwargs):
    try:
        num = int(num)
        if num > 30 and not force:
            num = 30
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
@trash_after()
async def sweeper(ctx, *args):
    """Generates sweeper argsay with counted bombs next to given field"""
    logger.debug(f"sweeper args: {args}")
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
    logger.debug(f"{sweeper_text}")
    message = await ctx.send(sweeper_text)
    return message


@bot.command()
@advanced_perm_check()
async def test2(ctx, *args, **kwargs):
    await ctx.channel.send("Test 2 ok ?")
    await ctx.channel.send(f"args: {args}")
    await ctx.channel.send(f"kwargs: {kwargs}")


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


if __name__ == "__main__":
    try:
        with open("token.txt", "rt") as file:
            token = file.read()
    except Exception as e:
        print(f"{e}")
        sys.exit(1)

    os.makedirs("avatars", exist_ok=True)
    bot.run(token)
    # 470285521 # permission int
