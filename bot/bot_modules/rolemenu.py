from .definitions import *
from .decorators import *
from .permissions import *
from .config import my_config
from .roles import set_member_single_role_by_id

from discord.ext import commands
from discord import Embed

import random
import numpy as np
import asyncio


@bot.command(aliases=['rm', 'rolemenu'])
@commands.has_permissions(manage_roles=True)
@advanced_args_function(bot)
@advanced_perm_check_function(restrictions=is_not_priv)
@log_call_function
@approve_fun
@my_help.help_decorator(
        "Command for managing role menus.", "add|remove|edit|refresh",
        menu='role',
        aliases=['rm', 'rolemenu'],
        actions={"create": "Create role menu from scratch or predefined",
                 "remove": "Remove role menu defined by Yasiu",
                 "show": "Show currently defined role menus on this server"}
)
async def role_menu(ctx, action=None, menu=None, *args, **kwargs):
    action = str(action).lower()
    menu = str(menu).lower()

    if action == "add" or action == "create":
        logger.debug(f"Adding role menu for {menu}")
        if menu == "color":
            await add_role_menu_colors(ctx, action, menu, 'single')

    elif action == "remove" or action == "del" or action == "delete":
        logger.debug(f"Removing role menu for {menu}")
        if menu == "color":
            await job_rolemenu_remove(ctx.guild.id, 'color')

    elif action == "show":
        rolemenus = list(my_config.show_server_role_menus(ctx.guild.id))
        text = ", ".join(rolemenus)
        text = "Currently defined role menus:\n" + text
        await ctx.send(text)

    else:
        actions = "create", "remove", "show"  # ,"update","edit"
        await ctx.send(f"Available actions ```{', '.join(actions)}```")


async def job_rolemenu_remove(guild_id, name):
    menu = my_config.get_role_menu_name(guild_id, name)
    if menu:
        chan_id = menu['channel_id']
        channel = bot.get_channel(chan_id)
        for msg_id in menu['message_ids']:
            try:
                message = await channel.fetch_message(msg_id)
            except Exception as err:
                logger.debug(f"{err}")
                continue

            try:
                await message.delete()
            except Exception as err:
                logger.warning(f"Error during message removing: {err}")

    my_config.remove_role_menu(guild_id, name)


@bot.command()
@advanced_args_function(bot)
@advanced_perm_check_function(is_bot_owner, restrictions=is_not_priv)
@log_call_function
@approve_fun
async def add_role_menu_colors(ctx, *args, **kwargs):
    server_roles = {role.name: role for role in ctx.guild.roles}
    text_half = ""
    text_end = ""
    pivot = 'LemonGrass'
    end_half = False

    exists = my_config.get_role_menu_name(ctx.guild.id, 'color')
    logger.debug(f"Checking if exists: {exists}")
    if exists:
        await ctx.send("This server already has role menu for colors.")
        return None

    "Send Embed Messages"
    emoji_dict = {}
    for name, value in ROLE_COLORS.items():
        role = server_roles.get(name, None)
        if not role:
            continue
        emoji_dict.update({value['emoji']: role.id})
        if role.name == pivot:
            text_half += f"\n{value['emoji']} {role.mention}"
            end_half = True
        elif not end_half:
            text_half += f"\n{value['emoji']} {role.mention}"
        else:
            text_end += f"\n{value['emoji']} {role.mention}"

    text_end += f"\n{EMOJIS['repeat_one']} Random"
    emoji_dict.update({EMOJIS['repeat_one']: "random"})

    embed_half = Embed(description=text_half)
    embed_end = Embed(description=text_end)
    rolemenu_half = await ctx.send(embed=embed_half)
    rolemenu_end = await ctx.send(embed=embed_end)

    try:
        await rolemenu_half.pin()
        await rolemenu_end.pin()
    except Exception as err:
        pass

    my_config.add_role_menu(ctx.guild.id, 'color', emoji_dict, [rolemenu_half.id, rolemenu_end.id],
                            ctx.channel.id, 'single')

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
    await ctx.message.delete(delay=30)


