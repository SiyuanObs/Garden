# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import random


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
    flower_values: dict[str, int] = field(default_factory=dict)
    coins: int = 0
    orders: list["Order"] = field(default_factory=list)
    order_timer: float = 10.0
    max_orders: int = 3
    order_interval: float = 10.0

    def __post_init__(self) -> None:
        if not self.level_xp:
            self.level_xp = self._load_level_config()
        if not self.flower_unlocks:
            self.flower_unlocks = self._load_flower_unlocks()
        if not self.flower_values:
            self.flower_values = self._load_flower_values()
        if not self.orders:
            self.generate_order()

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

    def _load_flower_values(self) -> dict[str, int]:
        config_path = (
            Path(__file__).resolve().parents[1] / "config" / "flower_values.json"
        )
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"red_rose": 3}
        values: dict[str, int] = {}
        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    values[str(key)] = int(value)
                except (ValueError, TypeError):
                    continue
        return values

    def unlocked_flowers(self) -> list[str]:
        unlocks = self.flower_unlocks or {}
        return [key for key, level in unlocks.items() if self.level >= level]

    def update_orders(self, dt: float) -> None:
        if dt <= 0:
            return
        if len(self.orders) >= self.max_orders:
            return
        self.order_timer -= dt
        if self.order_timer > 0:
            return
        self.generate_order()
        self.order_timer = self.order_interval

    def generate_order(self) -> None:
        available = self.unlocked_flowers()
        if not available:
            return
        total = random.randint(3, 5)
        num_types = random.randint(1, min(len(available), total))
        chosen = random.sample(available, num_types)
        remaining = total
        requirements: dict[str, int] = {}
        for idx, key in enumerate(chosen):
            if idx == num_types - 1:
                qty = remaining
            else:
                max_qty = remaining - (num_types - idx - 1)
                qty = random.randint(1, max_qty)
            requirements[key] = qty
            remaining -= qty
        reward = 0
        for key, qty in requirements.items():
            reward += self.flower_values.get(key, 0) * qty
        self.orders.append(Order(requirements=requirements, reward=reward))

    def deliver_order(self, index: int) -> None:
        if index < 0 or index >= len(self.orders):
            return
        order = self.orders[index]
        if not self.can_fulfill(order):
            missing = self.missing_for(order)
            if missing:
                self._set_message(f"缺少: {', '.join(missing)}")
            else:
                self._set_message("Not enough flowers")
            return
        for key, qty in order.requirements.items():
            self.inventory[key] = self.inventory.get(key, 0) - qty
        reward = self.order_value(order)
        self.coins += reward
        self.orders.pop(index)
        self.order_timer = self.order_interval
        self._set_message(f"Delivered +{reward} coins")

    def can_fulfill(self, order: "Order") -> bool:
        for key, qty in order.requirements.items():
            if self.inventory.get(key, 0) < qty:
                return False
        return True

    def missing_for(self, order: "Order") -> list[str]:
        missing: list[str] = []
        for key, qty in order.requirements.items():
            have = self.inventory.get(key, 0)
            if have < qty:
                missing.append(f"{FLOWER_TYPES.get(key, key)} x{qty - have}")
        return missing

    def order_value(self, order: "Order") -> int:
        total = 0
        for key, qty in order.requirements.items():
            total += self.flower_values.get(key, 0) * qty
        return total

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


@dataclass
class Order:
    requirements: dict[str, int]
    reward: int
