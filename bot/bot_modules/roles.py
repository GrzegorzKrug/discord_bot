from .definitions import *
from .decorators import *
from .permissions import *

from ast import literal_eval

from discord.ext import commands
from discord import Embed

import random
import numpy as np


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@log_call_function
@my_help.help_decorator("Create basic roles with colors", menu="role")
async def create_color_roles(ctx, *args, **kwargs):
    guild = ctx.message.guild
    roles = ROLE_COLORS.copy()

    dc = {role.name: role for role in guild.roles}
    params = {'mentionable': False, 'hoist': False}
    for name, color in roles.items():
        if name not in dc:
            logger.debug(f"Creating role: {name}")
            await guild.create_role(name=name, color=Colour.from_rgb(*color), **params)
        else:
            logger.debug(f"Editing role: {name}")
            await dc[name].edit(color=Colour.from_rgb(*color), **params)
    all_roles = ctx.guild.roles

    debug_colors = {role.name: role.mention for role in all_roles if role.name in roles}
    await ctx.send(' '.join(debug_colors[role] for role in roles))


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@log_call_function
@my_help.help_decorator("Show roles.py on server", menu="role")
async def roles(ctx, *args, **kwargs):
    guild = ctx.message.guild
    txt_start = ''
    role_text = []
    for role in guild.roles[1:]:
        role_text.append(role.mention)

    while len(role_text) > 0:
        text = txt_start
        for i, role in enumerate(role_text):
            new_text = text + f" {role}"

            if len(new_text) > 2_000:
                embed = Embed(title="Roles:", description=text)
                await ctx.send(embed=embed)
                text = ""
                role_text = role_text[i:]
                break
            else:
                text = new_text
        else:
            embed = Embed(title="Roles:", description=text)
            await ctx.send(embed=embed)
            break


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@approve_fun
@my_help.help_decorator("Create smooth colored roles.py",
                        "name max_level step start=(r,g,b) stop=(r,g,b)",
                        menu="role")
async def create_color_levels(ctx, name, end_level, level_step, *args, start, stop, dry=False, **kwargs):
    """
    Create roles with given name, and every level.
    Use -d or dry to dryrun command
    Args:
        ctx:
        name:
        end_level:
        level_step:
        *args:
        start:
        stop:
        **kwargs:

    Returns:

    """
    guild = ctx.message.guild

    name = name.title()
    level_step = int(level_step)
    end_level = int(end_level)

    start = "".join(start)
    stop = "".join(stop)

    logger.debug(start)
    logger.debug(stop)
    try:
        start = literal_eval(start)
        stop = literal_eval(stop)
    except Exception:
        await ctx.send("Please do not use spaces in ()")
        return None

    start = tuple(int(num) for num in start)
    stop = tuple(int(num) for num in stop)

    if len(start) != 3 or len(stop) != 3:
        await ctx.send("You gave incorrect colors")
        return None

    levels = [*range(level_step, end_level + 1, level_step)]

    num = len(levels)
    red = np.linspace(start[0], stop[0], num)
    green = np.linspace(start[1], stop[1], num)
    blue = np.linspace(start[2], stop[2], num)

    if dry:
        await ctx.send(f"This will create {num} roles")
        return None
    elif len(levels) > 100:
        await ctx.send(f"This will add more than 100 roles: {len(levels)} \n"
                       f"I can't do that. You can have only 250 roles max.")
        return None

    roles = {}
    for x, (level, color) in enumerate(zip(levels, zip(red, green, blue))):
        color = tuple([int(c) for c in color])
        roles.update({f"yasiu_{name}_{level}": color})

    dc = {role.name: role for role in guild.roles}
    params = {'mentionable': False, 'hoist': False}
    for name, color in roles.items():
        if name not in dc:
            logger.debug(f"adding role: {name}")
            await guild.create_role(name=name, color=Colour.from_rgb(*color), **params)
        else:
            logger.debug(f"editing role: {name}")
            await dc[name].edit(color=Colour.from_rgb(*color), **params)

    all_roles = ctx.guild.roles
    debug_colors = [role.mention for role in all_roles if role.name in roles]
    logger.info(f"Added {len(debug_colors)} roles in {ctx.guild}")
    await ctx.send("Roles: " + ' '.join(debug_colors))


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@my_help.help_decorator("Removes all roles added with smooth color", menu="role")
async def remove_yasiu_roles(ctx, *args, dry=False, **kwargs):
    count = 0

    for role in ctx.guild.roles:
        if role.name.startswith("yasiu_"):
            try:
                if not dry:
                    await role.delete()
                count += 1
            except Exception:
                pass
    if not dry:
        text = f"Removed {count} Yasiu's roles"
        logger.info(text + f" at {ctx.guild}")
        await ctx.send(text)
    else:
        await ctx.send(f"This will remove {count} roles")


