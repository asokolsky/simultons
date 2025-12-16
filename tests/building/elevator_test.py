"""
Testing the elevator-related stuff
"""

import unittest

from simultons import setup_logging
from simultons.building import Elevator

log = setup_logging(__name__)


class TestElevator(unittest.TestCase):
    """
    Verify Elevator functionality
    """

    def setUp(self) -> None:
        self.el: Elevator | None = Elevator(None, 'test', 5)
        return

    def tearDown(self) -> None:
        self.el = None
        return

    def test_all(self) -> None:
        """
        Test Elevator functionality
        """
        log.info(self.el)
        return
