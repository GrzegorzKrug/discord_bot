from .definitions import *
from .decorators import *
from .loggers import *
from .images import *



import asyncio
import datetime
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

    wanted = create_wanted_image(image, name, reward)
    await asyncio.sleep(0.1)

    if DEBUG_IMAGES:
        cv2.imwrite("debug_wanted.png", wanted)
    else:
        file = image_to_discord_file(wanted, "wanted")
        await ctx.send(file=file)





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

    imposter = create_imposter_image(image, name)
    await asyncio.sleep(0.1)

    file = image_to_discord_file(imposter, "imposter")
    await ctx.send(file=file)