@bot.command()
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@my_help.help_decorator("Removes all color roles made by YasiuBot", menu="role")
async def remove_yasiu_colors(ctx, *args, dry=False, **kwargs):
    count = 0

    for role in ctx.guild.roles:
        if role.name in ROLE_COLORS:
            try:
                if not dry:
                    await role.delete()
                count += 1
            except Exception:
                pass
    if not dry:
        text = f"Removed {count} Yasiu's color roles"
        logger.info(text + f" at {ctx.guild}")
        await ctx.send(text)
    else:
        await ctx.send(f"This will remove {count} color roles")


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@delete_call
@my_help.help_decorator("Select role with color. !color will show you available colors", "<color>|random", menu="role")
async def color(ctx, selection=None, *args, **kwargs):
    all_colors = [role for role in ctx.guild.roles if role.name in ROLE_COLORS]

    if not selection:
        roles_on_server = [role for role in all_colors if role.name not in ctx.guild.roles]
        if not roles_on_server:
            await ctx.send("There are no color roles.")
            return None

        desc = " ".join([role.mention for role in roles_on_server])
        embed = Embed(title="Select one of colors:", description=desc)
        embed.set_author(name="!color color  or  !color random")
        await ctx.send(embed=embed)
        return None

    current = [role for role in ctx.author.roles if role.name in ROLE_COLORS]
    if type(selection) is str and selection.lower() == "random":
        new_color = await set_member_color(ctx.author, ctx.guild)
        embed = Embed(title=f"{ctx.author.name} is now", description=new_color.mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed, delete_after=240)
        return None

    selected_list = [role for role in ctx.guild.roles if selection.lower() in role.name.lower()]

    if not selected_list:
        await ctx.send("Not found matching role")
        return None

    if len(selected_list) > 1:
        _selected_list = [role for role in selected_list if role.name.lower() == selection.lower()]
        if len(_selected_list) == 1:
            selected_list = _selected_list

    selected_color = selected_list[0]

    if selected_color.name not in ROLE_COLORS:
        "Color not in ROLE_COLORS"
        await ctx.send(f"This color is not valid: {selection}")

    else:
        "Color in ROLE_COLORS"
        await ctx.author.remove_roles(*current)
        await ctx.author.add_roles(selected_color)

        embed = Embed(title=f"{ctx.author.name} is now", description=selected_color.mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed, delete_after=240)


async def set_member_color(member, guild, selection=None):
    """
    Set member role to color or random
    Args:
        member:
        guild:
        new_color:

    Returns:

    """
    current = [role for role in member.roles if role.name in ROLE_COLORS]
    colors = [role for role in guild.roles if role.name in ROLE_COLORS]
    if not colors:
        return None

    n = 0
    new_color = random.choice(colors)

    if selection:
        selected_list = [role for role in guild.roles if selection.lower() in role.name.lower()]
        if selected_list:
            selected_color = selected_list[0]

            if selected_color.name not in ROLE_COLORS:
                if current:
                    await member.remove_roles(*current)
                await member.add_roles(new_color)
                return selected_color

    while n < 20:
        n += 1
        new_color = random.choice(colors)
        if new_color not in current:
            break

    if new_color:
        if current:
            await member.remove_roles(*current)
        await member.add_roles(new_color)
        return new_color
