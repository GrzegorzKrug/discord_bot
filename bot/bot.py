import numpy as np

import requests
import discord
import logging
import random
import cv2
import sys
import os


def define_logger(name="Logger", log_level="DEBUG", combined=True, add_timestamp=True):
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
        print("NewMSG: Server #'{0.guild.id}' ({0.guild.name}) by '{0.author}' at channel '{0.channel}': '{0.content}'".format(
            message))
        avatar_url = message.author.avatar_url
        if avatar_url:
            image = self.get_picture(avatar_url)
            # image = self.morph_image_to_gray(image)
            self.save_image(image, f"avatars/{message.author.name}.png")

    @staticmethod
    def get_picture(url_pic):
        re = requests.get(url_pic)
        if re.status_code == 200:
            re.raw = True
            im_bytes = re.content
            im_arr = np.frombuffer(im_bytes, np.uint8)
            image = cv2.imdecode(im_arr, cv2.IMREAD_COLOR)
            return image
            # cv2.imwrite("pic.png", image)
        else:
            print(f"Invalid status code when fetching picture: {re.status_code} from {url_pic}")

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
