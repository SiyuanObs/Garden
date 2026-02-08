import tkinter as tk
from tkinter import messagebox

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
        root.configure(bg="#f3f3f3")

        # Top bar canvas
        self.top_canvas = tk.Canvas(
            root, width=360, height=40, bg="#f3f3f3", highlightthickness=0
        )
        self.top_canvas.pack(fill="x", padx=16, pady=(12, 6))
        self.water_text_id = self.top_canvas.create_text(
            0, 20, anchor="w", text="", fill="#111111", font=("Helvetica", 12, "bold")
        )
        self.inventory_btn = tk.Button(
            root, text="Inventory", command=self.show_inventory
        )
        self.inventory_btn.place(relx=1.0, x=-16, y=16, anchor="ne")

        # Grid area
        grid_frame = tk.Frame(root, bg="#f3f3f3")
        grid_frame.pack(padx=16, pady=(6, 6))

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

        # Message line canvas
        self.message_canvas = tk.Canvas(
            root, width=360, height=26, bg="#f3f3f3", highlightthickness=0
        )
        self.message_canvas.pack(fill="x", padx=16, pady=(6, 12))
        self.message_text_id = self.message_canvas.create_text(
            0, 13, anchor="w", text="", fill="#111111"
        )

        self.refresh()

    def refresh(self) -> None:
        for row in range(3):
            for col in range(3):
                plot = self.state.plots[row][col]
                label = STATE_LABELS.get(plot.state, plot.state)
                self.buttons[row][col].config(text=label)

        self.top_canvas.itemconfig(
            self.water_text_id, text=f"water: {self.state.water}"
        )
        self.message_canvas.itemconfig(
            self.message_text_id, text=f"Message: {self.state.message}"
        )

    def on_click_plot(self, row: int, col: int) -> None:
        self.state.click_plot(row, col)
        self.refresh()

    def show_inventory(self) -> None:
        roses = self.state.inventory.get("红玫瑰", 0)
        messagebox.showinfo("Inventory", f"Red Rose: {roses}")


def run_app(state: GameState) -> None:
    root = tk.Tk()
    GardenUI(root, state)
    root.mainloop()
