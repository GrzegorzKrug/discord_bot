import discord
import asyncio
import random
import time
import re

from .permissions import CommandWithoutPermissions
from .definitions import send_disapprove, logger, EMOJIS
from .definitions import YOUSHISU_ID

from discord.ext.commands import CommandError
from discord import HTTPException, NotFound


def string_mention_converter(bot, guild, text: "input str", bold_name=True) -> "String":
    user_pattern = re.compile(r"<@!(\d+)>")
    role_pattern = re.compile(r"<@&(\d+)>")
    new_text = text

    new_text = new_text.replace("@everyone", "<everyone>")
    new_text = new_text.replace("@here", "<here>")

    user_list = user_pattern.findall(text)
    role_list = role_pattern.findall(text)

    for user in user_list:
        try:
            user_name = bot.get_user(int(user)).name
        except AttributeError:
            user_name = f"{user}"
        if bold_name:
            new_text = new_text.replace(f"<@!{user}>", f"@**{user_name}**")
        else:
            new_text = new_text.replace(f"<@!{user}>", f"@{user_name}")

    for role in role_list:
        try:
            roleid = int(role)
            role_name = guild.get_role(roleid).name
        except AttributeError as err:
            logger.error(f"Error in string_mention_converter {err}")
            role_name = f"{role}"
        new_text = new_text.replace(f"<@&{role}>", f"@*{role_name}*")
    return new_text


def check_query_method(coro):
    async def decorator(cls, ctx, *args, **kwargs):
        try:
            result = await coro(cls, ctx, *args, **kwargs)
            return result
        except HTTPException as err:
            logger.error(err)
            await send_disapprove(ctx)
            await ctx.send("Message is too long. Can not send results.")

        except AttributeError as err:
            logger.error(err)
            await send_disapprove(ctx)
            await ctx.send("Invalid query")

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__

    return decorator


def check_query_function(coro):
    async def decorator(cls, ctx, *args, **kwargs):
        try:
            result = await coro(cls, ctx, *args, **kwargs)
            return result
        except HTTPException as err:
            logger.error(err)
            await send_disapprove(ctx)
            await ctx.send("Message is too long. Can not send results.")

        except AttributeError as err:
            logger.error(err)
            await send_disapprove(ctx)
            await ctx.send("Invalid query")

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__

    return decorator


def log_duration_any(coro):
    async def decorator(*args, **kwargs):
        start = time.time()
        result = await coro(*args, **kwargs)
        stop = time.time()
        logger.debug(f"Duration of {coro.__name__} is {stop - start:<5.2f}s")
        return result

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__

    return decorator


def _get_advanced_args(bot, ctx, *args, bold_name=False, **kwargs):
    if not kwargs:
        kwargs = {"force": False, "dry": False, "sudo": False}

    good_args = list()
    text_args = []
    args, kwargs = _get_advanced_kwargs(bot, ctx, *args, **kwargs, bold_name=bold_name)
    args = list(args)

    for arg in args:
        if arg:
            if ',' in arg:
                arg, *rest = arg.split(',')
                for _rest in rest:
                    args.append(_rest)
            good_args.append(arg)
            text_args.append(arg)
        else:
            logger.debug(f"Unwanted arg: '{arg}'")

    good_args = tuple(_ar for _ar in good_args if _ar)
    return good_args, kwargs


def _get_advanced_kwargs(bot, ctx, *args, bold_name=False, **kwargs):
    args = list(args)
    if not kwargs:
        kwargs = {"force": False, "dry": False, "sudo": False, 'update': False}

    good_args = list()
    mention_pattern = re.compile(r"<@[!&]\d+>")
    text_args = []

    for arg in args:
        if arg.startswith("-f") or arg == 'force':
            "force, enforce parameters"
            kwargs['force'] = True
        elif arg.startswith("-d") or arg == 'dry':
            "dry run"
            kwargs['dry'] = True
        elif arg.startswith("-u") or arg == 'update' or arg == "upgrade":
            "update"
            kwargs['update'] = True
        elif arg.startswith("-s") or arg.startswith("-a") or arg == 'sudo':
            "sudo or admin"
            kwargs['sudo'] = True
        elif arg.startswith("-"):
            try:
                _ = float(arg)
                good_args.append(arg)
            except ValueError:
                "drop unknown parameters"
                logger.warning(f"unknown argument: {arg}")
        elif "=" in arg:
            key, val = arg.split("=")
            if key == "force" or key == "dry":
                continue
            if key and val:
                kwargs.update({key: val})
        elif mention_pattern.match(arg) or "@everyone" in arg or "@here" in arg:
            name = string_mention_converter(bot, ctx.guild, arg, bold_name=bold_name)
            text_args.append(name)

        else:
            good_args.append(arg)
            text_args.append(arg)

    good_args = tuple(good_args)
    text = ' '.join(text_args)
    kwargs['text'] = text

    return good_args, kwargs


