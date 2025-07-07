from pathlib import Path

import yaml


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
        print(f'Error: settings file {fname} not found.')
    except yaml.YAMLError as err:
        print(f'Error parsing settings from {fname}: {err}')
    return None
