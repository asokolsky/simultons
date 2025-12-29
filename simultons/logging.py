import logging
import logging.config
import sys
from pathlib import Path
from types import TracebackType
from typing import Any

import yaml

#
# contents of logging.yaml
#
logging_config: dict | None = None


def load_yaml(fpath: str) -> dict | None:
    """
    Load a YAML file and return as dict
    """
    # print('load_yaml', fpath)
    path = Path(fpath)
    with path.open('r') as file:
        try:
            config = yaml.safe_load(file.read())
            assert isinstance(config, dict)
            # print('load_yaml', config)
            return config
        except FileNotFoundError:
            print(f'Error: file {path} not found.')
        except yaml.YAMLError as err:
            print(f'Error: parsing {path}: {err}')
    return None


def setup_logging(
    logger_name: str | None,
    level: int = logging.NOTSET,
    logging_config_path: str | None = None,
) -> Any:
    """
    Setup the logger `logger_name`
    """
    # print('setup_logging', level, logging_config_path)
    global logging_config
    if logging_config_path is None:
        logging_config_path = 'logging.yaml'
    # parent_dir = Path(__file__).absolute().parents[1]
    # logging_config_path = parent_dir / 'logging.yaml'
    logging_config = load_yaml(logging_config_path)
    # repetitive calls can be useful
    if logging_config is None:
        # set the defaults
        logging.basicConfig(level=level)
    else:
        # set the logging according to the `logging.yaml`
        logging.config.dictConfig(logging_config)
    logger = logging.getLogger(logger_name)
    if level != logging.NOTSET:
        logger.setLevel(level)
    # logger.propagate = False
    assert logger is not None
    # print('setup_logging() =>', logger)
    # print_logging_tree()
    return logger


def print_logging_tree() -> None:
    """
    See https://pypi.org/project/logging-tree/
    """
    from logging_tree import printout  # noqa: PLC0415

    printout()
    return


log = setup_logging(__name__)


def handle_uncaught_exception(
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    exc_traceback: TracebackType | None,
) -> None:
    """
    Log an uncaught exception which terminates the app.
    """
    log.critical(
        'uncaught exception, application will terminate.',
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    return


sys.excepthook = handle_uncaught_exception
