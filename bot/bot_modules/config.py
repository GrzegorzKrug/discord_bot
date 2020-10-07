from .definitions import logger
from discord.ext.commands import CommandError
from discord.errors import NotFound

import shelve
import os


class Config:
    def __init__(self):
        self.all_configs = {}
        self.config_dir = os.path.abspath(os.path.join(__file__, '..', '..', 'config'))
        self.clear_config_not_save = False
        os.makedirs(self.config_dir, exist_ok=True)

        # Config is checked, when bot is ready and logged in, now we just load.
        self.load()
        self.new_config_shape()

    def save(self):
        config_file = os.path.join(self.config_dir, "shelf.db")
        if self.clear_config_not_save:
            with shelve.open(config_file, flag="n") as sh:
                pass
        else:
            with shelve.open(config_file, flag="c") as sh:
                sh['all_configs'] = self.all_configs
                logger.debug("Config save success")

    def load(self):
        config_file = os.path.join(self.config_dir, "shelf.db")
        try:
            sh = shelve.open(config_file, flag="r")
        except Exception as err:
            logger.error(f"Open DB failed: {err}")

            return None

        try:
            all_configs = sh['all_configs']
            self.all_configs = all_configs
            logger.debug("Config load success")
        except Exception as err:
            logger.error(f"Error when loading config {err}")
            pass

        finally:
            sh.close()

    async def check_loaded_config(self, bot):
        if not self.all_configs:
            logger.debug(f"Creating new configs")

            self.all_configs = {guild.id: ServerConfig(guild.id, guild.name) for guild in bot.guilds}

        else:
            for config in self.all_configs.values():
                await config.check(bot)

            guilds = {guild.id for guild in bot.guilds}
            have_cfg = set(self.all_configs.keys())
            missing_configs = have_cfg.difference(guilds)

            for guild_id in missing_configs:
                guild = bot.get_guild(guild_id)
                self.all_configs[guild_id] = ServerConfig(guild_id, guild.name)

    def new_config_shape(self):
        logger.debug(f"New config shape starting.")
        for id, config in self.all_configs.items():
            logger.debug(f"New config for server: {id}")
            self.all_configs[id] = ServerConfig(None, None) + config

        logger.debug(f"New config: {self.all_configs}")

    def add_server(self, guild_id, guild_name):
        cfg = ServerConfig(guild_id, guild_name)
        self.all_configs[guild_id] = cfg

    def add_role_menu(self, guild_id, name, *args, **kwargs):
        self.all_configs[guild_id].add_role_menu(name, *args, **kwargs)

    def remove_role_menu(self, guild_id, name):
        self.all_configs[guild_id].remove_role_menu(name)

    def get_role_menu_id(self, guild_id, message_id):
        return self.all_configs[guild_id].get_role_menu_id(message_id)

    def show_server_role_menus(self, guild_id):
        logger.debug(f"Asking for server roles: {guild_id}")
        return self.all_configs[guild_id].show_role_menus()

    def items(self):
        return self.all_configs.items()

    def get_role_menu_name(self, guild_id, name):
        return self.all_configs[guild_id].get_role_menu_name(name)


class ServerConfig:
    def __init__(self, server_id, name):
        self.server_id = server_id
        self.name = name
        self.config = dict()
        self.role_menus = RoleMenus()

    def __add__(self, other):
        if other:
            self.config = {**self.config, **other.config}
            self.role_menus = self.role_menus + other.role_menus
            self.name = other.name
            self.server_id = other.server_id
        return self

    async def check(self, bot):
        """ Check if channels defined are visible for bot"""
        logger.debug(f"Checking config for: {self.name}")
        if self.role_menus:
            to_delete = set()
            # logger.debug(f"Checking role menu: {self.role_menus}")
            for name, settings in self.role_menus.items():
                logger.debug(f"configs: {settings}")
                for msg_id in settings['message_ids']:
                    channel = bot.get_channel(self.role_menus.refs_to_channel.get(msg_id))
                    try:
                        await channel.fetch_message(msg_id)
                        logger.debug(f"found message, not removing menu")
                    except NotFound:
                        logger.debug(f"Don't see message, removing role menu: {name}")
                        to_delete.add(name)
                        break

            for bad_role_menu in to_delete:
                logger.info(f"Removing missing role menu: {self.name}: {bad_role_menu}")
                self.remove_role_menu(bad_role_menu)

    def add_role_menu(self, name, emojis_role_dictionary, message_ids, channel_id, role_type):
        logger.debug(f"SC: Add role menu: {self.name}: {name}")
        message_ids = set(message_ids)
        self.role_menus.add_role_menu(name, emojis_role_dictionary, message_ids, channel_id, role_type)

    def remove_role_menu(self, name):
        logger.debug(f"SC: Remove role menu: {self.name}: {name}")
        self.role_menus.remove_role_menu(name)

    def get_role_menu_id(self, message_id):
        logger.debug(f"SC: Get role menu: {self.name}: {message_id}")
        return self.role_menus.get_role_menu_id(message_id)

    def get_role_menu_name(self, name):
        logger.debug(f"SC: Get role menu: {self.name}: {name}")
        return self.role_menus.get_role_menu_name(name)

    def show_role_menus(self):
        names = self.role_menus.keys()
        return names

    def __str__(self):
        return f"Config for {self.name}:\n{self.role_menus}"

    def show(self):
        return f"Config {self.name}: {self.role_menus}"


