from discord import File
from io import BytesIO

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
        avatar_url = ctx.message.mentions[0].avatar_url
        name = ctx.message.mentions[0].name
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
    angle = np.random.randint(0, 360)
    pool = ["{} was not the imposter.",
            "{} was the imposter"]
    text = random.choice(pool)
    imposter = imutils.rotate_bound(image, angle)
    imposter = cv2.resize(imposter, (350, 350))

    rs, cs, _ = imposter.shape
    posx, posy = 307, 160
    roi = eject_picture[posy:posy + rs, posx:posx + cs, :]

    roi[:, :, :] = imposter

    text = text.format(name)

    cv2.putText(eject_picture, text, (50, 600), cv2.QT_FONT_NORMAL, 2, (255, 255, 255), 3)
    dest_x, dest_y = eject_picture.shape[0:2]

    dest_x = int(dest_x // 1.5)
    dest_y = int(dest_y // 1.5)

    eject_picture = cv2.resize(eject_picture, (dest_y, dest_x))
    return eject_picture
