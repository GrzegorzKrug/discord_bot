from .definitions import YOUSHISU_ID


class RestrictedError(PermissionError):
    pass


class CommandWithoutPermissions(PermissionError):
    pass


def is_not_priv(ctx, *args, **kwargs):
    if ctx.guild:
        return True
    else:
        raise RestrictedError("This command is restricted to server channels.")


def is_priv(ctx, *args, **kwargs):
    if ctx.guild:
        raise RestrictedError("This command is restricted to private channels.")
    else:
        return True


def is_bot_owner(ctx, *args, **kwargs):
    if ctx.message.author.id == YOUSHISU_ID:
        return True
    else:
        raise RestrictedError("This command is restricted to Youshisu.")


def is_server_owner(ctx, *args, **kwargs):
    if not ctx.guild:
        raise RestrictedError("This command is restricted to server.")

    elif not ctx.guild.owner.id == ctx.author.id:
        raise RestrictedError("This command is restricted to server owner.")
    else:
        return True


def this_is_disabled(*args, **kwargs):
    raise RestrictedError("Command is disabled.")
