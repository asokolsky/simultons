from pathlib import Path

import yaml

from . import setup_logging

log = setup_logging(__name__)


def load_settings(fname: str = 'settings.yaml') -> dict | None:
    """
    Load application settings from YAML-formatted fname.
    Returns JSON or None in case of failure
    """
    try:
        path = Path(fname)
        with path.open('r') as file:
            settings = yaml.safe_load(file)
            assert isinstance(settings, dict)
            return settings

    except FileNotFoundError:
        log.error(f'Error: settings file {fname} not found.')
    except yaml.YAMLError as err:
        log.error(f'Error parsing settings from {fname}: {err}')
    return None
