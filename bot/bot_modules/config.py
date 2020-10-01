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

    def add_role_menu(self, guild_id, name, *args, **kwargs):
        self.all_configs[guild_id].add_role_menu(name, *args, **kwargs)

    def remove_role_menu(self, guild_id, name):
        self.all_configs[guild_id].remove_role_menu(name)

    def get_role_menu_id(self, guild_id, message_id):
        return self.all_configs[guild_id].get_role_menu_id(message_id)

    def items(self):
        return self.all_configs.items()

    def is_role_menu_defined(self, guild_id, name):
        return self.all_configs[guild_id].get_role_menu_name(name)


class ServerConfig:
    def __init__(self, server_id, name):
        self.server_id = server_id
        self.name = name
        self.config = {}
        self.role_menus = RoleMenus()  # "Name": ids

    async def check(self, bot):
        """ Check if channels defined are visible for bot"""
        logger.debug(f"Checking config for: {self.name}")
        if self.role_menus:
            to_delete = set()
            for name, settings in self.role_menus.items():
                for msg_id in settings['message_ids']:
                    channel = bot.get_channel(self.role_menus.refs_to_channel.get(msg_id))
                    try:
                        await channel.fetch_message(msg_id)
                    except NotFound:
                        logger.debug(f"Don't see message, removing rolemenu: {name}")
                        to_delete.add(name)
                        break

            for bad_role_menu in to_delete:
                logger.info(f"Removing missing role menu: {self.name}: {bad_role_menu}")
                self.remove_role_menu(bad_role_menu)

    def add_role_menu(self, name, emojis_role_dictionary, message_ids, channel_id):
        logger.debug(f"SC: Add role menu: {self.name}: {name}")
        message_ids = set(message_ids)
        self.role_menus.add_role_menu(name, emojis_role_dictionary, message_ids, channel_id)

    def remove_role_menu(self, name):
        logger.debug(f"SC: Remove role menu: {self.name}: {name}")
        self.role_menus.remove_role_menu(name)

    def get_role_menu_id(self, message_id):
        logger.debug(f"SC: Get role menu: {self.name}: {message_id}")
        return self.role_menus.get_role_menu_id(message_id)

    def get_role_menu_name(self, name):
        logger.debug(f"SC: Get role menu: {self.name}: {name}")
        return self.role_menus.get_role_menu_name(name)

    def __str__(self):
        return f"Config {self.name}: {self.role_menus}"

    def show(self):
        return f"Config {self.name}: {self.role_menus}"


class RoleMenus:
    def __init__(self):
        self.menus = {}
        self.message_ids = set()
        self.refs_to_channel = {}

    def add_role_menu(self, name, emojis_role_dictionary, message_ids, channel_id):
        logger.debug(f"Adding role menu: {name}")
        if name in self.menus:
            raise CommandError(f"This menu is defined on server {name}")
        else:
            self.menus.update({name: {
                    'name': name,
                    'emojis_roles': emojis_role_dictionary,
                    'channel_id': channel_id,
                    'message_ids': message_ids}})
            for msg_id in message_ids:
                self.message_ids.add(msg_id)
                self.refs_to_channel.update({msg_id: channel_id})

    def remove_role_menu(self, name):
        logger.debug(f"RM: Removing role_menu: {name}")
        if name not in self.menus:
            raise CommandError(f"This menu is not defined {name}")

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
        return self.menus.get(name, None)

    def items(self):
        return self.menus.items()

    def __str__(self):
        return str(self.menus.items())


my_config = Config()
