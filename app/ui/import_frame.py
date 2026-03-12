"""
Import dialog for CSV files – FinAnalazer2.
"""
import threading
from tkinter import filedialog, messagebox
from typing import Callable, Optional
import customtkinter as ctk

from app.csv_parser import parse_mbank_csv
from app import database as db


class ImportDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_done: Optional[Callable[[int, int], None]] = None):
        super().__init__(parent)
        self.title("Importovat CSV")
        self.geometry("520x300")
        self.resizable(False, False)
        self.on_done = on_done

        self._build_ui()
        self.after(100, self._center)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        px, py = self.master.winfo_rootx(), self.master.winfo_rooty()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self, text="Import mBank CSV",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, pady=(20, 8), padx=20)

        # File path row
        file_frame = ctk.CTkFrame(self, fg_color="transparent")
        file_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar()
        self._path_entry = ctk.CTkEntry(
            file_frame, textvariable=self._path_var,
            placeholder_text="Vyberte CSV soubor…"
        )
        self._path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            file_frame, text="Procházet", width=90,
            command=self._browse
        ).grid(row=0, column=1)

        # Progress bar
        self._progress = ctk.CTkProgressBar(self)
        self._progress.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        self._progress.set(0)

        # Status label
        self._status_var = ctk.StringVar(value="Vyberte soubor a spusťte import.")
        self._status_label = ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=ctk.CTkFont(size=12), wraplength=460
        )
        self._status_label.grid(row=3, column=0, padx=20, pady=4)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=20, pady=(8, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        self._import_btn = ctk.CTkButton(
            btn_frame, text="Importovat",
            command=self._start_import
        )
        self._import_btn.grid(row=0, column=0, padx=(0, 8), sticky="e")

        ctk.CTkButton(
            btn_frame, text="Zavřít",
            fg_color="transparent", border_width=1,
            command=self.destroy
        ).grid(row=0, column=1)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Vyberte mBank CSV soubor",
            filetypes=[("CSV soubory", "*.csv"), ("Všechny soubory", "*.*")]
        )
        if path:
            self._path_var.set(path)

    def _start_import(self):
        path = self._path_var.get().strip()
        if not path:
            messagebox.showwarning("Chyba", "Vyberte soubor CSV.", parent=self)
            return

        self._import_btn.configure(state="disabled", text="Importuji…")
        self._progress.set(0)
        self._status_var.set("Čtu soubor…")

        thread = threading.Thread(target=self._do_import, args=(path,), daemon=True)
        thread.start()

    def _do_import(self, path: str):
        try:
            transactions = parse_mbank_csv(path)
            total = len(transactions)
            if total == 0:
                self.after(0, lambda: self._finish_import(0, 0, "Soubor neobsahuje žádné transakce."))
                return

            imported = 0
            skipped = 0
            for i, tx in enumerate(transactions):
                ok = db.insert_transaction(
                    date_posted=tx['date_posted'],
                    date_executed=tx['date_executed'],
                    description=tx['description'],
                    message=tx['message'],
                    payer_payee=tx['payer_payee'],
                    account_number=tx['account_number'],
                    ks=tx['ks'],
                    vs=tx['vs'],
                    ss=tx['ss'],
                    amount=tx['amount'],
                    balance=tx['balance'],
                    import_hash=tx['import_hash'],
                )
                if ok:
                    imported += 1
                else:
                    skipped += 1

                # Update progress every 50 rows
                if i % 50 == 0:
                    progress = (i + 1) / total
                    self.after(0, lambda p=progress: self._progress.set(p))

            self.after(0, lambda: self._finish_import(imported, skipped))
        except Exception as e:
            self.after(0, lambda: self._finish_import(0, 0, f"Chyba: {e}"))

    def _finish_import(self, imported: int, skipped: int, error: str = ""):
        self._progress.set(1.0)
        self._import_btn.configure(state="normal", text="Importovat")

        if error:
            self._status_var.set(error)
            messagebox.showerror("Chyba importu", error, parent=self)
            return

        msg = f"Importováno: {imported} nových transakcí\nPřeskočeno duplikátů: {skipped}"
        self._status_var.set(msg)

        if self.on_done:
            self.on_done(imported, skipped)
