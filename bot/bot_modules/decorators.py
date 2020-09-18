import asyncio
import time
import re

from .permissions import CommandWithoutPermissions
from .definitions import send_disapprove, logger

from discord.ext.commands import CommandError
from discord import HTTPException


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
    mention_pattern = re.compile(r"<@[!&]\d+>")
    text_args = []

    for arg in args:
        if arg.startswith("-f"):
            "force, enforce parameters"
            kwargs['force'] = True
        elif arg.startswith("-d"):
            "dry run"
            kwargs['dry'] = True
        elif arg.startswith("-s") or arg.startswith("-a"):
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


def advanced_args_function(bot, bold_name=False):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(fun):
        logger.warning(f"Advanced args are not supporting non kwargs functions")

        async def f(ctx, *args, text=None, **kwargs):
            if text:
                logger.error(f"Text is already in advanced args: {text}")

            good_args, kwargs = _get_advanced_args(bot, ctx, *args, bold_name=bold_name, **kwargs)
            output = await fun(ctx, *good_args, **kwargs)
            return output

        f.__name__ = fun.__name__
        f.__doc__ = fun.__doc__
        return f

    return wrapper


def advanced_args_method(bold_name=False):
    """
    Decorator that translates args to create flags and converts string into kwargs.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    def wrapper(fun):
        logger.warning(f"Advanced args are not supporting non kwargs functions")
        if "." not in fun.__qualname__:
            raise TypeError("This decorator is for methods")

        async def f(cls, ctx, *args, text=None, **kwargs):
            if text:
                logger.error(f"Text is already in advanced args: {text}")

            good_args, kwargs = _get_advanced_args(cls, ctx, *args, bold_name=bold_name, **kwargs)

            output = await fun(cls, ctx, *good_args, **kwargs)
            return output

        f.__name__ = fun.__name__
        f.__doc__ = fun.__doc__
        return f

    return wrapper


def check_sudo_permission(ctx):
    logger.critical(f"NotImplemented, sudo is not checking permission yet")
    return False


def check_force_permission(ctx):
    logger.critical(f"NotImplemented, force is not checking permission yet")
    return False


def _check_advanced_perm(ctx, *args, checking_funcs=None, sudo=False, force=False, **kwargs):
    if len(checking_funcs) <= 0:
        raise CommandWithoutPermissions("Not checking any permission")

    if sudo and check_sudo_permission(ctx) or all(
            chk_f(ctx, *args, **kwargs) for chk_f in checking_funcs):
        if force:
            force = check_force_permission(ctx)

        return True, force
    else:
        raise CommandError("No permission")


def advanced_perm_check_function(bot, *checking_funcs, bold_name=False):
    """
    Check channels and permissions, use -s -sudo or -a -admin to run it.
    Args:
        *checking_funcs:
        bold_name: if output text should use bold font
    Returns:
        message object returned by calling given function with given params
    """

    def decorator(fun):
        @advanced_args_function(bot, bold_name)
        async def f(*args, sudo=False, force=False, **kwargs):
            valid, force = _check_advanced_perm(*args,
                                                sudo=sudo, force=force, **kwargs,
                                                checking_funcs=[*checking_funcs])
            if valid:
                output = await fun(*args, force=force, **kwargs)
                return output
            else:
                raise CommandError("No permission")

        f.__name__ = fun.__name__
        f.__doc__ = fun.__doc__
        return f

    return decorator


def advanced_perm_check_method(*checking_funcs, bold_name=False):
    """
    Check channels and permissions, use -s -sudo or -a -admin to run it.
    Args:
        *checking_funcs:
        bold_name: if output text should use bold font
    Returns:
        message object returned by calling given function with given params
    """

    def decorator(fun):
        @advanced_args_method(bold_name)
        async def f(cls, *args, sudo=False, force=False, **kwargs):
            valid, force = _check_advanced_perm(*args,
                                                sudo=sudo, force=force, **kwargs,
                                                checking_funcs=[*checking_funcs])
            if valid:
                output = await fun(cls, *args, force=force, **kwargs)
                return output
            else:
                raise CommandError("No permission")

        f.__name__ = fun.__name__
        f.__doc__ = fun.__doc__
        return f

    return decorator


def delete_call(fun):
    """
    Decorator that removes message which triggered command.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        result = await fun(ctx, *args, **kwargs)

        try:
            await ctx.message.delete()
        except Exception as pe:
            logger.warning(f"Can not delete call: {pe}")

        return result

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator


def approve_fun(fun):
    """
    Decorator that adds reaction if success, else x.
    Args:
        fun:

    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        try:
            result = await fun(ctx, *args, **kwargs)
            await ctx.message.add_reaction('✅')
            return result
        except Exception as pe:
            await ctx.message.add_reaction('❌')

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator


def trash_after(bot, timeout=600):
    """
    Decorator, that remove message after given time.
    Decorated function must return message!
    Args:
        timeout: Integer, default 600

    Returns:
        message object returned by calling given function with given params
    """

    def function(fun):
        async def decorator(ctx, *args, **kwargs):

            message = await fun(ctx, *args, **kwargs)

            await message.add_reaction("❎")
            await asyncio.sleep(0.1)

            def check_reaction(reaction, user):
                return user == ctx.message.author \
                       and str(reaction.emoji) == '❎' \
                       and reaction.message.id == message.id

            try:
                if timeout < 1:
                    tm = 30
                else:
                    tm = timeout
                reaction, user = await bot.wait_for('reaction_add',
                                                    check=check_reaction,
                                                    timeout=tm)
            except asyncio.TimeoutError:
                pass

            await message.delete()

        decorator.__name__ = fun.__name__
        decorator.__doc__ = fun.__doc__
        return decorator

    return function


def _log_call(ctx, *args, **kwargs):
    if ctx.guild:
        where = f"#{ctx.channel}, {ctx.guild.name} ({ctx.guild.id})"
    else:
        where = f"{ctx.channel}"
    logger.info(f"Invo: '{ctx.message.content}', Args:{args}, Kwargs:{kwargs}. {ctx.message.author}, {where}")


def log_call_function(fun):
    """
    Decorator, logs function.
    Args:
    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(ctx, *args, **kwargs):
        _log_call(ctx, *args, **kwargs)
        message = await fun(ctx, *args, **kwargs)
        return message

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator


def log_call_method(fun):
    """
    Decorator, logs cog method.
    Args:
    Returns:
        message object returned by calling given function with given params
    """

    async def decorator(cls, ctx, *args, **kwargs):
        _log_call(ctx, *args, **kwargs)
        message = await fun(cls, ctx, *args, **kwargs)
        return message

    decorator.__name__ = fun.__name__
    decorator.__doc__ = fun.__doc__
    return decorator
