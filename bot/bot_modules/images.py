from discord import File
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

from .decorators import *

import requests
import imutils
import numpy as np
import cv2
import os


def get_picture(url):
    res = requests.get(url, stream=True)
    if res.status_code != 200:
        logger.error(f"Request has incorrect code: {res.status_code}")
        return None

    try:
        "Get frame from image"
        image = np.frombuffer(res.content, dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        frame = cv2.resize(image, (256, 256))

    except Exception:
        "Get frame from gifs"
        bytes_like = BytesIO(res.content)
        imageObject = Image.open(bytes_like)
        imageObject.seek(0)
        frame = image_pillow_to_array(imageObject)

    return frame


def get_font_to_bounding_box(font_path, text, max_width, max_height, initial_font_size=50, minimal_font_size=3):
    if max_width:
        text_width = max_width + 1
    else:
        text_width = None
    if max_height:
        text_height = max_height
    else:
        text_height = None

    font_size = initial_font_size + 1
    font = None

    while (
            (max_width and text_width > max_width) or
            (max_height and text_height > max_height)) \
            and font_size > minimal_font_size:
        font_size -= 1
        font = ImageFont.truetype(font_path, size=font_size)
        text_width, text_height = font.getsize(text)

    return font


def image_array_to_pillow(matrix):
    success, img_bytes = cv2.imencode(".png", matrix)
    bytes_like = BytesIO(img_bytes)
    image = Image.open(bytes_like)
    return image


def image_pillow_to_array(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    matrix = np.frombuffer(buffer.read(), dtype=np.uint8)
    matrix = cv2.imdecode(matrix, cv2.IMREAD_COLOR)
    return matrix


def image_to_discord_file(image, filename):
    success, img_bytes = cv2.imencode(".png", image)
    if success:
        bytes_like = BytesIO(img_bytes)
        fp = File(bytes_like, filename=f"{filename}.png")
        return fp


def convert_to_sephia(image, depth=8, intense=40):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = np.array(image, dtype=int)

    image[:, :, 0] = np.mean([gray, image[:, :, 0] / 3 - intense], axis=0)
    image[:, :, 1] = np.mean([gray, image[:, :, 1] / 3 + intense], axis=0)
    image[:, :, 2] = np.mean([gray, image[:, :, 2] / 3 + (depth ** 2) + intense], axis=0)

    mask = image > 255
    image[mask] = 255
    mask = image < 0
    image[mask] = 0

    image = np.array(image, dtype=np.uint8)
    return image


def blend_to_single_color(image, color: "BGR"):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = gray / 255
    gray = gray[:, :, np.newaxis]
    image = gray * color
    image = np.array(image, dtype=np.uint8)
    return image


def create_imposter_image(image, name):
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


def create_wanted_image(avatar, name, reward: int):
    img_path = os.path.join(os.path.dirname(__file__), "src_images", "wanted.jpg")
    wanted = cv2.imread(img_path)
    wanted = imutils.resize(wanted, width=310)
    brown_dark = (55, 40, 30)
    brown_text = (59, 45, 37)
    green_dark = (30, 90, 20)

    crop_x = 1
    crop_y = 31
    cx, cy = 29, 90
    avatar = avatar[crop_y:-crop_y, crop_x:-crop_x, :]
    avatar = blend_to_single_color(avatar, (185, 204, 217))
    rows, cols, channels = avatar.shape

    slic = (slice(cy, cy + rows), slice(cx, cx + cols), slice(None))
    roi = wanted[slic]
    roi[:, :] = avatar
    pt1 = (29, 90)
    pt2 = (pt1[0] + 256 - 2 * crop_x,
           pt1[1] + 256 - 2 * crop_y)
    cv2.rectangle(wanted, pt1, pt2, (41, 45, 60), 2)

    font_path = os.path.join(os.path.dirname(__file__), "src_fonts/BouWeste.ttf")

    wanted = image_array_to_pillow(wanted)
    draw = ImageDraw.Draw(wanted)

    font = get_font_to_bounding_box(font_path, name, max_width=257, max_height=None, initial_font_size=48)
    draw.text((155, 335), name, font=font, fill=brown_text, anchor="mm")

    reward = "$ " + f"{reward:,}"
    font = get_font_to_bounding_box(font_path, reward, max_width=250, max_height=None, initial_font_size=48)
    draw.text((280, 377), reward, font=font, fill=brown_dark, anchor="rm")

    font = ImageFont.truetype(font_path, size=16)
    draw.text((35, 400), "For being in wrong place\n at wrong time.", font=font, fill=(50, 50, 50))

    wanted = image_pillow_to_array(wanted)
    return wanted


def create_hulk_taco(avatar):
    img_path = os.path.join(os.path.dirname(__file__), "src_images", "hulk_taco.jpg")
    background = cv2.imread(img_path)
    background = imutils.resize(background, width=1100)
    h, w, c = background.shape
    green_dark = (111, 159, 127)

    avatar = blend_to_single_color(avatar, green_dark)
    x_st = 290
    x_end = x_st + 256
    y_st = 55
    y_end = y_st + 256

    roi = background[y_st:y_end, x_st:x_end]

    alpha = create_circular_alpha_mask((256, 256), (120, 120), 90, feather=30)  # avatar size (256,256,3)
    alpha = alpha.reshape(256, 256, 1)

    alpha = alpha / 255
    roi[:, :] = roi * alpha + avatar * (1 - alpha)

    background = imutils.resize(background, width=1000)
    return background


def create_circular_alpha_mask(shape, center, min_radius, feather=0):
    """
    Creates alpha masks that hides point of interest of given radius and feather
    Args:
        shape:
        center:
        min_radius:
        feather:

    Returns:

    """
    h, w = shape
    if center is None:
        center = (int(w / 2), int(h / 2))
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

    mask = dist_from_center <= min_radius
    mask_feather = dist_from_center <= (min_radius + feather)
    rest = ~(mask | mask_feather)

    dist_from_center = (dist_from_center - min_radius) / (feather) * 255
    dist_from_center[mask] = 0
    dist_from_center[rest] = 255

    return dist_from_center
