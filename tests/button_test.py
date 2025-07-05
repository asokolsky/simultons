"""
Testing all the button-related stuff
"""

import unittest
from typing import ClassVar

from simultons import Button, ButtonWithLed, ButtonWithLedPanel


class TestButton(unittest.TestCase):
    """
    Verify Button functionality
    """

    button_label: ClassVar = 'foo'
    clicks: ClassVar = 0

    def setUp(self) -> None:
        self.button: Button | None = Button(self.button_label, self.callback)
        return

    def tearDown(self) -> None:
        self.button = None
        return

    def callback(self, button: Button) -> None:
        """
        Button callback
        """
        TestButton.clicks += 1
        self.assertEqual(button, self.button)
        return

    def test_all(self) -> None:
        """
        Test Button functionality
        """
        #
        # verify clicks go through
        #
        clicks_old = self.clicks
        assert self.button is not None
        self.button.click()
        self.assertEqual(self.clicks, clicks_old + 1)
        #
        # verify clicks do NOT go through when button is disabled
        #
        clicks_old = self.clicks
        self.button.disable()
        self.button.click()
        self.assertEqual(self.clicks, clicks_old)
        #
        # verify enabled button representation
        #
        self.button.enable()
        self.assertEqual(
            self.button.__repr__(),
            f"<Button '{self.button_label}' at {hex(id(self.button))}>",
        )
        #
        # verify disabled button representation
        #
        self.button.disable()
        self.assertEqual(
            self.button.__repr__(),
            f"<Button '_{self.button_label}_' at {hex(id(self.button))}>",
        )
        return


class TestButtonWithLed(unittest.TestCase):
    """
    Verify ButtonWithLed functionality
    """

    button_label = 'foo'
    clicks = 0

    def setUp(self) -> None:
        self.button: ButtonWithLed | None = ButtonWithLed(
            self.button_label, self.callback
        )
        return

    def tearDown(self) -> None:
        self.button = None
        return

    def callback(self, button: Button) -> None:
        """
        Button callback
        """
        TestButtonWithLed.clicks += 1
        self.assertEqual(button, self.button)
        return

    def test_all(self) -> None:
        """
        Test ButtonWithLed functionality
        """
        assert self.button is not None
        self.assertFalse(self.button.is_on())
        self.assertEqual(
            self.button.__repr__(),
            f"<ButtonWithLed '{self.button_label}' at {hex(id(self.button))}>",
        )
        #
        # verify clicks go through
        #
        self.button.click()
        self.assertTrue(self.button.is_on())
        self.assertEqual(
            self.button.__repr__(),
            f"<ButtonWithLed '*_{self.button_label}_*' at {hex(id(self.button))}>",
        )
        #
        # verify clicks do NOT go through when disabled
        #
        self.assertFalse(self.button.enabled)
        self.button.click()
        self.assertTrue(self.button.is_on())
        self.assertEqual(
            self.button.__repr__(),
            f"<ButtonWithLed '*_{self.button_label}_*' at {hex(id(self.button))}>",
        )

        return


class TestButtonWithLedPanel(unittest.TestCase):
    """
    Verify ButtonWithLedPanel functionality
    """

    labels: ClassVar = ['1', '2', '3', '4', '5']

    def setUp(self) -> None:
        self.panel: ButtonWithLedPanel | None = ButtonWithLedPanel(
            self.labels, self.callback
        )
        return

    def tearDown(self) -> None:
        self.panel = None
        return

    def callback(self, panel: ButtonWithLedPanel, led_on: list[int]) -> None:  # noqa: ARG002
        """
        Callback
        """
        self.assertEqual(panel, self.panel)
        return

    def test_all(self) -> None:
        """
        Test ButtonWithLedPanel functionality
        """
        assert self.panel is not None
        self.assertEqual(self.panel.leds_on, [])
        self.assertEqual(self.panel.annotated_labels, self.labels)
        self.panel.click(2)
        self.assertEqual(self.panel.leds_on, [2])
        self.assertEqual(self.panel.annotated_labels, ['1', '2', '*_3_*', '4', '5'])
        self.panel.click(4)
        self.assertEqual(self.panel.leds_on, [2, 4])
        self.assertEqual(self.panel.annotated_labels, ['1', '2', '*_3_*', '4', '*_5_*'])

        self.panel._buttons[0].disable()
        self.panel._buttons[4].disable()
        self.assertEqual(
            self.panel.annotated_labels, ['_1_', '2', '*_3_*', '4', '*_5_*']
        )
        #
        # verify click on a disabled button has no effect
        #
        self.panel.click(4)
        self.assertEqual(
            self.panel.annotated_labels, ['_1_', '2', '*_3_*', '4', '*_5_*']
        )
        #
        # verify panel reset
        #
        self.panel.reset()
        self.assertEqual(self.panel.leds_on, [])
        self.assertEqual(self.panel.annotated_labels, ['1', '2', '3', '4', '5'])
        #
        # verify click on enabled button has effect
        #
        self.panel.click(4)
        self.assertEqual(self.panel.leds_on, [4])
        self.assertEqual(self.panel.annotated_labels, ['1', '2', '3', '4', '*_5_*'])

        self.panel.click(2)
        self.assertEqual(self.panel.leds_on, [2, 4])
        annotated_labels = ['1', '2', '*_3_*', '4', '*_5_*']
        self.assertEqual(self.panel.annotated_labels, annotated_labels)
        self.assertEqual(
            self.panel.__repr__(),
            f'<ButtonWithLedPanel {annotated_labels} at {hex(id(self.panel))}>',
        )
        return


if __name__ == '__main__':
    unittest.main()
