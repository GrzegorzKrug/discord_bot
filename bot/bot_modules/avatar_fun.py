from .definitions import *
from .decorators import *
from .loggers import *
from .images import *

import asyncio
import imutils
import numpy as np
import cv2


@bot.command()
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Creates poster", menu="fun")
async def wanted(ctx, name, avatar_url, *args, **kwargs):
    image = get_picture(avatar_url)
    image = cv2.resize(image, (256, 256))
    await asyncio.sleep(0.1)

    imposter = _create_wanted_image(image, name)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(imposter, "wanted")
    await ctx.send(file=file)


def _create_wanted_image(image, name):
    img_path = os.path.join(os.path.dirname(__file__), "src_images", "wanted3.png")
    wanted = cv2.imread(img_path)

    image = convert_to_sephia(image, 7, 60)
    rows, cols, channels = image.shape
    cx, cy = 185, 350
    slic = (slice(cy, cy + rows), slice(cx, cx + cols), slice(None))
    roi = wanted[slic]
    roi[:, :] = image
    gray = cv2.cvtColor(wanted, cv2.COLOR_BGR2GRAY)
    mask = gray >= 255
    # wanted[mask] = 0
    return wanted


@bot.command(aliases=['imposter'])
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Check if somebody was and imposter", menu="fun", aliases=['imposter'])
async def check_imposter(ctx, name, avatar_url, *args, **kwargs):
    """"""
    image = get_picture(avatar_url)
    await asyncio.sleep(0.1)
    imposter = _create_imposter_image(image, name)
    await asyncio.sleep(0.1)
    file = image_to_discord_file(imposter, "imposter")
    await ctx.send(file=file)


def _create_imposter_image(image, name):
    img_path = os.path.join(os.path.dirname(__file__), "src_images", "imposter.png")
    eject_picture = cv2.imread(img_path)
    is_imposter = random.choice([True, False])
    angle = np.random.randint(15, 160)

    if is_imposter:
        text = "was the imposter."
    else:
        text = "was not the imposter."

    imposter = cv2.resize(image, (256, 256))
    imposter = imutils.rotate_bound(imposter, angle)

    rs, cs, _ = imposter.shape
    posx, posy = 400, 120
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
