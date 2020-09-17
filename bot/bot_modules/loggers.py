import datetime
import logging
import random
import os


def define_logger(name="logs", log_level="DEBUG", date_in_file=True,
                  combined=True, add_timestamp=True):
    if combined:
        file_name = "all"
    else:
        file_name = name

    if date_in_file:
        dt = datetime.datetime.now().strftime("%Y-%m-%d")
        file_name = f"{dt}-" + file_name
    file_name += ".log"

    if add_timestamp:
        unique_name = str(random.random())  # Random unique
    else:
        unique_name = name

    logger = logging.getLogger(unique_name)

    # Switch log level from env variable
    if log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif log_level == "INFO":
        logger.setLevel(logging.INFO)
    elif log_level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif log_level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif log_level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.WARNING)

    # Log Handlers: Console and file
    try:
        fh = logging.FileHandler(os.path.join(r'/logs', file_name),
                                 mode='a')
    except FileNotFoundError:
        os.makedirs(r'logs', exist_ok=True)
        fh = logging.FileHandler(os.path.join(r'logs', file_name),
                                 mode='a')

    ch = logging.StreamHandler()

    # LEVEL
    fh.setLevel("INFO")

    # Log Formatting
    formatter = logging.Formatter(
            f'%(asctime)s -{name}- %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False  # this prevents other loggers I thinks from logging

    return logger


logger = define_logger("Bot")
