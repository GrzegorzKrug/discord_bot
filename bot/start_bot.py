import sys
import os

from bot_modules.bot import bot

try:
    with open("token.txt", "rt") as file:
        token = file.read()
except Exception as e:
    print(f"{e}")
    sys.exit(1)

bot.run(token)
# asyncio.run(custom_run(token))
# 470285521 # permission int
