from .definitions import *
from .decorators import *
from .permissions import *

from ast import literal_eval

from discord.ext import commands
from discord import Embed

import random
import numpy as np
import asyncio


@bot.command(aliases=['create_role_colors', 'create_color_roles'])
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@log_call_function
@my_help.help_decorator("Create colors that do not exist. Use keyword to update existing.",
                        '(update)',
                        menu="role", aliases=['create_role_colors', 'create_color_roles'])
async def create_colors(ctx, key=None, *args, update=False, **kwargs):
    guild = ctx.message.guild
    top = 1
    for role in guild.roles:
        if role.name == "YasiuApp":
            top = role.position - 1
    top = 1 if top < 1 else top

    roles = ROLE_COLORS.copy()
    dc = {role.name: role for role in guild.roles}
    params = {'mentionable': False, 'hoist': False, "reason": f"Called by {ctx.author}"}

    if not update:
        if type(key) is str and ("update" in key.lower() or "refresh" in key.lower()):
            update = True
        else:
            update = False

    for name, value in roles.items():
        color = value['color']
        if name not in dc:
            logger.debug(f"Creating role: {name}")
            role = await guild.create_role(name=name, color=Colour.from_rgb(*color), **params)
            await role.edit(position=top)
            # top += 1
        else:
            if update:
                logger.debug(f"Editing role: {name}")
                await dc[name].edit(color=Colour.from_rgb(*color), position=top, **params)

    server_roles = ctx.guild.roles
    new_roles_mentions = {role.name: role.mention for role in server_roles if role.name in roles}
    roles_text_in_order = ' '.join(new_roles_mentions[role] for role in roles)

    embed = Embed(title="Colors:", description=roles_text_in_order)
    embed.set_author(name="!color")
    await ctx.send(embed=embed)


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@approve_fun
@log_call_function
@my_help.help_decorator("Show roles on server", menu="role")
async def show_roles(ctx, *args, **kwargs):
    """
    Show all roles on this server.
    Args:
        ctx:
        *args:
        **kwargs:

    Returns:

    """
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
@my_help.help_decorator("Create smooth colored roles. Name of game, max level, level interval.",
                        "name max step start=(r,g,b) stop=(r,g,b)",
                        menu="role")
