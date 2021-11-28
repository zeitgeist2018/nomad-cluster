import os

import logging


log_level = os.environ.get('LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=log_level,
    datefmt='%Y-%m-%d %H:%M:%S')


class LoggingService:
    def debug(self, message):
        logging.debug(message)

    def info(self, message):
        logging.info(message)

    def warn(self, message):
        logging.warning(message)

    def err(self, message):
        logging.error(message)
