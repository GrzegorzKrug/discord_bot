from discord import File
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


def image_to_discord_file(image, filename):
    success, img_bytes = cv2.imencode(".png", image)
    if success:
        bytes_like = BytesIO(img_bytes)
        fp = File(bytes_like, filename=f"{filename}.png")
        return fp


def convert_to_sephia(image, depth, intense):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = np.array(image, dtype=int)

    image[:, :, 0] = np.mean([gray, image[:, :, 0] / 2 - intense], axis=0)
    image[:, :, 1] = np.mean([gray, image[:, :, 1] / 2 + intense], axis=0)
    image[:, :, 2] = np.mean([gray, image[:, :, 2] + (depth ** 2) + intense], axis=0)

    mask = image > 255
    image[mask] = 255
    mask = image < 0
    image[mask] = 0

    image = np.array(image, dtype=np.uint8)
    return image
