from .definitions import *
from .decorators import *
from .loggers import *
from .images import *

from PIL import ImageDraw, ImageFont

import asyncio
import datetime
import imutils
import numpy as np
import cv2


@bot.command()
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Create wanted poster", example="(name) or (mention)", menu="fun")
async def wanted(ctx, user, *args, **kwargs):
    name = user.name
    avatar_url = user.avatar_url
    image = get_picture(avatar_url)
    image = cv2.resize(image, (256, 256))
    await asyncio.sleep(0.1)

    join_date = user.joined_at
    dt = datetime.datetime.now()
    duration = dt - join_date
    duration = int(duration.total_seconds()) // 60
    reward = duration

    wanted = _create_wanted_image(image, name, reward)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(wanted, "wanted")
    await ctx.send(file=file)


def _create_wanted_image(image, name, reward: int):
    img_path = os.path.join(os.path.dirname(__file__), "src_images", "wanted.jpg")
    wanted = cv2.imread(img_path)
    wanted = imutils.resize(wanted, width=310)

    crop_x = 1
    crop_y = 30
    cx, cy = 29, 90
    image = image[crop_y:-crop_y, crop_x:-crop_x, :]
    image = convert_to_sephia(image, 8, 40)
    rows, cols, channels = image.shape

    slic = (slice(cy, cy + rows), slice(cx, cx + cols), slice(None))
    roi = wanted[slic]
    roi[:, :] = image
    font_path = os.path.join(os.path.dirname(__file__), "src_fonts/BouWeste.ttf")

    wanted = image_array_to_pillow(wanted)
    draw = ImageDraw.Draw(wanted)

    font = get_font_to_bounding_box(font_path, name, max_width=257, max_height=None, initial_font_size=48)
    draw.text((155, 335), name, font=font, fill=(55, 40, 30), anchor="mm")

    reward = "$ " + f"{reward:,}"
    font = get_font_to_bounding_box(font_path, reward, max_width=250, max_height=None, initial_font_size=48)
    draw.text((280, 377), reward, font=font, fill=(30, 90, 20), anchor="rm")

    font = ImageFont.truetype(font_path, size=16)
    draw.text((35, 400), "For being in wrong place\n at wrong time.", font=font, fill=(50, 50, 50))

    wanted = image_pillow_to_array(wanted)
    return wanted


@bot.command(aliases=['imposter'])
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Check if somebody was and imposter", example="(name) or (mention)", menu="fun",
                        aliases=['imposter'])
async def check_imposter(ctx, user, *args, **kwargs):
    """"""
    name = user.name
    avatar_url = user.avatar_url

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