async def check_and_assign_reaction_color_role(member, message_id, channel_id, guild, emoji):
    if member.bot:
        return None

    menu = my_config.get_role_menu_id(guild.id, message_id)

    logger.debug(f"Checked menu: {bool(menu)}")
    if not menu:
        return None

    emoji_to_role = menu['emojis_roles']
    role_type = menu['role_type']

    if emoji not in emoji_to_role:
        return None

    logger.debug(f"Color emoji check correct: {emoji}")
    selection = emoji_to_role.get(emoji, None)

    if not selection:
        return None

    coro_name = f"{guild.name}-{menu['name']}-{member.name}"
    loop = asyncio.get_event_loop()
    await asyncio.sleep(0.1)

    for task in asyncio.all_tasks():
        if task.get_name() == coro_name:
            task.cancel()
            logger.debug(f"Canceled during: {emoji}")

    menu = my_config.get_role_menu_id(guild.id, message_id)
    message_ids = menu['message_ids']

    coro = job_add_role_clear_reactions(selection, guild, channel_id, message_ids, emoji_to_role, emoji_to_role.keys(),
                                        {emoji}, member)
    task = loop.create_task(coro, name=coro_name)

    while not task.done():
        await asyncio.sleep(1)
        if task.cancelled():
            return None
    "Make sure that user did not spammed emojis"
    color = await set_member_single_role_by_id(member, guild, emoji_to_role, selection)
    logger.debug(f"Reaction finished: {emoji}")
    return color


async def job_add_role_clear_reactions(selection, guild, channel_id, message_ids,
                                       emoji_to_role, emojis_to_remove, skip_emojis,
                                       member):
    await set_member_single_role_by_id(member, guild, emoji_to_role, selection)
    await clear_reactions(channel_id, message_ids, emojis_to_remove, skip_emojis, member)
    # color = await set_member_single_role_by_id(member, guild, ROLE_COLORS.keys(), selection)


async def clear_reactions(channel_id, message_ids, emojis_to_remove, skip_emojis, member):
    """
    Universal function, to clear emojis from selected user.
    Args:
        channel_id:
        message_ids:
        emojis_to_remove:
        skip_emojis:
        member:

    Returns:

    """
    "Create sets, to operate faster"
    message_ids = set(message_ids)
    emojis_to_remove = set(emojis_to_remove)
    skip_emojis = set(skip_emojis)
    channel = bot.get_channel(channel_id)

    logger.debug(f"Emojis to remove: {emojis_to_remove}")
    logger.debug(f"skip emojis : `{skip_emojis}`")

    for msg_id in message_ids:
        message = await channel.fetch_message(msg_id)
        for reaction in message.reactions:
            await asyncio.sleep(0.01)
            if str(reaction.emoji) in skip_emojis:
                logger.debug(f"Skipped: {reaction.emoji}")
                continue

            if str(reaction.emoji) not in emojis_to_remove:
                logger.debug(f"Don't remove that, skip: {reaction.emoji}")
                continue

            users = await reaction.users().flatten()
            this_user = [user for user in users if user.id == member.id]
            if this_user:
                await message.remove_reaction(reaction.emoji, member)
                logger.debug(f"Removed {reaction.emoji}")
            else:
                logger.debug(f"Nothing happened: {reaction.emoji}")


@bot.event
async def on_raw_reaction_add(payload):
    message_id = payload.message_id
    user_id = payload.user_id
    channel_id = payload.channel_id
    guild_id = payload.guild_id
    emoji = payload.emoji
    em_name = emoji.name
    member = payload.member

    logger.debug(f"reaction: '{emoji.name}' ")
    logger.debug(f"ID:       {emoji.id}")
    logger.debug(f"Custom?:  {emoji.is_custom_emoji()}")
    logger.debug(f"Unicode?: {emoji.is_unicode_emoji()}")
    logger.debug(f"bytes:    {bytes(emoji.name, encoding='utf-8')}")

    try:
        guild = member.guild
    except AttributeError as err:
        return None

    await check_and_assign_reaction_color_role(member, message_id, channel_id, member.guild, em_name)
