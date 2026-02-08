import tkinter as tk

from garden.models import GameState


STATE_LABELS = {
    "empty": "空",
    "planted": "🌱",
    "ready": "🌹",
}


class GardenUI:
    def __init__(self, root: tk.Tk, state: GameState) -> None:
        self.root = root
        self.state = state
        self.buttons: list[list[tk.Button]] = []

        root.title("Garden MVP")
        root.resizable(False, False)

        self.info_label = tk.Label(root, text="", justify="left", anchor="w")
        self.info_label.pack(fill="x", padx=20, pady=(16, 8))

        grid_frame = tk.Frame(root)
        grid_frame.pack(padx=20, pady=(0, 10))

        for row in range(3):
            button_row: list[tk.Button] = []
            for col in range(3):
                btn = tk.Button(
                    grid_frame,
                    text="",
                    width=6,
                    height=3,
                    command=lambda r=row, c=col: self.on_click_plot(r, c),
                )
                btn.grid(row=row, column=col, padx=6, pady=6)
                button_row.append(btn)
            self.buttons.append(button_row)

        self.refresh()

    def refresh(self) -> None:
        for row in range(3):
            for col in range(3):
                plot = self.state.plots[row][col]
                label = STATE_LABELS.get(plot.state, plot.state)
                self.buttons[row][col].config(text=label)

        roses = self.state.inventory.get("红玫瑰", 0)
        self.info_label.config(
            text=(
                f"Water: {self.state.water}    "
                f"Inventory: 红玫瑰 × {roses}\n"
                f"Message: {self.state.message}"
            )
        )

    def on_click_plot(self, row: int, col: int) -> None:
        self.state.click_plot(row, col)
        self.refresh()


def run_app(state: GameState) -> None:
    root = tk.Tk()
    GardenUI(root, state)
    root.mainloop()
