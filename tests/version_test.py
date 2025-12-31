import tomllib
import unittest
from pathlib import Path

from simultons import __version__, setup_logging

log = setup_logging(__name__)


class TestModuleVersion(unittest.TestCase):
    """
    Verify simultons versions in project.toml and __init__.py are the same
    """

    def test_version(self) -> None:
        log.info('test_version')
        repo_root = Path(__file__).absolute().parents[1]
        pyproject_path = repo_root / 'pyproject.toml'
        self.assertTrue(pyproject_path.is_file())
        with pyproject_path.open('rb') as f:
            data = tomllib.load(f)
            self.assertIsInstance(data, dict)
            version = data['project']['version']
            self.assertEqual(version, __version__)
        return
