import sys
import os

from bot_modules.bot import bot
from bot_modules.definitions import logger

try:
    token_file = os.getenv("TOKEN_FILE", None)
    if token_file:
        with open(token_file, "rt") as file:
            token = file.read()

    else:
        with open("token.txt", "rt") as file:
            token = file.read()

except Exception as e:
    logger.critical(f"{e}")
    sys.exit(1)

bot.run(token)
