import json
import logging
import logging.config
import sys
import time
from typing import Optional, Union

logger = logging.getLogger('aiohttp.serve')


def configure_logging(log_config: Optional[Union[dict, str]] = None):
    if log_config is None:
        if not logger.hasHandlers():
            # default configuration
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s [%(process)d] [%(name)s] %(levelname)s : %(message)s'
            )
            formatter.converter = time.gmtime

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    else:
        if isinstance(log_config, dict):
            logging.config.dictConfig(log_config)
        elif log_config.endswith('.json'):
            with open(log_config) as file:
                loaded_config = json.load(file)
                logging.config.dictConfig(loaded_config)
        elif log_config.endswith(('.yaml', '.yml')):
            import yaml

            with open(log_config) as file:
                loaded_config = yaml.safe_load(file)
                logging.config.dictConfig(loaded_config)
        else:
            # See the note about fileConfig() here:
            # https://docs.python.org/3/library/logging.config.html#configuration-file-format
            logging.config.fileConfig(log_config, disable_existing_loggers=False)
