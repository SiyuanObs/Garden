# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


FLOWER_TYPES: dict[str, str] = {
    "red_rose": "Red Rose",
    "white_lily": "White Lily",
    "eucalyptus": "Eucalyptus",
}

FLOWER_LABELS: dict[str, str] = {
    "red_rose": "Red Rose / 红玫瑰",
    "white_lily": "White Lily / 白百合",
    "eucalyptus": "Eucalyptus / 尤加利叶",
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

    def _set_message(self, text: str) -> None:
        self.message = text

    def plant_flower(self, row: int, col: int, flower_key: str) -> None:
        plot = self.plots[row][col]
        if plot.state != "empty":
            return
        name = FLOWER_TYPES.get(flower_key, "Red Rose")
        plot.state = "planted"
        plot.crop = CropType(key=flower_key, name=name)
        self._set_message(f"Planted {name}")

    def click_plot(self, row: int, col: int) -> None:
        plot = self.plots[row][col]
        if plot.state == "empty":
            return
        if plot.state == "planted":
            if self.water <= 0:
                self._set_message("Not enough water")
                return
            self.water -= 1
            plot.state = "ready"
            if plot.crop:
                self._set_message(f"Watered. {plot.crop.name} is ready")
            else:
                self._set_message("Watered. Ready to harvest")
            return
        if plot.state == "ready":
            if plot.crop:
                self.inventory[plot.crop.key] = self.inventory.get(plot.crop.key, 0) + 1
            plot.state = "empty"
            plot.crop = None
            self._set_message("Harvested")
