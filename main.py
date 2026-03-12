import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tkinter as tk

# Splash screen (basic tkinter = loads instantly, before customtkinter)
splash = tk.Tk()
splash.title("")
splash.overrideredirect(True)
splash.configure(bg="#1a1a1a")

w, h = 320, 110
x = (splash.winfo_screenwidth() - w) // 2
y = (splash.winfo_screenheight() - h) // 2
splash.geometry(f"{w}x{h}+{x}+{y}")

tk.Label(splash, text="FinAnalazer2",
         font=("Segoe UI", 20, "bold"),
         bg="#1a1a1a", fg="white").pack(pady=(22, 4))
tk.Label(splash, text="Načítám aplikaci...",
         font=("Segoe UI", 11),
         bg="#1a1a1a", fg="#888888").pack()

splash.update()

# Heavy imports happen here (customtkinter, matplotlib, ...)
from app.ui.main_window import MainWindow

splash.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