def find_one_member_name_and_picture(bot, get_random_if_none=True):
    """
    Decorator that find.
    Args:
        bot: bot instance
        bold_name:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(coro):
        logger.warning(f"Advanced args are not supporting non kwargs functions")

        async def f(ctx, *args, **kwargs):
            user = None
            if ctx.message.mentions:
                user = ctx.message.mentions[0]

            elif args:
                name = args[0]
                member = discord.utils.find(lambda m: name.lower() in m.name.lower(), ctx.guild.members)
                logger.debug(f"Found member: {member}")
                if member:
                    user = member
            if user is None:
                if get_random_if_none:
                    if ctx.guild:
                        user = random.choice(ctx.guild.members)
                    else:
                        user = ctx.author
                else:
                    user = ctx.author

            output = await coro(ctx, user, *args, **kwargs)
            return output

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return wrapper


def advanced_args_function(bot, bold_name=False):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        bot: bot instance
        bold_name:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(coro):
        logger.warning(f"Advanced args are not supporting non kwargs functions")

        async def f(ctx, *args, text=None, **kwargs):
            if text:
                logger.error(f"Text is already in advanced args: {text}")

            good_args, kwargs = _get_advanced_args(bot, ctx, *args, bold_name=bold_name, **kwargs)
            output = await coro(ctx, *good_args, **kwargs)
            return output

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return wrapper


def advanced_kwargs_only_function(bot, bold_name=False):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        bot: bot instance
        bold_name:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(coro):
        logger.warning(f"Advanced args are not supporting non kwargs functions")

        async def f(ctx, *args, text=None, **kwargs):
            if text:
                logger.error(f"Text is already in advanced args: {text}")

            good_args, kwargs = _get_advanced_kwargs(bot, ctx, *args, bold_name=bold_name, **kwargs)
            output = await coro(ctx, *good_args, **kwargs)
            return output

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return wrapper


def advanced_args_method(bold_name=False):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        bold_name:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(coro):
        logger.warning(f"Advanced args are not supporting non kwargs functions")

        async def f(cls, ctx, *args, text=None, **kwargs):
            if text:
                logger.error(f"Text is already in advanced args: {text}")

            good_args, kwargs = _get_advanced_args(cls, ctx, *args, bold_name=bold_name, **kwargs)

            output = await coro(cls, ctx, *good_args, **kwargs)
            return output

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return wrapper


def check_sudo_permission(ctx):
    if ctx.message.author.id == YOUSHISU_ID:
        return True
    else:
        return False


def check_force_permission(ctx):
    logger.critical(f"NotImplemented, force is not checking permission yet")
    return False


def _check_advanced_perm(ctx, *args, rule_sets=None, restrictions=None, sudo=False, force=False, **kwargs):
    if not rule_sets and not restrictions:
        raise CommandWithoutPermissions("Not checking any permission")

    if force:
        force = check_force_permission(ctx)

    if restrictions:
        if type(restrictions) is not list and type(restrictions) is not tuple:
            restrictions = [restrictions]

        for rule in restrictions:
            valid, error = rule(ctx, *args, **kwargs)
            if not valid:
                raise error

    if sudo and check_sudo_permission(ctx):
        return True, force

    else:
        rule_sets = [rules if type(rules) is list or type(rules) is set else [rules]
                     for rules in rule_sets]
        all_errors = []

        for rules in rule_sets:
            valids, errors = zip(*[chk_f(ctx, *args, **kwargs) for chk_f in rules])
            if all(valids):
                return True, force
            else:
                all_errors += errors

        if len(all_errors) > 0:
            raise all_errors[0]
            # return False, all_errors[0].args
        else:
            return True, force


def advanced_perm_check_function(*rules_sets, restrictions=None):
    """
    Check channels and permissions, use -s -sudo or -a -admin to run it.
    Args:
        *rules_sets:
        restrictions: Restrictions must be always met
    Returns:
        message object returned by calling given function with given params
    """

    def decorator(coro):
        async def f(*args, sudo=False, force=False, **kwargs):
            valid, force = _check_advanced_perm(*args,
                                                sudo=sudo, force=force, **kwargs,
                                                rule_sets=[*rules_sets], restrictions=restrictions)
            if valid:
                output = await coro(*args, force=force, **kwargs)
                return output
            else:
                logger.error(f"Permission check failed! Exceptions should be raised earlier!")
                raise CommandError("Permission check failed.")

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return decorator


def advanced_perm_check_method(*rules_sets, restrictions=None):
    """
    Check channels and permissions, use -s -sudo or -a -admin to run it.
    Args:
        *rules_sets:
        restrictions: Restrictions must be always met
    Returns:
        message object returned by calling given function with given params
    """

    def decorator(coro):
        async def f(cls, *args, sudo=False, force=False, **kwargs):
            valid, force = _check_advanced_perm(*args,
                                                sudo=sudo, force=force, **kwargs,
                                                rule_sets=[*rules_sets], restrictions=restrictions)
            if valid:
                output = await coro(cls, *args, force=force, **kwargs)
                return output
            else:
                # raise errors[0]
                raise CommandError("No permission")

        f.__name__ = coro.__name__
        f.__doc__ = coro.__doc__
        return f

    return decorator


def delete_call(coro):
    """
    Decorator that removes message which triggered command.
    Args:
        coro:

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        result = await coro(ctx, *args, **kwargs)

        try:
            await ctx.message.delete()
        except Exception as pe:
            logger.warning(f"Can not delete call: {pe}")

        return result

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__
    return decorator