class RoleMenus:
    def __init__(self):
        self.menus = {}
        self.message_ids = set()
        self.refs_to_channel = {}

    def __add__(self, old):
        logger.debug("ADD RLM")
        if old:
            new_menu = {}
            for name, value in old.menus.items():
                logger.debug(f"Menu name: {name}")
                blank_menu = self.new_role_menu(name)

                for key, _val in value.items():
                    if key in blank_menu[name]:
                        blank_menu[name][key] = _val
                        logger.debug(f"Key yes, in dict: {key}")
                    else:
                        logger.debug(f"Key not in dict: {key}")

                logger.debug(f"blank: {blank_menu}")
                new_menu.update({**blank_menu})

            logger.debug(f"New menu: {new_menu.items()}")

            self.menus = new_menu
            self.message_ids = self.message_ids | old.message_ids
            self.refs_to_channel = {**self.refs_to_channel, **old.refs_to_channel}

        return self

    def __str__(self):
        return f"Menus: {self.menus.items()},\n" \
               f"Msg ids: {self.message_ids},\n" \
               f"Refs to channel: {self.refs_to_channel},\n" \
               f"Dir: {dir(self)}"

    def add_role_menu(self, name, emojis_role_dictionary, message_ids, channel_id, role_type):
        logger.debug(f"Adding role menu: {name}")
        if name in self.menus:
            raise CommandError(f"This menu is defined on server {name}")
        else:
            menu = self.new_role_menu(name, emojis_role_dictionary, message_ids, channel_id, role_type)
            self.menus.update({**menu})

            for msg_id in message_ids:
                self.message_ids.add(msg_id)
                self.refs_to_channel.update({msg_id: channel_id})

    @staticmethod
    def new_role_menu(name=None, emojis_role_dictionary=None, message_ids=None, channel_id=None, role_type="single"):
        menu = dict()
        emojis_role_dictionary = dict() if not emojis_role_dictionary else emojis_role_dictionary
        message_ids = set() if not message_ids else message_ids
        channel_id = set() if not channel_id else channel_id

        menu.update({name: {
                'name': name,
                'emojis_roles': emojis_role_dictionary,
                'channel_id': channel_id,
                'message_ids': message_ids,
                'role_type': role_type
        }})
        return menu

    def remove_role_menu(self, name):
        logger.debug(f"RM: Removing role_menu: {name}")
        if name not in self.menus:
            raise CommandError(f"This menu is not defined `{name}`")

        rolemenu = self.menus.get(name)
        for msg_id in rolemenu['message_ids']:
            try:
                self.message_ids.remove(msg_id)
            except Exception:
                pass
            try:
                self.refs_to_channel.pop(msg_id)
            except Exception:
                pass
        self.menus.pop(name)

    def get_role_menu_id(self, message_id):
        for menu in self.menus.values():
            logger.debug(f"Checking role menu: {menu['message_ids']}")
            valid = message_id in menu['message_ids']
            logger.debug(f"valid: {valid}")
            if message_id in menu['message_ids']:
                return menu

    def get_role_menu_name(self, name):
        logger.debug(f"RM: get role menu")
        return self.menus.get(name, None)

    def items(self):
        return self.menus.items()

    def keys(self):
        return self.menus.keys()


my_config = Config()
