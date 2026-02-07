import tkinter as tk


def run_app() -> None:
    root = tk.Tk()
    root.title("Garden MVP")
    root.resizable(False, False)

    label = tk.Label(root, text="Ready")
    label.pack(padx=24, pady=(20, 10))

    exit_button = tk.Button(root, text="Exit", command=root.destroy)
    exit_button.pack(padx=24, pady=(0, 20))

    root.mainloop()