def approve_fun(coro):
    """
    Decorator that adds reaction if success, else x.
    Args:
        coro:

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        try:
            result = await coro(ctx, *args, **kwargs)
            await ctx.message.add_reaction('✅')
            return result
        except NotFound:
            pass
        except Exception as pe:
            try:
                await ctx.message.add_reaction('❌')
            except NotFound:
                pass
            raise pe

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__
    return decorator


def trash_after(bot, timeout=600, delete_after_TO=False):
    """
    Decorator, that remove message after given time.
    Decorated function must return message!
    Args:
        bot: bot instance
        timeout: Integer, default 600
        delete_with_TO: Delete if timeout occured.

    Returns:
        message object returned by calling given function with given params
    """

    def function(coro):
        async def decorator(ctx, *args, **kwargs):

            message = await coro(ctx, *args, **kwargs)

            await message.add_reaction(EMOJIS['green_x'])
            await asyncio.sleep(0.1)

            def check_reaction(reaction, user):
                return user == ctx.message.author \
                       and str(reaction.emoji) == EMOJIS['green_x'] \
                       and reaction.message.id == message.id

            try:
                if timeout < 10:
                    tm = 10
                else:
                    tm = timeout
                reaction, user = await bot.wait_for('reaction_add',
                                                    check=check_reaction,
                                                    timeout=tm)
            except asyncio.TimeoutError:
                try:
                    await message.clear_reaction(EMOJIS['green_x'])
                except Exception:
                    pass
                if not delete_after_TO:
                    return None

            await message.delete()

        decorator.__name__ = coro.__name__
        decorator.__doc__ = coro.__doc__
        return decorator

    return function


def pages(bot, timeout=600):
    """
    Decorated function must return message!
    Args:
        bot: bot instance
        timeout: Integer, default 600
        delete_with_TO: Delete if timeout occured.

    Returns:
        message object returned by calling given function with given params
    """

    def function(coro):
        async def decorator(ctx, *args, **kwargs):
            page = 0
            message = await coro(ctx, *args, page=0, **kwargs)

            def wait_for_arrow(reaction, user):
                return user == ctx.message.author \
                       and str(reaction.emoji) in [EMOJIS['green_x'], EMOJIS['arrow_left'], EMOJIS['arrow_right']] \
                       and reaction.message.id == message.id

            await message.add_reaction(EMOJIS['green_x'])
            await message.add_reaction(EMOJIS['arrow_left'])
            await message.add_reaction(EMOJIS['arrow_right'])

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add",
                                                        check=wait_for_arrow,
                                                        timeout=timeout)
                    await reaction.remove(user)

                    if str(reaction.emoji) == EMOJIS['green_x']:
                        break
                    elif str(reaction.emoji) == EMOJIS['arrow_right']:
                        page += 1
                    else:
                        page -= 1
                    await coro(ctx, *args, old_message=message, page=page)

                except Exception as err:
                    print(err)
                    break
            await message.clear_reaction(EMOJIS["green_x"])
            await message.clear_reaction(EMOJIS["arrow_left"])
            await message.clear_reaction(EMOJIS["arrow_right"])

        decorator.__name__ = coro.__name__
        decorator.__doc__ = coro.__doc__
        return decorator

    return function


def menus(bot, menu_count=10, timeout=600):
    """
    Decorated function must return message!
    Args:
        bot: bot instance
        timeout: Integer, default 600
        delete_with_TO: Delete if timeout occured.

    Returns:
        message object returned by calling given function with given params
    """

    def function(coro):
        async def decorator(ctx, *args, **kwargs):
            page = 0
            menu = 0
            message = await coro(ctx, *args, **kwargs)
            emojis = [EMOJIS['green_x'], EMOJIS['arrow_left'], EMOJIS['arrow_right'], EMOJIS['arrow_back_left']] \
                     + [EMOJIS[num] for num in range(1, menu_count + 1)]
            emoji_pages_dict = {EMOJIS[num]: num for num in range(1, menu_count + 1)}

            def wait_for_arrow(reaction, user):
                return user == ctx.message.author \
                       and str(reaction.emoji) in emojis \
                       and reaction.message.id == message.id

            # for em in emojis:
            await message.add_reaction(EMOJIS['green_x'])
            await message.add_reaction(EMOJIS['arrow_back_left'])

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add",
                                                        check=wait_for_arrow,
                                                        timeout=timeout)
                    await reaction.remove(user)

                    if str(reaction.emoji) == EMOJIS['green_x']:
                        break
                    elif str(reaction.emoji) == EMOJIS['arrow_right']:
                        page += 1
                    elif str(reaction.emoji) in emoji_pages_dict:
                        page = 0
                        menu = emoji_pages_dict[str(reaction.emoji)]
                    elif str(reaction.emoji) == EMOJIS['arrow_back_left']:
                        menu = 0
                        page = 0
                    else:
                        page -= 1

                    await coro(ctx, old_message=message, menu=menu, page=page)

                except Exception as err:
                    print(err)
                    break
            for em in emojis:
                await message.clear_reaction(em)

        decorator.__name__ = coro.__name__
        decorator.__doc__ = coro.__doc__
        return decorator

    return function


def _log_call(ctx, *args, **kwargs):
    if ctx.guild:
        where = f"#{ctx.channel}, {ctx.guild.name} ({ctx.guild.id})"
    else:
        where = f"{ctx.channel}"
    logger.info(f"Invo: '{ctx.message.content}', Args:{args}, Kwargs:{kwargs}. {ctx.message.author}, {where}")


def log_call_function(coro):
    """
    Decorator, logs function.
    Args:
    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        _log_call(ctx, *args, **kwargs)
        message = await coro(ctx, *args, **kwargs)
        return message

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__
    return decorator


def log_call_method(coro):
    """
    Decorator, logs cog method.
    Args:
    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(cls, ctx, *args, **kwargs):
        _log_call(ctx, *args, **kwargs)
        message = await coro(cls, ctx, *args, **kwargs)
        return message

    decorator.__name__ = coro.__name__
    decorator.__doc__ = coro.__doc__
    return decorator
