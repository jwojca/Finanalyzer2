"""
Main application window for FinAnalazer2.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import customtkinter as ctk

from app import database as db
from app.default_data import load_defaults
from app import categorizer

from app.ui.transactions_frame import TransactionsFrame
from app.ui.categories_frame import CategoriesFrame
from app.ui.keywords_frame import KeywordsFrame
from app.ui.import_frame import ImportDialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SIDEBAR_WIDTH = 210
NAV_BUTTON_HEIGHT = 40


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FinAnalazer2")
        self.geometry("1280x800")
        self.minsize(900, 600)

        try:
            db.init_db()
            load_defaults()
        except Exception as e:
            messagebox.showerror("Chyba databáze", f"Nelze inicializovat databázi:\n{e}")
            self.destroy()
            return

        self._build_ui()
        self.show_frame("prehled")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, self._init_async)

    def _on_close(self):
        self.quit()
        self.destroy()

    def _build_ui(self):
        # Grid layout: sidebar | content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(99, weight=1)  # spacer

        # App title
        title_label = ctk.CTkLabel(
            self.sidebar, text="FinAnalazer2",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        # Import button
        self.btn_import = ctk.CTkButton(
            self.sidebar, text="Importovat CSV",
            height=36, fg_color="#2ecc71", hover_color="#27ae60",
            text_color="black", font=ctk.CTkFont(weight="bold"),
            command=self._open_import
        )
        self.btn_import.grid(row=1, column=0, padx=12, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(self.sidebar, text="NAVIGACE",
                     font=ctk.CTkFont(size=10), text_color="gray").grid(
            row=2, column=0, padx=16, pady=(0, 4), sticky="w"
        )

        # Nav buttons
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("prehled", "Přehled"),
            ("transakce", "Transakce"),
            ("kategorie", "Kategorie"),
            ("klic_slova", "Klíčová slova"),
            ("grafy", "Grafy"),
        ]
        for i, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                height=NAV_BUTTON_HEIGHT, anchor="w",
                fg_color="transparent", hover_color="#1f538d",
                border_width=0, corner_radius=6,
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=3 + i, column=0, padx=8, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        # Uncategorized badge label (shown on Transakce button)
        self._badge_var = tk.StringVar(value="")
        self._badge_label = ctk.CTkLabel(
            self.sidebar, textvariable=self._badge_var,
            fg_color="#e74c3c", corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white", width=30, height=18
        )

        # ── Content area ──────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Připraveno")
        status_bar = ctk.CTkLabel(
            self, textvariable=self.status_var,
            height=24, anchor="w",
            font=ctk.CTkFont(size=11),
            fg_color=("#d0d0d0", "#1a1a1a"),
            text_color=("black", "#aaaaaa"),
            corner_radius=0
        )
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # ── Build frames ──────────────────────────────────────────────────────
        self._frames: dict[str, ctk.CTkFrame] = {}

        self._frames["prehled"] = self._build_overview_frame()
        self._frames["transakce"] = TransactionsFrame(
            self.content, on_category_change=self.refresh_all
        )
        self._frames["kategorie"] = CategoriesFrame(
            self.content, on_change=self.refresh_all
        )
        self._frames["klic_slova"] = KeywordsFrame(
            self.content, on_change=self.refresh_all
        )
        self._frames["grafy"] = None  # lazy init

        for frame in self._frames.values():
            if frame is not None:
                frame.grid(row=0, column=0, sticky="nsew")
                frame.grid_remove()

        self._current_frame = None

    def _build_overview_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            frame, text="Vítejte v FinAnalazer2",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(40, 8))

        ctk.CTkLabel(
            frame,
            text=(
                "Aplikace pro analýzu finančních transakcí z mBank.\n\n"
                "Začněte importem CSV souboru tlačítkem 'Importovat CSV' vlevo.\n"
                "Poté můžete procházet Transakce, nastavit Kategorie\n"
                "a zobrazit Grafy."
            ),
            font=ctk.CTkFont(size=14), justify="center"
        ).grid(row=1, column=0, pady=8)

        self._overview_stats = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=13), justify="center",
            text_color="gray"
        )
        self._overview_stats.grid(row=2, column=0, pady=16)

        return frame

    def _update_overview_stats(self):
        try:
            years = db.get_available_years()
            if not years:
                self._overview_stats.configure(text="Databáze je prázdná. Importujte CSV soubor.")
                return
            tx_count = db.get_transaction_count()
            uncategorized = db.get_uncategorized_count()
            stats = db.get_summary_stats()
            text = (
                f"Celkem transakcí: {tx_count}  |  "
                f"Bez kategorie: {uncategorized}\n"
                f"Celkový příjem: {stats['income']:,.2f} Kč  |  "
                f"Celkové výdaje: {stats['expense']:,.2f} Kč  |  "
                f"Bilance: {stats['balance']:,.2f} Kč\n"
                f"Roky v databázi: {', '.join(str(y) for y in years)}"
            )
            self._overview_stats.configure(text=text)
        except Exception:
            pass

    def _init_async(self):
        result = {}

        def work():
            try:
                result['count'] = categorizer.categorize_all_uncategorized()
            except Exception as e:
                result['error'] = e

        def check(thread):
            if thread.is_alive():
                self.after(100, lambda: check(thread))
                return
            if result.get('count'):
                self.set_status(f"Kategorizovano: {result['count']} transakci")
            else:
                self.set_status("Připraveno")
            self._update_badge()
            self._update_overview_stats()

        t = threading.Thread(target=work, daemon=True)
        t.start()
        check(t)

    def _open_import(self):
        dialog = ImportDialog(self, on_done=self._on_import_done)
        dialog.grab_set()

    def _on_import_done(self, imported: int, skipped: int):
        try:
            count = categorizer.categorize_all_uncategorized()
            self.set_status(
                f"Import dokončen: {imported} nových, {skipped} duplikátů. "
                f"Kategorizováno: {count}."
            )
        except Exception as e:
            self.set_status(f"Chyba při kategorizaci po importu: {e}")
        self.refresh_all()

    def show_frame(self, name: str):
        # Deactivate all
        for btn in self._nav_buttons.values():
            btn.configure(fg_color="transparent")

        # Lazy init for charts (matplotlib is slow to initialize)
        if name == "grafy" and self._frames["grafy"] is None:
            from app.ui.charts_frame import ChartsFrame
            self._frames["grafy"] = ChartsFrame(self.content)
            self._frames["grafy"].grid(row=0, column=0, sticky="nsew")

        frame = self._frames.get(name)
        if frame is None:
            return

        if self._current_frame:
            self._current_frame.grid_remove()

        frame.grid()
        self._current_frame = frame
        self._current_frame_name = name

        if name in self._nav_buttons:
            self._nav_buttons[name].configure(fg_color="#1f538d")

        # Refresh relevant frames
        if name == "prehled":
            self._update_overview_stats()
        elif name == "transakce":
            self._frames["transakce"].refresh()
        elif name == "kategorie":
            self._frames["kategorie"].refresh()
        elif name == "klic_slova":
            self._frames["klic_slova"].refresh()
        elif name == "grafy":
            self._frames["grafy"].refresh()

        self._update_badge()

    def refresh_all(self):
        self._update_badge()
        self._update_overview_stats()
        current = getattr(self, '_current_frame_name', None)
        if current == "transakce":
            self._frames["transakce"].refresh()
        elif current == "kategorie":
            self._frames["kategorie"].refresh()
        elif current == "klic_slova":
            self._frames["klic_slova"].refresh()
        elif current == "grafy":
            self._frames["grafy"].refresh()

    def _update_badge(self):
        try:
            count = db.get_uncategorized_count()
            if count > 0:
                self._badge_var.set(str(count))
                # Position badge near Transakce button
                btn = self._nav_buttons.get("transakce")
                if btn:
                    self._badge_label.place(
                        in_=self.sidebar, x=170, rely=0,
                        y=btn.winfo_y() + 11
                    )
                    self._badge_label.lift()
            else:
                self._badge_var.set("")
                self._badge_label.place_forget()
        except Exception:
            pass

    def set_status(self, text: str):
        self.status_var.set(text)
        self.after(6000, lambda: self.status_var.set("Připraveno")
                   if self.status_var.get() == text else None)
