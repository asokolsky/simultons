"""
All the button-related stuff
"""

from collections.abc import Callable


class Button:
    """
    Simple push button with a label, can be en/dis-abled, clicked.
    """

    def __init__(self, label: str, callback: Callable) -> None:
        """
        Initializer
        """
        self._callback = callback
        self._label = label
        self._enabled = True
        return

    @property
    def enabled(self) -> bool:
        """
        Enabled property
        """
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool) -> None:
        """
        Enabled property.
        When not enabled, callback is not called.
        """
        self._enabled = val
        return

    def enable(self) -> None:
        """
        Enabled property
        """
        self.enabled = True
        return

    def disable(self) -> None:
        """
        Enabled property
        """
        self.enabled = False
        return

    def click(self) -> bool:
        """
        Definitive button action to be called by users.
        Returns whether click had its effect, i.e. button was enabled.
        """
        if not self.enabled:
            return False
        self.on_click()
        return True

    def on_click(self) -> None:
        """
        Default click event handler just executes call-back, if any.
        """
        if self._callback is not None:
            self._callback(self)
        return

    @property
    def annotated_label(self) -> str:
        """
        Return the label representing enabled/disabled status
        """
        if self._enabled:
            return self._label
        return f'_{self._label}_'

    def __repr__(self) -> str:
        """
        Object print representation
        """
        return f"<{type(self).__qualname__} '{self.annotated_label}' at {hex(id(self))}>"


class ButtonWithLed(Button):
    """
    A push button with a feedback (state) LED.
    The LED does ON when the button is pushed, stays ON until reset.
    """

    def __init__(self, label: str, callback: Callable) -> None:
        """
        Initializer
        """
        super().__init__(label, callback)
        self._led_on = False
        return

    def on_click(self) -> None:
        """
        Handle button press and release, on release, I guess.
        Flips LED by default.
        """
        if not self._led_on:
            self._led_on = True
            super().on_click()
            self.disable()
        return

    def reset(self) -> None:
        """
        Turns LED off, enables the button
        """
        self._led_on = False
        self.enable()
        return

    def is_on(self) -> bool:
        """
        Retrieve led status
        """
        return self._led_on

    @property
    def annotated_label(self) -> str:
        """
        Return the label representing led on/of, enabled/disabled status
        """
        label = super().annotated_label
        if self._led_on:
            label = '*' + label + '*'
        return label

    def __repr__(self) -> str:
        """
        Object print representation
        """
        return f"<{type(self).__qualname__} '{self.annotated_label}' at {hex(id(self))}>"


class ButtonWithLedPanel:
    """
    A panel with N push buttons with feedback LEDs
    """

    def __init__(self, labels: list[str], callback: Callable) -> None:
        self._buttons: list[ButtonWithLed] = []
        self._callback = callback
        self._buttons = [
            ButtonWithLed(label, self.button_callback) for label in labels
        ]
        return

    def button_callback(self, button: Button) -> None:  # noqa: ARG002
        """
        Callback for when any button in the panel is clicked.
        """
        return

    def click(self, button: int) -> None:
        """
        Definitive button action to be called by users.
        Activate button press and release, on release, I guess.
        """
        self._buttons[button].click()
        self.on_click()
        return

    def on_click(self) -> None:
        """
        Click event handler
        """
        if self._callback is not None:
            self._callback(self, self.leds_on)
        return

    def reset(self) -> None:
        """
        Reset all the buttons in the panel.
        """
        for b in self._buttons:
            b.reset()
        return

    @property
    def leds_on(self) -> list[int]:
        """
        Returns the list of button indexes which are on
        """
        return [i for i, button in enumerate(self._buttons) if button.is_on()]

    @property
    def annotated_labels(self) -> list[str]:
        """
        Return the list of the annotated labels
        """
        return [button.annotated_label for button in self._buttons]

    def __repr__(self) -> str:
        """
        Object print representation
        """
        return f'<{type(self).__qualname__} {self.annotated_labels} at {hex(id(self))}>'
