import tkinter as tk

from garden.models import GameState


class GardenUI:
    def __init__(self, root: tk.Tk, state: GameState) -> None:
        self.root = root
        self.state = state

        root.title("Garden MVP")
        root.resizable(False, False)

        self.status_label = tk.Label(root, text="", justify="left", anchor="w")
        self.status_label.pack(fill="x", padx=24, pady=(20, 10))

        button_frame = tk.Frame(root)
        button_frame.pack(padx=24, pady=(0, 20))

        plant_button = tk.Button(
            button_frame, text="Plant Red Rose / 种下红玫瑰", command=self.on_plant
        )
        plant_button.pack(fill="x")

        water_button = tk.Button(button_frame, text="Water / 浇水", command=self.on_water)
        water_button.pack(fill="x", pady=(6, 0))

        harvest_button = tk.Button(
            button_frame, text="Harvest / 收获", command=self.on_harvest
        )
        harvest_button.pack(fill="x", pady=(6, 0))

        self.refresh()

    def format_inventory(self) -> str:
        if not self.state.inventory:
            return "Empty"
        count = self.state.inventory.get("红玫瑰", 0)
        return f"红玫瑰 × {count}"

    def refresh(self) -> None:
        plot_state = self.state.plot.state
        crop_name = self.state.plot.crop.name if self.state.plot.crop else "None"
        inventory = self.format_inventory()
        message = self.state.message
        text = (
            f"Plot state: {plot_state}\n"
            f"Current crop: {crop_name}\n"
            f"Inventory: {inventory}\n"
            f"Message: {message}"
        )
        self.status_label.config(text=text)

    def on_plant(self) -> None:
        self.state.plant_rose()
        self.refresh()

    def on_water(self) -> None:
        self.state.water()
        self.refresh()

    def on_harvest(self) -> None:
        self.state.harvest()
        self.refresh()


def run_app(state: GameState) -> None:
    root = tk.Tk()
    GardenUI(root, state)
    root.mainloop()