async def create_color_levels(ctx, name, end_level, level_step, *args, start, stop, dry=False, **kwargs):
    """
    Create roles with given name, and every level.
    Use -d or dry to dryrun command
    Args:
        ctx:
        name: game name, this will be prefix of game
        end_level: (max) this will be final top level role
        level_step: interval for levels
        *args:
        start: (r,g,b), starting color, avoid using space
        stop: (r,g,b), ending color, avoid using space
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
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@my_help.help_decorator("Remove roles mentioned in command", menu="role")
async def remove_role(ctx, *args, dry=False, **kwargs):
    mentions = ctx.message.role_mentions

    count = 0
    for role in mentions:
        try:
            if not dry:
                await role.delete()
            count += 1
        except Exception:
            pass
    if not dry:
        text = f"Removed {count} roles"
        logger.info(text + f" at {ctx.guild}")
        await ctx.send(text)
    else:
        await ctx.send(f"This will remove {count} roles")


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@delete_call
@my_help.help_decorator("Select role with color. !color will show you available colors", "<color>|random", menu="role")
async def color(ctx, selection=None, *args, **kwargs):
    """
    Command for editing member colors.
    Args:
        ctx:
        selection:
        *args:
        **kwargs:

    Returns:

    """
    all_colors = [role for role in ctx.guild.roles if role.name in ROLE_COLORS]

    if not selection:
        roles_on_server = [role for role in all_colors if role.name not in ctx.guild.roles]
        if not roles_on_server:
            await ctx.send("There are no color roles on servers.", delete_after=60)
            return None

        server_roles = ctx.guild.roles
        new_roles_mentions = {role.name: role.mention for role in server_roles if role.name in ROLE_COLORS}
        roles_text_in_order = ' '.join([new_roles_mentions.get(role, '') for role in ROLE_COLORS])

        embed = Embed(title=f"Select one of colors {len(new_roles_mentions)}:", description=roles_text_in_order)
        embed.set_author(name="!color color  or  !color random")
        await ctx.send(embed=embed)
        return None

    if type(selection) is str and selection.lower() == "random" or "rand" in selection.lower():
        new_color = await set_member_single_role(ctx.author, ctx.guild, ROLE_COLORS.keys(), allow_random=True)
        embed = Embed(title=f"{ctx.author.name} is now", description=new_color.mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed, delete_after=240)
        return None

    selected_list = [role for role in ctx.guild.roles if selection.lower() in role.name.lower()]

    if not selected_list:
        await ctx.send("Not found matching role", delete_after=60)
        return None

    new_color = await set_member_single_role(ctx.author, ctx.guild, ROLE_COLORS.keys(), selection)
    if not new_color:
        "Color not in ROLE_COLORS"
        await ctx.send(f"This color is not valid: {selection}", delete_after=60)

    else:
        "Color in ROLE_COLORS"
        embed = Embed(title=f"{ctx.author.name} is now", description=new_color.mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed, delete_after=240)


async def set_member_single_role(member, guild, roles_names,
                                 selection_text=None,
                                 allow_random=False,
                                 find_in_name=True):
    """
    Set member role to color or random
    Args:
        member:
        guild:
        roles_names:
        selection_text: find role by its name, if more than 1, first role is selected from exact list if possible
        allow_random: Select random role if nothing matches
        find_in_name: Partial name finding

    Returns:

    """
    current = set(role for role in member.roles if role.name in roles_names and role.name != "@everyone")
    available_roles = [role for role in guild.roles if role.name in roles_names and role.name != "@everyone"]

    if not available_roles:
        logger.debug(f"no available roles")
        return None

    logger.debug(f"Selection text: {selection_text}")
    if type(selection_text) is str and "random" in selection_text.lower():
        random_role = True
    else:
        random_role = False

    if selection_text and not random_role:
        if find_in_name:
            matching_list = [role for role in available_roles if selection_text.lower() in role.name.lower()]
        else:
            matching_list = []
        exact_list = [role for role in available_roles if selection_text.lower() == role.name.lower()]

        if not matching_list:
            logger.debug(f"not matching list")
            return None

        if find_in_name and len(matching_list) == 1:
            selected_role = matching_list[0]
        elif find_in_name and len(matching_list) > 1:
            try:
                selected_role = exact_list[0]
            except IndexError:
                selected_role = matching_list[0]
        elif exact_list:
            selected_role = exact_list[0]
        else:
            selected_role = None

        if selected_role:
            try:
                current.remove(selected_role)
            except KeyError:
                pass

            await member.add_roles(selected_role)

            if current:
                await member.remove_roles(*current)
            return selected_role
        else:
            logger.debug(f"No role was selected")

    if (allow_random or random_role) and available_roles:
        n = 0
        new_role = random.choice(available_roles)

        while n < 10:
            n += 1
            new_role = random.choice(available_roles)
            if new_role not in current:
                break

        if new_role:
            try:
                current.remove(new_role)
            except KeyError:
                pass

            await member.add_roles(new_role)

            if current:
                await member.remove_roles(*current)
            return new_role


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(is_bot_owner, restrictions=is_not_priv)
@log_call_function
@approve_fun
async def test_reaction(ctx, *args, **kwargs):
    server_roles = {role.name: role for role in ctx.guild.roles}
    text_half = ""
    text_end = ""
    pivot = 'LemonGrass'
    end_half = False

    "Send Embed Messages"
    for name, value in ROLE_COLORS.items():
        role = server_roles.get(name, None)
        if not role:
            continue

        if role.name == pivot:
            text_half += f"\n{value['emoji']} {role.mention}"
            end_half = True
        elif not end_half:
            text_half += f"\n{value['emoji']} {role.mention}"
        else:
            text_end += f"\n{value['emoji']} {role.mention}"

    text_end += f"\n{EMOJIS['repeat_one']} Random"

    embed_half = Embed(description=text_half)
    embed_end = Embed(description=text_end)
    rolemenu_half = await ctx.send(embed=embed_half)
    rolemenu_end = await ctx.send(embed=embed_end)

    role_menu_pair = (rolemenu_half.id, rolemenu_end.id)
    my_config.add_rolemenu_color_pair(role_menu_pair)

    "Add Reactions"
    end_half = False
    for name, value in ROLE_COLORS.items():
        emoji = value['emoji']
        if name == pivot:
            end_half = True
            await rolemenu_half.add_reaction(emoji)
        elif not end_half:
            await rolemenu_half.add_reaction(emoji)
        else:
            await rolemenu_end.add_reaction(emoji)
        await asyncio.sleep(0.02)
    await rolemenu_end.add_reaction(EMOJIS['repeat_one'])


async def check_and_assign_reaction_color_role(member, message_id, channel_id, guild, emoji):
    if member.bot:
        return None

    valid = my_config.color_pairs.check_if_in(message_id)
    if not valid:
        return None

    emoji_to_name_dict = {item['emoji']: name for name, item in ROLE_COLORS.items()}
    emoji_to_name_dict.update({EMOJIS['repeat_one']: "random"})

    if emoji not in emoji_to_name_dict:
        return None
    logger.debug(f"Color emoji check correct: {emoji}")
    selection = emoji_to_name_dict.get(emoji, None)

    if not selection:
        return None

    coro_name = f"{guild.name}-color-{member.name}"
    loop = asyncio.get_event_loop()
    await asyncio.sleep(0.1)

    for task in asyncio.all_tasks():
        if task.get_name() == coro_name:
            task.cancel()
            logger.debug(f"Canceled during: {emoji}")

    key, value = my_config.color_pairs.get_pair(message_id)
    coro = job_add_role_clear_reaction(selection, guild, channel_id, [key, value], set(emoji_to_name_dict.keys()),
                                       emoji, member)
    task = loop.create_task(coro, name=coro_name)

    while not task.done():
        await asyncio.sleep(1)
        if task.cancelled():
            return None
    "Make sure that user did not spammed emojis"
    color = await set_member_single_role(member, guild, ROLE_COLORS.keys(), selection)
    logger.debug(f"Reaction finished: {emoji}")
    return color


async def job_add_role_clear_reaction(selection, guild,
                                      channel_id, messages_ids,
                                      emojis_to_remove, skip_emojis,
                                      member):
    await set_member_single_role(member, guild, ROLE_COLORS.keys(), selection)
    await clear_reactions(channel_id, messages_ids, emojis_to_remove, skip_emojis, member)
    # color = await set_member_single_role(member, guild, ROLE_COLORS.keys(), selection)


async def clear_reactions(channel_id, messages_ids, emojis_to_remove, skip_emojis, member):
    """
    Universal function, to clear emojis from selected user.
    Args:
        channel_id:
        messages_ids:
        emojis_to_remove:
        skip_emojis:
        member:

    Returns:

    """
    "Create sets, to operate faster"
    messages_ids = set(messages_ids)
    emojis_to_remove = set(emojis_to_remove)
    skip_emojis = set(skip_emojis)
    channel = bot.get_channel(channel_id)

    logger.debug(f"Emojis to remove: {emojis_to_remove}")
    logger.debug(f"skip emojis : {skip_emojis}")

    for msg_id in messages_ids:
        message = await channel.fetch_message(msg_id)
        for reaction in message.reactions:
            await asyncio.sleep(0.01)
            if str(reaction.emoji) in skip_emojis:
                continue

            if str(reaction.emoji) not in emojis_to_remove:
                continue

            users = await reaction.users().flatten()
            this_user = [user for user in users if user.id == member.id]
            if this_user:
                await asyncio.sleep(0.01)
                await message.remove_reaction(reaction.emoji, member)
                logger.debug(f"Removed {reaction.emoji}")


@bot.event
async def on_raw_reaction_add(payload):
    message_id = payload.message_id
    user_id = payload.user_id
    channel_id = payload.channel_id
    guild_id = payload.guild_id
    emoji = payload.emoji.name
    member = payload.member
    try:
        guild = member.guild
    except AttributeError as err:
        return None

    await check_and_assign_reaction_color_role(member, message_id, channel_id, member.guild, emoji)


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=[is_not_priv, is_bot_owner])
@log_call_function
@approve_fun
async def showconfig(ctx, *args, **kwargs):
    text = my_config.color_pairs.__str__()
    await ctx.send(text)
