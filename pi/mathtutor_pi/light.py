"""The status light each kid's button has."""

from typing import Protocol


class Light(Protocol):
    def steady(self) -> None:
        """Ready: solid on."""

    def blink(self) -> None:
        """Working: slow blink until the next call."""

    def flash(self) -> None:
        """Failed: fast flash until the next call."""
