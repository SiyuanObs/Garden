# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


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
    level: int = 1
    xp: int = 0
    level_xp: dict[int, int] = field(default_factory=dict)
    flower_unlocks: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.level_xp:
            self.level_xp = self._load_level_config()
        if not self.flower_unlocks:
            self.flower_unlocks = self._load_flower_unlocks()

    def _load_level_config(self) -> dict[int, int]:
        config_path = Path(__file__).resolve().parents[1] / "config" / "level_xp.json"
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"1": 10}
        level_xp: dict[int, int] = {}
        for key, value in data.items():
            try:
                level_xp[int(key)] = int(value)
            except (ValueError, TypeError):
                continue
        return level_xp

    def _load_flower_unlocks(self) -> dict[str, int]:
        config_path = (
            Path(__file__).resolve().parents[1] / "config" / "flower_unlocks.json"
        )
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"red_rose": 1}
        unlocks: dict[str, int] = {}
        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    unlocks[str(key)] = int(value)
                except (ValueError, TypeError):
                    continue
        return unlocks

    def xp_required(self) -> int | None:
        return self.level_xp.get(self.level)

    def gain_xp(self, amount: int) -> None:
        if amount <= 0:
            return
        self.xp += amount
        while True:
            required = self.xp_required()
            if required is None:
                break
            if self.xp < required:
                break
            self.xp -= required
            self.level += 1

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
                self.gain_xp(1)
            plot.state = "empty"
            plot.crop = None
            self._set_message("Harvested")
