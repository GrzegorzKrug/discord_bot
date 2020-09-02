import numpy as np
import requests
import asyncio
import discord
import logging
import random
import scipy
import cv2
import sys
import os


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


class Bot(discord.Client):
    logger = define_logger("Bot")

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        author = message.author
        text = message.content.lower()
        server_id = message.guild.id
        channel = message.channel

        msg = ("Msg: '{0.guild.name}' ({0.guild.id}) by '{0.author}' "
               "at channel '{0.channel}': '{0.content}'").format(message)

        if text.startswith("!saveme"):
            self.logger.info(msg)
            await self.save_avatar(author.name, author.avatar_url)
        elif text.startswith("!hello"):
            self.logger.info(msg)
            await channel.send('Powiedz siema!')
        elif text.startswith("!sweeper"):
            self.logger.info(msg)
            arr_text = text.split(" ")
            try:
                if len(arr_text) == 1:
                    size = 7
                    bombs = None
                elif len(arr_text) == 2:
                    cmd, size = arr_text
                    size = int(size)
                    bombs = None
                elif len(arr_text) == 3:
                    cmd, size, bombs = arr_text
                    size = int(size)
                    bombs = int(bombs)
                else:
                    raise ValueError("Too much params")

                arr = await self.generate_sweeper(size, bombs)
                await channel.send(str(arr))

            except ValueError as ve:
                self.logger.error(f"{ve} during {msg}")
                channel.send(f"You should specify number for this game "
                             "(!sweeper 10) or 10 and 20 bombs")

        elif author.id == self.user.id:
            pass
            # print(f"This is my message: {text}")
        elif text.startswith("!"):
            self.logger.warning(f"unkown command '{text}'")
            await channel.send(f'what is this command: {text}? ')
        else:
            print(f"msg: {text}")

    async def save_avatar(self, name, avatar_url):
        image = await self.get_picture(avatar_url)
        self.save_image(image, f"avatars/{name}.png")

    @staticmethod
    async def generate_sweeper(size, bombs=None):
        """Generates sweeper array with counted bombs next to given field"""
        if size < 1:
            size = 2
        elif size > 14:
            size = 14

        if bombs is None or bombs < 0:
            bombs = size * size // 5
        fields = size * size
        bomb_list = [1 if fi < bombs else 0 for fi in range(fields)]
        random.shuffle(bomb_list)
        temp_arr = np.array(bomb_list).reshape(size, size)
        bomb_arr = np.zeros((size+2, size+2), dtype=int)
        for rind, row in enumerate(temp_arr):
            rind += 1
            for cin, num in enumerate(row):
                cin += 1
                if num:
                    bomb_arr[rind-1:rind+2, cin-1:cin+2] += 1
        bomb_arr = bomb_arr[1:-1, 1:-1]
        mask = temp_arr == 1
        bomb_arr[mask] = -1
        hidden_text = '\n'.join(
            "".join(f"||`{num:^2}`||" if num >= 0 else "||:boom:||" for num in row)
            for row in bomb_arr)
        text = f"Sweeper game {size}x{size}, bombs: {bombs}, area in bombs: {bombs / fields*100:4.1f}%"
        sweeper_text = f"{text}\n{hidden_text}"
        return sweeper_text

    @staticmethod
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

    @staticmethod
    def morph_image_to_gray(image):
        """Converts rgb image to gray"""
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image

    @staticmethod
    def save_image(image, path):
        path = os.path.abspath(path)
        Bot.logger.debug(f"Saving image to: {path}")
        cv2.imwrite(path, image)


if __name__ == "__main__":
    try:
        with open("token.txt", "rt") as file:
            token = file.read()
    except Exception as e:
        print(f"{e}")
        sys.exit(1)

    # CONFIG =
    os.makedirs("avatars", exist_ok=True)
    bot = Bot()
    bot.run(token)
    # 470285521 # permission int
