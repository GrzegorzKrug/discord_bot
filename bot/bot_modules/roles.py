from .definitions import *
from .decorators import *
from .permissions import *

from ast import literal_eval

from discord.ext import commands

import numpy as np


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@log_call_function
@my_help.help_decorator("Create basic roles.py with colors", menu="role")
async def create_color_roles(ctx, *args, **kwargs):
    guild = ctx.message.guild
    roles = ROLE_COLORS.copy()

    dc = {role.name: role for role in guild.roles}
    params = {'mentionable': False, 'hoist': False}
    for name, color in roles.items():
        if name not in dc:
            logger.debug("Creating role: {}")
            await guild.create_role(name=name, color=Colour.from_rgb(*color), **params)
        else:
            print(f"editing role: {name}")
            await dc[name].edit(color=Colour.from_rgb(*color), **params)
    all_roles = ctx.guild.roles

    debug_colors = {role.name: role.mention for role in all_roles if role.name in roles}
    await ctx.send(' '.join(debug_colors[role] for role in roles))


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@my_help.help_decorator("Show roles.py on server", menu="role")
async def roles(ctx, *args, **kwargs):
    guild = ctx.message.guild
    txt_start = 'Roles: '
    role_text = []
    for role in guild.roles[1:]:
        role_text.append(role.mention)

    while len(role_text) > 0:
        text = txt_start
        for i, role in enumerate(role_text):
            new_text = text + f" {role}"

            if len(new_text) > 2_000:
                await ctx.send(text)
                text = ""
                role_text = role_text[i:]
                break
            else:
                text = new_text
        else:
            await ctx.send(text)
            break


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@approve_fun
@my_help.help_decorator("Create smooth colored roles.py",
                        "<name> <end_level> <level_step> start=(r,g,b) stop=(r,g,b)",
                        menu="role")
async def smooth_role_levels(ctx, name, end_level, level_step, *args, start, stop, **kwargs):
    guild = ctx.message.guild

    name = name.title()
    level_step = int(level_step)
    end_level = int(end_level)

    start = literal_eval(start)
    stop = literal_eval(stop)

    start = tuple(int(num) for num in start)
    stop = tuple(int(num) for num in stop)
    assert len(start) == 3 and len(stop) == 3

    levels = [*range(level_step, end_level + 1, level_step)]
    num = len(levels)
    red = np.linspace(start[0], stop[0], num)
    green = np.linspace(start[1], stop[1], num)
    blue = np.linspace(start[2], stop[2], num)
    roles = {}
    for x, (level, color) in enumerate(zip(levels, zip(red, green, blue))):
        color = tuple([int(c) for c in color])
        roles.update({f"yasiu_{name}_{level}": color})

    dc = {role.name: role for role in guild.roles}
    params = {'mentionable': False, 'hoist': False}
    for name, color in roles.items():
        if name not in dc:
            print(f"adding role: {name}")
            await guild.create_role(name=name, color=Colour.from_rgb(*color), **params)
        else:
            print(f"editing role: {name}")
            await dc[name].edit(color=Colour.from_rgb(*color), **params)

    all_roles = ctx.guild.roles
    debug_colors = [role.mention for role in all_roles if role.name in roles]
    await ctx.send("Roles: " + ' '.join(debug_colors))


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@my_help.help_decorator("Removes all rolles added with smooth color", menu="role")
async def purge_yasiu_roles(ctx, *args, **kwargs):
    count = 0
    for role in ctx.guild.roles:
        if role.name.startswith("yasiu_"):
            try:
                await role.delete()
                count += 1
            except Exception:
                pass
    text = f"Removed {count} Yasiu's roles.py"
    logger.info(text + f" at {ctx.guild}")
    await ctx.send(text)
