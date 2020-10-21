from discord import File
from io import BytesIO

import discord

from .definitions import *
from .decorators import *
from .loggers import *

import requests
import imutils
import numpy as np
import cv2


@bot.command(aliases=['imposter'])
@advanced_args_function(bot)
@log_call_function
@my_help.help_decorator("Check if somebody was and imposter", menu="fun", aliases=['imposter'])
async def check_imposter(ctx, *args, **kwargs):
    if ctx.message.mentions:
        "Process mention"
        avatar_url = ctx.message.mentions[0].avatar_url
        name = ctx.message.mentions[0].name

    elif args:
        name = args[0]
        member = discord.utils.find(lambda m: name.lower() in m.name.lower(), ctx.guild.members)
        logger.debug(f"Found member: {member}")
        if member:
            avatar_url = member.avatar_url
            name = member.name
        else:
            avatar_url = ctx.author.avatar_url
            name = ctx.author.name

    else:
        avatar_url = ctx.author.avatar_url
        name = ctx.author.name

    res = requests.get(avatar_url, stream=True)
    if res.status_code != 200:
        logger.error(f"Request has incorrect code: {res.status_code}")
        return None
    image = np.frombuffer(res.content, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    imposter = _create_imposter_image(image, name)
    success, img_bytes = cv2.imencode(".png", imposter)
    if success:
        bytes_like = BytesIO(img_bytes)
        fp = File(bytes_like, filename="imposter.png")
        await ctx.send(file=fp)

    # await send_approve(ctx)


def _create_imposter_image(image, name):
    imp_path = os.path.join(os.path.dirname(__file__), "src_images", "imposter.png")
    eject_picture = cv2.imread(imp_path)
    is_imposter = random.choice([True, False])
    angle = np.random.randint(15, 170)

    if is_imposter:
        text = "was the imposter."
    else:
        text = "was not the imposter."

    imposter = cv2.resize(image, (320, 320))
    imposter = imutils.rotate_bound(imposter, angle)

    rs, cs, _ = imposter.shape
    posx, posy = 350, 110
    roi = eject_picture[posy:posy + rs, posx:posx + cs, :]
    roi[:, :, :] = imposter

    text_color = (0, 0, 255) if is_imposter else (255, 255, 255)
    cv2.putText(eject_picture, name, (50, 600), cv2.FONT_HERSHEY_COMPLEX, 1.6, text_color, 2, cv2.LINE_AA)
    cv2.putText(eject_picture, text, (50, 660), cv2.FONT_HERSHEY_COMPLEX, 1.6, (255, 255, 255), 2, cv2.LINE_AA)
    dest_x, dest_y = eject_picture.shape[0:2]

    dest_x = int(dest_x // 1.5)
    dest_y = int(dest_y // 1.5)

    eject_picture = cv2.resize(eject_picture, (dest_y, dest_x))
    return eject_picture