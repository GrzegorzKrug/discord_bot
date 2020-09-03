import numpy as np
import requests
import asyncio
import logging
import random
import scipy
import cv2
import sys
import os

from discord.ext.commands import Bot


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
    ch.setLevel("INFO")

    # Log Formatting
    formatter = logging.Formatter(
            f'%(asctime)s - {name} - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    return logger


logger = define_logger("Bot")

bot = Bot(command_prefix='!', case_insensitive=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    # print('Logged on as {0}!'.format(self.user))


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command(name="saveme")
async def save_avatar(ctx):
    avatar_url = ctx.author.avatar_url
    name = ctx.author.name

    image = await get_picture(avatar_url)
    save_image(image, f"avatars/{name}.png")


@bot.event
async def on_command_error(ctx, command):
    logger.warning(f"Not found cmd: '{command}' at {ctx.guild} ({ctx.guild.id})")
    # await ctx.send(f"What is this: !{command} ?")


@bot.command()
async def sweeper(ctx, *arr):
    """Generates sweeper array with counted bombs next to given field"""
    logger.debug(f"sweeper args: {arr}")
    if len(arr) == 0:
        size = 7
        bombs = None
    elif len(arr) == 1:
        size = arr[0]
        size = int(size)
        bombs = None
    elif len(arr) == 2:
        size, bombs = arr
        size = int(size)
        bombs = int(bombs)
    else:
        logger.error(f"Sweeper args does not match{arr}")
        return 0

    "Check table size, 2k characters limit"
    if size < 1:
        size = 2
    elif size > 13:
        size = 13

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
            "".join(f"||`{num:^2}`||" if num >= 0 else "||:boom:||" for num in row)
            for row in bomb_arr)
    text = f"Sweeper {size}x{size}, bombs: {bombs:.0f}  ({bombs / fields * 100:.0f}%)"
    sweeper_text = f"{text}\n{hidden_text}"
    logger.debug(f"Sweeper msg len: {len(sweeper_text)}")
    await ctx.send(sweeper_text)


@bot.command()
async def test(ctx, arg=None):
    logger.debug("Testing!")
    await ctx.channel.send("testing")


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
