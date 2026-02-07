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
    plot: Plot = field(default_factory=Plot)
    message: str = "Ready"

    def _set_message(self, text: str) -> None:
        self.message = text

    def plant_rose(self) -> None:
        if self.plot.state != "empty":
            self._set_message("Cannot plant: plot is not empty.")
            return
        rose = CropType(name="红玫瑰")
        self.plot.state = "planted"
        self.plot.crop = rose
        self._set_message("Planted 红玫瑰.")

    def water(self) -> None:
        if self.plot.state != "planted":
            self._set_message("Cannot water: plot is not planted.")
            return
        self.plot.state = "ready"
        self._set_message("Watered: 红玫瑰 is ready to harvest.")

    def harvest(self) -> None:
        if self.plot.state != "ready":
            self._set_message("Cannot harvest: crop is not ready.")
            return
        self.inventory["红玫瑰"] = self.inventory.get("红玫瑰", 0) + 1
        self.plot.state = "empty"
        self.plot.crop = None
        self._set_message("Harvested 红玫瑰.")
