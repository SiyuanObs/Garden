# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CropType:
    name: str


@dataclass
class Plot:
    state: str = "empty"  # "empty" | "planted" | "ready"
    crop: CropType | None = None


@dataclass
class GameState:
    inventory: dict[str, int] = field(default_factory=dict)
    plots: list[list[Plot]] = field(
        default_factory=lambda: [[Plot() for _ in range(3)] for _ in range(3)]
    )
    message: str = "Ready"
    water: int = 20

    def _set_message(self, text: str) -> None:
        self.message = text

    def click_plot(self, row: int, col: int) -> None:
        plot = self.plots[row][col]
        if plot.state == "empty":
            plot.state = "planted"
            plot.crop = CropType(name="红玫瑰")
            self._set_message("种下红玫瑰")
            return
        if plot.state == "planted":
            if self.water <= 0:
                self._set_message("水不足")
                return
            self.water -= 1
            plot.state = "ready"
            self._set_message("浇水完成，红玫瑰可收获")
            return
        if plot.state == "ready":
            self.inventory["红玫瑰"] = self.inventory.get("红玫瑰", 0) + 1
            plot.state = "empty"
            plot.crop = None
            self._set_message("收获红玫瑰")
