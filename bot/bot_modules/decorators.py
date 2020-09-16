import asyncio
import re

from .loggers import logger
from discord.ext.commands import CommandError


class Decorators:
    def __init__(self, bot):
        self.bot = bot

    def string_mention_converter(self, guild, text: "input str", bold_name=True) -> "String":
        user_pattern = re.compile(r"<@!(\d+)>")
        role_pattern = re.compile(r"<@&(\d+)>")
        new_text = text

        new_text = new_text.replace("@everyone", "<everyone>")
        new_text = new_text.replace("@here", "<here>")

        user_list = user_pattern.findall(text)
        role_list = role_pattern.findall(text)

        for user in user_list:
            try:
                user_name = self.bot.get_user(int(user)).name
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

    def _get_advanced_args(self, ctx, *args, bold_name=False, **kwargs):
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
                name = Decorators.string_mention_converter(self.bot, ctx.guild, arg, bold_name=bold_name)
                text_args.append(name)

            else:
                good_args.append(arg)
                text_args.append(arg)
        good_args = tuple(good_args)
        text = ' '.join(text_args)
        kwargs['text'] = text

        return good_args, kwargs

    def advanced_args_function(self, bold_name=False):
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

                good_args, kwargs = self._get_advanced_args(ctx, *args, bold_name=bold_name, **kwargs)

                output = await fun(ctx, *good_args, **kwargs)
                return output

            f.__name__ = fun.__name__
            f.__doc__ = fun.__doc__
            return f

        return wrapper

    def advanced_args_method(self, bold_name=False):
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

                good_args, kwargs = self._get_advanced_args(ctx, *args, bold_name=bold_name, **kwargs)

                output = await fun(cls, ctx, *good_args, **kwargs)
                return output

            f.__name__ = fun.__name__
            f.__doc__ = fun.__doc__
            return f

        return wrapper

    @staticmethod
    def check_sudo_permission(ctx):
        logger.critical(f"NotImplemented, sudo is not checking permission yet")
        return False

    @staticmethod
    def check_force_permission(ctx):
        logger.critical(f"NotImplemented, force is not checking permission yet")
        return False

    @staticmethod
    def _check_advanced_perm(ctx, *args, checking_funcs=None, sudo=False, force=False, **kwargs):
        if sudo and Decorators.check_sudo_permission(ctx) or all(
                chk_f(ctx, *args, **kwargs) for chk_f in checking_funcs):
            if force:
                force = Decorators.check_force_permission(ctx)

            return True, force
        else:
            raise CommandError("No permission")

    def advanced_perm_check_function(self, *checking_funcs, bold_name=False):
        """
        Check channels and permissions, use -s -sudo or -a -admin to run it.
        Args:
            *checking_funcs:
            bold_name: if output text should use bold font
        Returns:
            message object returned by calling given function with given params
        """

        def decorator(fun):
            @self.advanced_args_function(bold_name)
            async def f(*args, sudo=False, force=False, **kwargs):
                valid, force = self._check_advanced_perm(*args,
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

    def advanced_perm_check_method(self, *checking_funcs, bold_name=False):
        """
        Check channels and permissions, use -s -sudo or -a -admin to run it.
        Args:
            *checking_funcs:
            bold_name: if output text should use bold font
        Returns:
            message object returned by calling given function with given params
        """

        def decorator(fun):
            @self.advanced_args_method(bold_name)
            async def f(cls, *args, sudo=False, force=False, **kwargs):
                valid, force = self._check_advanced_perm(*args,
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

    @staticmethod
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

    @staticmethod
    def trash_after(timeout=600):
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

    @staticmethod
    def log_call(fun):
        """
        Decorator, logs function.
        Args:
            timeout: Integer, default 600

        Returns:
            message object returned by calling given function with given params
        """

        async def decorator(ctx, *args, **kwargs):
            if ctx.guild:
                where = f"#{ctx.channel}, {ctx.guild.name} ({ctx.guild.id})"
            else:
                where = f"{ctx.channel}"
            logger.info(f"Invo: '{ctx.message.content}', Args:{args}, Kwargs:{kwargs}. {ctx.message.author}, {where}")
            message = await fun(ctx, *args, **kwargs)
            return message

        decorator.__name__ = fun.__name__
        decorator.__doc__ = fun.__doc__
        return decorator
