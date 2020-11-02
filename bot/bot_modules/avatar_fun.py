from .definitions import *
from .decorators import *
from .loggers import *
from .images import *

import asyncio
import datetime
import cv2


@bot.command(aliases=['hulk'])
@advanced_args_function(bot)
@get_author_name_and_picture_ifnotmentioned(bot)
@log_call_function
@my_help.help_decorator("Create hulk with taco", example="(name) or (mention)", menu="fun", aliases=['hulk'])
async def taco(ctx, user, *args, **kwargs):
    name = user.name
    avatar_url = user.avatar_url

    avatar = get_picture(avatar_url)
    await asyncio.sleep(0.1)

    image = create_hulk_taco(avatar)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(image, "hulk")
    await ctx.send(file=file)


@bot.command()
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Create wanted poster", example="(name) or (mention)", menu="fun")
async def wanted(ctx, user, *args, **kwargs):
    name = user.name
    avatar_url = user.avatar_url
    avatar = get_picture(avatar_url)
    await asyncio.sleep(0.1)

    join_date = user.joined_at
    dt = datetime.datetime.now()
    duration = dt - join_date
    duration = int(duration.total_seconds()) // 60
    reward = duration

    image = create_wanted_image(avatar, name, reward)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(image, "wanted")
    await ctx.send(file=file)


@bot.command(aliases=['check_imposter'])
@advanced_args_function(bot)
@find_one_member_name_and_picture(bot)
@log_call_function
@my_help.help_decorator("Check if somebody was an imposter", example="(name) or (mention)", menu="fun",
                        aliases=['check_imposter'])
async def imposter(ctx, user, *args, **kwargs):
    """"""
    name = user.name
    avatar_url = user.avatar_url

    avatar = get_picture(avatar_url)
    await asyncio.sleep(0.1)

    image = create_imposter_image(avatar, name)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(image, "imposter")
    await ctx.send(file=file)
