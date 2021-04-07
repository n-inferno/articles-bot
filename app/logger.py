import logging


def get_logger():
    lg = logging.getLogger('bot')
    lg.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s"))
    lg.addHandler(console_handler)
    return lg


logger = get_logger()
