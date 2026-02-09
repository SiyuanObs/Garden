# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


FLOWER_TYPES: dict[str, str] = {
    "red_rose": "Red Rose",
    "white_lily": "White Lily",
    "eucalyptus": "Eucalyptus",
}


@dataclass(frozen=True)
class CropType:
    key: str
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
    active_flower: str = "red_rose"

    def _set_message(self, text: str) -> None:
        self.message = text

    def click_plot(self, row: int, col: int) -> None:
        plot = self.plots[row][col]
        if plot.state == "empty":
            plot.state = "planted"
            name = FLOWER_TYPES.get(self.active_flower, "Red Rose")
            plot.crop = CropType(key=self.active_flower, name=name)
            self._set_message(f"种下 {name}")
            return
        if plot.state == "planted":
            if self.water <= 0:
                self._set_message("水不足")
                return
            self.water -= 1
            plot.state = "ready"
            if plot.crop:
                self._set_message(f"浇水完成，{plot.crop.name} 可收获")
            else:
                self._set_message("浇水完成，可收获")
            return
        if plot.state == "ready":
            if plot.crop:
                self.inventory[plot.crop.key] = self.inventory.get(plot.crop.key, 0) + 1
            plot.state = "empty"
            plot.crop = None
            self._set_message("收获完成")
