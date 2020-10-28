from discord import File
from PIL import Image, ImageFont
from io import BytesIO

import discord

from .decorators import *

import requests
import numpy as np
import cv2


def get_picture(url):
    res = requests.get(url, stream=True)
    if res.status_code != 200:
        logger.error(f"Request has incorrect code: {res.status_code}")
        return None

    image = np.frombuffer(res.content, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


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