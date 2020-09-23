from .definitions import YOUSHISU_ID


class RestrictedError(PermissionError):
    pass


class CommandWithoutPermissions(PermissionError):
    pass


def is_not_priv(ctx, *args, **kwargs):
    if ctx.guild:
        return True, None
    else:
        return False, RestrictedError("This command is restricted to server channels.")


def has_arguments(ctx, *args, **kwargs):
    if len(args) > 0:
        return True, None
    else:
        return False, RestrictedError("This requires arguments.")


# def has_role_perm(ctx, *args, **kwargs):
#     if False:
#         ctx.author.rol
#         return True, None
#
#     else:
#         return False, RestrictedError("This command is restricted to user with role-manage permission.")


def is_priv(ctx, *args, **kwargs):
    if ctx.guild:
        return False, RestrictedError("This command is restricted to private channels.")
    else:
        return True, None


def is_bot_owner(ctx, *args, **kwargs):
    if ctx.message.author.id == YOUSHISU_ID:
        return True, None
    else:
        return False, RestrictedError("This command is restricted to Youshisu.")


def is_server_owner(ctx, *args, **kwargs):
    if not ctx.guild:
        return False, RestrictedError("This command is restricted to server.")

    elif not ctx.guild.owner.id == ctx.author.id:
        return False, RestrictedError("This command is restricted to server owner.")
    else:
        return True, None


def this_is_disabled(*args, **kwargs):
    raise RestrictedError("Command is disabled.")
