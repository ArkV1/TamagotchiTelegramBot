# utils/logging.py
import logging

def setup_logging(level=logging.INFO):
    # Create a custom logger
    logger = logging.getLogger('telegram_bot')
    logger.setLevel(level)

    # Create handlers (e.g., console and file handlers)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('bot.log')
    # TODO: PRODUCTION
    # c_handler.setLevel(logging.WARNING)
    # DEVELOPMENT
    f_handler.setLevel(logging.ERROR)

    # Create formatters and add them to the handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

# Usage example
# logger = setup_logging()
# logger.info("This is an info message")
