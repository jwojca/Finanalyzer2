"""
Categories management frame for FinAnalazer2.
"""
import tkinter as tk
from tkinter import messagebox, colorchooser
from typing import Optional, Callable
import customtkinter as ctk

from app import database as db

PRESET_COLORS = [
    "#e74c3c", "#c0392b", "#e67e22", "#d35400",
    "#f1c40f", "#f39c12", "#2ecc71", "#27ae60",
    "#1abc9c", "#16a085", "#3498db", "#2980b9",
    "#9b59b6", "#8e44ad", "#1f538d", "#2c3e50",
    "#95a5a6", "#7f8c8d", "#888888", "#ffffff",
]


class CategoriesFrame(ctk.CTkFrame):
    def __init__(self, parent, on_change: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.on_change = on_change
        self._selected_cat_id: Optional[int] = None
        self._selected_parent_id: Optional[int] = None
        self._color_var = tk.StringVar(value="#5599ff")

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left: category tree ───────────────────────────────────────────────
        left = ctk.CTkFrame(self, width=300)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_propagate(False)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Kategorie",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, pady=(12, 4), padx=12, sticky="w")

        self._cat_scroll = ctk.CTkScrollableFrame(left)
        self._cat_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self._cat_scroll.grid_columnconfigure(0, weight=1)

        # Add category buttons
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.grid(row=2, column=0, pady=(4, 8), padx=8, sticky="ew")
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="+ Hlavní", height=32,
                      command=self._add_main_category).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(btn_row, text="+ Pod-kat.", height=32,
                      command=self._add_sub_category).grid(
            row=0, column=1, padx=(4, 0), sticky="ew")

        # ── Right: edit form ──────────────────────────────────────────────────
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Upravit kategorii",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(12, 8), padx=16, sticky="w")

        # Name
        ctk.CTkLabel(right, text="Název:").grid(
            row=1, column=0, padx=16, pady=6, sticky="w")
        self._name_var = tk.StringVar()
        ctk.CTkEntry(right, textvariable=self._name_var).grid(
            row=1, column=1, padx=(0, 16), pady=6, sticky="ew")

        # Parent
        ctk.CTkLabel(right, text="Nadřazená:").grid(
            row=2, column=0, padx=16, pady=6, sticky="w")
        self._parent_var = tk.StringVar(value="(žádná)")
        self._parent_cb = ctk.CTkComboBox(right, variable=self._parent_var, width=200)
        self._parent_cb.grid(row=2, column=1, padx=(0, 16), pady=6, sticky="w")

        # Color
        ctk.CTkLabel(right, text="Barva:").grid(
            row=3, column=0, padx=16, pady=6, sticky="w")
        color_frame = ctk.CTkFrame(right, fg_color="transparent")
        color_frame.grid(row=3, column=1, padx=(0, 16), pady=6, sticky="w")

        self._color_preview = tk.Label(
            color_frame, bg=self._color_var.get(),
            width=4, height=1, relief="solid"
        )
        self._color_preview.pack(side="left", padx=(0, 8))

        self._color_entry = ctk.CTkEntry(
            color_frame, textvariable=self._color_var, width=90)
        self._color_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(color_frame, text="Vybrat…", width=80,
                      command=self._pick_color).pack(side="left")

        # Preset color grid
        presets_frame = ctk.CTkFrame(right, fg_color="transparent")
        presets_frame.grid(row=4, column=0, columnspan=2, padx=16, pady=4, sticky="w")
        for i, c in enumerate(PRESET_COLORS):
            btn = tk.Button(
                presets_frame, bg=c, width=2, height=1,
                relief="flat", bd=1,
                command=lambda col=c: self._set_color(col)
            )
            btn.grid(row=i // 10, column=i % 10, padx=1, pady=1)

        # Flags
        ctk.CTkLabel(right, text="Typ:").grid(
            row=5, column=0, padx=16, pady=6, sticky="w")
        flags_frame = ctk.CTkFrame(right, fg_color="transparent")
        flags_frame.grid(row=5, column=1, padx=(0, 16), pady=6, sticky="w")

        self._is_transfer_var = tk.BooleanVar()
        self._is_income_var = tk.BooleanVar()

        ctk.CTkCheckBox(flags_frame, text="Převod (inter-účet)",
                        variable=self._is_transfer_var).pack(side="left", padx=(0, 16))
        ctk.CTkCheckBox(flags_frame, text="Příjem",
                        variable=self._is_income_var).pack(side="left")

        # Direction
        ctk.CTkLabel(right, text="Směr plateb:").grid(
            row=6, column=0, padx=16, pady=6, sticky="w")
        self._direction_var = tk.StringVar(value="Oboje")
        self._direction_cb = ctk.CTkComboBox(
            right,
            variable=self._direction_var,
            values=["Oboje", "Pouze příchozí (+)", "Pouze odchozí (-)"],
            state="readonly",
            width=200
        )
        self._direction_cb.grid(row=6, column=1, padx=(0, 16), pady=6, sticky="w")

        # Save/Delete buttons
        btn_row2 = ctk.CTkFrame(right, fg_color="transparent")
        btn_row2.grid(row=7, column=0, columnspan=2, pady=(16, 8), padx=16, sticky="w")

        ctk.CTkButton(btn_row2, text="Uložit", width=100,
                      command=self._save_category).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row2, text="Nová kategorie", width=130,
                      fg_color="transparent", border_width=1,
                      command=self._new_category).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row2, text="Smazat", width=90,
                      fg_color="#c0392b", hover_color="#922b21",
                      command=self._delete_category).pack(side="left")

        # Info label
        self._info_var = tk.StringVar(value="")
        ctk.CTkLabel(right, textvariable=self._info_var,
                     text_color="gray", font=ctk.CTkFont(size=11)).grid(
            row=8, column=0, columnspan=2, padx=16, pady=4, sticky="w")

    # ── Direction helpers ─────────────────────────────────────────────────────

    _DIRECTION_TO_DB = {
        "Oboje": None,
        "Pouze příchozí (+)": "income",
        "Pouze odchozí (-)": "expense",
    }
    _DIRECTION_FROM_DB = {v: k for k, v in _DIRECTION_TO_DB.items()}

    def _direction_label(self, direction: Optional[str]) -> str:
        return self._DIRECTION_FROM_DB.get(direction, "Oboje")

    def _direction_db(self) -> Optional[str]:
        return self._DIRECTION_TO_DB.get(self._direction_var.get())

    # ── Category tree rendering ───────────────────────────────────────────────

    def refresh(self):
        self._refresh_tree()
        self._refresh_parent_combo()

    def _refresh_tree(self):
        # Clear existing widgets in scroll frame
        for widget in self._cat_scroll.winfo_children():
            widget.destroy()

        try:
            all_cats = db.get_all_categories()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))
            return

        # Separate top-level and sub-categories
        top_cats = [c for c in all_cats if not c['parent_id']]
        sub_map: dict[int, list] = {}
        for c in all_cats:
            if c['parent_id']:
                sub_map.setdefault(c['parent_id'], []).append(c)

        # Count transactions per category
        try:
            tx_counts = self._get_tx_counts()
        except Exception:
            tx_counts = {}

        row = 0
        for cat in top_cats:
            self._add_cat_widget(cat, indent=0, row=row,
                                 tx_count=tx_counts.get(cat['id'], 0))
            row += 1
            for sub in sub_map.get(cat['id'], []):
                self._add_cat_widget(sub, indent=1, row=row,
                                     tx_count=tx_counts.get(sub['id'], 0))
                row += 1

    def _get_tx_counts(self) -> dict:
        from app import database as db2
        import sqlite3
        counts = {}
        with db2.get_conn() as conn:
            rows = conn.execute(
                "SELECT category_id, COUNT(*) as cnt FROM transactions "
                "WHERE category_id IS NOT NULL GROUP BY category_id"
            ).fetchall()
            for r in rows:
                counts[r['category_id']] = r['cnt']
        return counts

    def _add_cat_widget(self, cat, indent: int, row: int, tx_count: int):
        frame = ctk.CTkFrame(
            self._cat_scroll,
            fg_color=("#d0d0d0", "#333333"),
            corner_radius=4
        )
        frame.grid(row=row, column=0, sticky="ew",
                   padx=(indent * 20, 0), pady=2)
        frame.grid_columnconfigure(1, weight=1)

        # Colored dot
        dot = tk.Label(frame, bg=cat['color'] or '#888888',
                       width=2, height=1)
        dot.grid(row=0, column=0, padx=(8, 4), pady=4)

        # Name
        flags = ""
        if cat['is_transfer']:
            flags += " [T]"
        if cat['is_income']:
            flags += " [P]"
        direction = cat['direction'] if 'direction' in cat.keys() else None
        if direction == 'income':
            flags += " [↓]"
        elif direction == 'expense':
            flags += " [↑]"

        name_label = ctk.CTkLabel(
            frame, text=cat['name'] + flags,
            anchor="w", font=ctk.CTkFont(size=12)
        )
        name_label.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        # Count
        if tx_count:
            ctk.CTkLabel(
                frame, text=f"{tx_count}",
                font=ctk.CTkFont(size=11), text_color="gray",
                width=40
            ).grid(row=0, column=2, padx=(0, 8))

        # Bind click
        cat_id = cat['id']
        for widget in (frame, name_label, dot):
            widget.bind("<Button-1>", lambda e, cid=cat_id: self._select_category(cid))
        frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=("#bebebe", "#3d3d3d")))
        frame.bind("<Leave>", lambda e, f=frame: f.configure(fg_color=("#d0d0d0", "#333333")))

    def _select_category(self, cat_id: int):
        self._selected_cat_id = cat_id
        try:
            cat = db.get_category_by_id(cat_id)
            if cat:
                self._name_var.set(cat['name'])
                self._set_color(cat['color'] or '#5599ff')
                self._is_transfer_var.set(bool(cat['is_transfer']))
                self._is_income_var.set(bool(cat['is_income']))
                direction = cat['direction'] if 'direction' in cat.keys() else None
                self._direction_var.set(self._direction_label(direction))
                # Parent
                if cat['parent_id']:
                    parent = db.get_category_by_id(cat['parent_id'])
                    self._parent_var.set(parent['name'] if parent else "(žádná)")
                    self._selected_parent_id = cat['parent_id']
                else:
                    self._parent_var.set("(žádná)")
                    self._selected_parent_id = None
                self._info_var.set(f"Vybráno: {cat['name']} (ID {cat_id})")
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _refresh_parent_combo(self):
        try:
            top_cats = db.get_categories()  # parent_id=None => top-level
            values = ["(žádná)"] + [c['name'] for c in top_cats]
            self._parent_cb.configure(values=values)
            self._parent_map = {c['name']: c['id'] for c in top_cats}
        except Exception:
            self._parent_map = {}

    def _pick_color(self):
        color = colorchooser.askcolor(
            color=self._color_var.get(), title="Vybrat barvu"
        )
        if color and color[1]:
            self._set_color(color[1])

    def _set_color(self, color: str):
        self._color_var.set(color)
        try:
            self._color_preview.configure(bg=color)
        except Exception:
            pass

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_main_category(self):
        self._selected_cat_id = None
        self._selected_parent_id = None
        self._name_var.set("")
        self._set_color("#5599ff")
        self._is_transfer_var.set(False)
        self._is_income_var.set(False)
        self._direction_var.set("Oboje")
        self._parent_var.set("(žádná)")
        self._info_var.set("Nová hlavní kategorie")

    def _add_sub_category(self):
        if self._selected_cat_id is None:
            messagebox.showinfo("Upozornění",
                                "Nejdřív vyberte nadřazenou kategorii v seznamu vlevo.")
            return
        try:
            cat = db.get_category_by_id(self._selected_cat_id)
            if cat and not cat['parent_id']:
                # Selected is top-level → will be parent
                self._selected_parent_id = self._selected_cat_id
            elif cat:
                self._selected_parent_id = cat['parent_id']
        except Exception:
            pass

        self._selected_cat_id = None
        self._name_var.set("")
        self._set_color("#5599ff")
        self._is_transfer_var.set(False)
        self._is_income_var.set(False)
        self._direction_var.set("Oboje")
        # Set parent combo
        try:
            if self._selected_parent_id:
                parent = db.get_category_by_id(self._selected_parent_id)
                self._parent_var.set(parent['name'] if parent else "(žádná)")
        except Exception:
            pass
        self._info_var.set("Nová podkategorie")

    def _new_category(self):
        self._selected_cat_id = None
        self._name_var.set("")
        self._set_color("#5599ff")
        self._is_transfer_var.set(False)
        self._is_income_var.set(False)
        self._direction_var.set("Oboje")
        self._parent_var.set("(žádná)")
        self._info_var.set("Nová kategorie")

    def _save_category(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("Chyba", "Zadejte název kategorie.")
            return

        color = self._color_var.get().strip()
        if not color.startswith('#'):
            color = '#5599ff'

        is_transfer = self._is_transfer_var.get()
        is_income = self._is_income_var.get()

        # Resolve parent
        parent_name = self._parent_var.get()
        parent_id = self._parent_map.get(parent_name) if parent_name != "(žádná)" else None

        direction = self._direction_db()
        try:
            if self._selected_cat_id is not None:
                db.update_category(self._selected_cat_id, name, color,
                                   is_transfer=is_transfer, is_income=is_income,
                                   parent_id=parent_id, direction=direction)
                self._info_var.set(f"Uloženo: {name}")
            else:
                new_id = db.add_category(name, parent_id, color,
                                         is_transfer=is_transfer, is_income=is_income,
                                         direction=direction)
                self._selected_cat_id = new_id
                self._info_var.set(f"Přidáno: {name}")

            self.refresh()
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _delete_category(self):
        if self._selected_cat_id is None:
            messagebox.showwarning("Upozornění", "Vyberte kategorii ke smazání.")
            return
        try:
            cat = db.get_category_by_id(self._selected_cat_id)
            name = cat['name'] if cat else str(self._selected_cat_id)
        except Exception:
            name = str(self._selected_cat_id)

        if not messagebox.askyesno(
            "Smazat kategorii",
            f"Opravdu smazat kategorii '{name}'?\n"
            "Všechny přiřazené transakce ztratí kategorii."
        ):
            return

        try:
            db.delete_category(self._selected_cat_id)
            self._selected_cat_id = None
            self._selected_parent_id = None
            self._name_var.set("")
            self._info_var.set("Kategorie smazána.")
            self.refresh()
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))
