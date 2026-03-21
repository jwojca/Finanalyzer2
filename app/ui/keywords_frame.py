"""
Keywords management frame for FinAnalazer2.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import customtkinter as ctk

from app import database as db
from app import categorizer
from app.ui.widgets import SearchableDropdown


def _attach_tooltip(widget, text: str):
    tip = None

    def show(event):
        nonlocal tip
        x = widget.winfo_rootx() + widget.winfo_width() + 4
        y = widget.winfo_rooty() + (widget.winfo_height() - 20) // 2
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        tk.Label(tip, text=text, background="#2b2b2b", foreground="white",
                 relief="flat", padx=6, pady=3,
                 font=("Segoe UI", 10)).pack()

    def hide(event):
        nonlocal tip
        if tip:
            tip.destroy()
            tip = None

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)


def _apply_treeview_style():
    is_dark = ctk.get_appearance_mode().lower() == "dark"
    bg      = "#2b2b2b" if is_dark else "#f5f5f5"
    fg      = "white"   if is_dark else "#1a1a1a"
    head_bg = "#3b3b3b" if is_dark else "#e0e0e0"

    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    style.configure(
        "Keywords.Treeview",
        background=bg, foreground=fg,
        fieldbackground=bg, rowheight=26, borderwidth=0
    )
    style.configure(
        "Keywords.Treeview.Heading",
        background=head_bg, foreground=fg, relief="flat"
    )
    style.map(
        "Keywords.Treeview",
        background=[('selected', '#1f538d')],
        foreground=[('selected', 'white')]
    )


FIELD_LABELS = {
    'all': 'Vše',
    'description': 'Popis',
    'message': 'Zpráva',
    'payer_payee': 'Plátce',
}
FIELD_VALUES = list(FIELD_LABELS.keys())
FIELD_DISPLAY = list(FIELD_LABELS.values())


class KeywordsFrame(ctk.CTkFrame):
    def __init__(self, parent, on_change: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.on_change = on_change
        _apply_treeview_style()
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, height=50)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(top, text="Filtr kategorie:").grid(
            row=0, column=0, padx=(12, 4), pady=8)
        self._cat_filter_var = tk.StringVar(value="Všechny")
        self._cat_filter_cb = SearchableDropdown(
            top, variable=self._cat_filter_var, width=180,
            command=lambda _: self._apply_filter()
        )
        self._cat_filter_cb.grid(row=0, column=1, padx=4, pady=8)

        ctk.CTkLabel(top, text="Hledat:").grid(
            row=0, column=2, padx=(12, 4), pady=8)
        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', lambda *_: self._apply_filter())
        ctk.CTkEntry(
            top, textvariable=self._search_var,
            placeholder_text="Klíčové slovo…", width=200
        ).grid(row=0, column=3, padx=(0, 12), pady=8, sticky="w")

        self._show_dups_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            top, text="Pouze duplicitní", variable=self._show_dups_var,
            command=self._apply_filter
        ).grid(row=0, column=4, padx=(0, 12), pady=8)

        # Recategorize button
        ctk.CTkButton(
            top, text="Překategorizovat vše", width=160,
            fg_color="#e67e22", hover_color="#d35400",
            command=self._recategorize_all
        ).grid(row=0, column=5, padx=(0, 12), pady=8)

        # ── Treeview ──────────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        cols = ("keyword", "category", "field", "priority", "note")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Keywords.Treeview", selectmode="browse"
        )
        self._tree.heading("keyword", text="Klíčové slovo")
        self._tree.heading("category", text="Kategorie")
        self._tree.heading("field", text="Pole")
        self._tree.heading("priority", text="Priorita")
        self._tree.heading("note", text="Poznámka")

        self._tree.column("keyword", width=200, minwidth=120)
        self._tree.column("category", width=180, minwidth=100)
        self._tree.column("field", width=90, minwidth=70, anchor="center")
        self._tree.column("priority", width=70, minwidth=50, anchor="center")
        self._tree.column("note", width=320, minwidth=150)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._tree.tag_configure("duplicate", background="#8b4a00", foreground="white")
        self._tree.bind("<Double-1>", lambda e: self._edit_keyword())

        # ── Bottom buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent", height=46)
        btn_row.grid(row=2, column=0, padx=8, pady=(2, 8), sticky="ew")

        ctk.CTkButton(btn_row, text="Přidat", width=90,
                      command=self._add_keyword).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Upravit", width=90,
                      fg_color="transparent", border_width=1,
                      command=self._edit_keyword).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Smazat", width=90,
                      fg_color="#c0392b", hover_color="#922b21",
                      command=self._delete_keyword).pack(side="left", padx=(0, 16))

        # Test section
        ctk.CTkLabel(btn_row, text="Test:").pack(side="left")
        self._test_var = tk.StringVar()
        ctk.CTkEntry(
            btn_row, textvariable=self._test_var,
            placeholder_text="Zadejte text transakce…", width=280
        ).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Testovat", width=90,
                      command=self._test_keyword).pack(side="left")
        self._test_result_var = tk.StringVar(value="")
        ctk.CTkLabel(btn_row, textvariable=self._test_result_var,
                     text_color="#2ecc71", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=8)

    # ── Refresh / Filter ─────────────────────────────────────────────────────

    def refresh(self):
        self._refresh_cat_filter()
        self._apply_filter()

    def _refresh_cat_filter(self):
        try:
            cats = db.get_all_categories()
            values = ["Všechny"] + [c['name'] for c in cats]
            self._cat_filter_cb.configure(values=values)
            self._cat_id_map = {c['name']: c['id'] for c in cats}
        except Exception:
            self._cat_id_map = {}

    def _apply_filter(self):
        cat_name = self._cat_filter_var.get()
        cat_id = self._cat_id_map.get(cat_name) if cat_name != "Všechny" else None
        search = self._search_var.get().strip().lower()

        try:
            all_kws = db.get_keywords(category_id=cat_id)
            all_kws_global = db.get_keywords()  # all keywords for duplicate detection
        except Exception as e:
            messagebox.showerror("Chyba", str(e))
            return

        # Detect duplicates (same keyword text, case-insensitive)
        from collections import Counter
        kw_counts = Counter(k['keyword'].upper() for k in all_kws_global)
        dup_keywords = {kw for kw, cnt in kw_counts.items() if cnt > 1}

        # Clear tree
        for item in self._tree.get_children():
            self._tree.delete(item)

        only_dups = self._show_dups_var.get()
        for kw in all_kws:
            if search and search not in kw['keyword'].lower():
                continue
            is_dup = kw['keyword'].upper() in dup_keywords
            if only_dups and not is_dup:
                continue
            field_label = FIELD_LABELS.get(kw['field'], kw['field'])
            self._tree.insert(
                "", "end", iid=str(kw['id']),
                values=(kw['keyword'], kw['category_name'], field_label, kw['priority'], kw['note'] or ''),
                tags=("duplicate",) if is_dup else ()
            )

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_keyword(self):
        dialog = KeywordDialog(self, title="Přidat klíčové slovo")
        self.wait_window(dialog)
        if dialog.result:
            kw, cat_id, field, priority, note = dialog.result
            try:
                db.add_keyword(kw, cat_id, field, priority, note)
                self.refresh()
                if self.on_change:
                    self.on_change()
            except Exception as e:
                messagebox.showerror("Chyba", str(e))

    def _edit_keyword(self):
        selected = self._tree.selection()
        if not selected:
            return
        kw_id = int(selected[0])
        # Fetch current data
        try:
            kws = db.get_keywords()
            current = next((k for k in kws if k['id'] == kw_id), None)
            if not current:
                return
        except Exception as e:
            messagebox.showerror("Chyba", str(e))
            return

        dialog = KeywordDialog(
            self, title="Upravit klíčové slovo",
            keyword=current['keyword'],
            category_id=current['category_id'],
            field=current['field'],
            priority=current['priority'],
            note=current['note'] or ''
        )
        self.wait_window(dialog)
        if dialog.result:
            kw, cat_id, field, priority, note = dialog.result
            try:
                db.update_keyword(kw_id, kw, cat_id, field, priority, note)
                self.refresh()
                if self.on_change:
                    self.on_change()
            except Exception as e:
                messagebox.showerror("Chyba", str(e))

    def _delete_keyword(self):
        selected = self._tree.selection()
        if not selected:
            return
        kw_id = int(selected[0])
        if not messagebox.askyesno("Smazat", "Smazat vybrané klíčové slovo?"):
            return
        try:
            db.delete_keyword(kw_id)
            self.refresh()
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _recategorize_all(self):
        if not messagebox.askyesno(
            "Překategorizovat",
            "Přeřadit všechny ne-manuální transakce podle aktuálních klíčových slov?"
        ):
            return
        try:
            count = categorizer.recategorize_all(auto_only=True)
            messagebox.showinfo("Hotovo", f"Překategorizováno {count} transakcí.")
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _test_keyword(self):
        text = self._test_var.get().strip()
        if not text:
            return
        try:
            kws = db.get_keywords()
            tx = {
                'description': text,
                'message': text,
                'payer_payee': text,
            }
            cat_id = categorizer.categorize_transaction(tx, kws)
            if cat_id:
                cat = db.get_category_by_id(cat_id)
                name = cat['name'] if cat else str(cat_id)
                self._test_result_var.set(f"→ {name}")
            else:
                self._test_result_var.set("→ (bez shody)")
        except Exception as e:
            self._test_result_var.set(f"Chyba: {e}")


# ── Keyword Add/Edit Dialog ───────────────────────────────────────────────────

class KeywordDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Klíčové slovo",
                 keyword: str = "", category_id: Optional[int] = None,
                 field: str = "all", priority: int = 0, note: str = ""):
        super().__init__(parent)
        self.title(title)
        self.geometry("460x320")
        self.resizable(False, False)
        self.result = None

        self._init_keyword = keyword
        self._init_cat_id = category_id
        self._init_field = field
        self._init_priority = priority
        self._init_note = note

        self._build_ui()
        self.after(50, self._center)
        self.grab_set()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        px, py = self.master.winfo_rootx(), self.master.winfo_rooty()
        self.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # Keyword
        ctk.CTkLabel(self, text="Klíčové slovo:").grid(
            row=0, column=0, padx=16, pady=(20, 6), sticky="w")
        self._kw_var = tk.StringVar(value=self._init_keyword)
        ctk.CTkEntry(self, textvariable=self._kw_var, width=280).grid(
            row=0, column=1, padx=(0, 16), pady=(20, 6), sticky="ew")

        # Category
        ctk.CTkLabel(self, text="Kategorie:").grid(
            row=1, column=0, padx=16, pady=6, sticky="w")
        try:
            cats = db.get_all_categories()
        except Exception:
            cats = []

        self._cat_display_map: dict[str, int] = {}
        cat_values = []
        for cat in cats:
            prefix = "  └ " if cat['parent_id'] else ""
            display = prefix + cat['name']
            cat_values.append(display)
            self._cat_display_map[display] = cat['id']
            self._cat_display_map[cat['name']] = cat['id']

        # Find current category display name
        init_display = ""
        if self._init_cat_id:
            for k, v in self._cat_display_map.items():
                if v == self._init_cat_id and not k.startswith("  └"):
                    init_display = k
                    break
            if not init_display:
                for k, v in self._cat_display_map.items():
                    if v == self._init_cat_id:
                        init_display = k
                        break

        self._cat_var = tk.StringVar(value=init_display or (cat_values[0] if cat_values else ""))
        SearchableDropdown(self, variable=self._cat_var,
                           values=cat_values, width=280).grid(
            row=1, column=1, padx=(0, 16), pady=6, sticky="ew")

        # Field
        ctk.CTkLabel(self, text="Pole:").grid(
            row=2, column=0, padx=16, pady=6, sticky="w")
        field_display = FIELD_LABELS.get(self._init_field, 'Vše')
        self._field_var = tk.StringVar(value=field_display)
        SearchableDropdown(self, variable=self._field_var,
                           values=FIELD_DISPLAY, width=160).grid(
            row=2, column=1, padx=(0, 16), pady=6, sticky="w")

        # Priority
        ctk.CTkLabel(self, text="Priorita:").grid(
            row=3, column=0, padx=16, pady=6, sticky="w")
        self._priority_var = tk.StringVar(value=str(self._init_priority))
        ctk.CTkEntry(self, textvariable=self._priority_var, width=80).grid(
            row=3, column=1, padx=(0, 16), pady=6, sticky="w")

        # Note
        ctk.CTkLabel(self, text="Poznámka:").grid(
            row=4, column=0, padx=16, pady=6, sticky="w")
        self._note_var = tk.StringVar(value=self._init_note)
        ctk.CTkEntry(self, textvariable=self._note_var, width=300,
                     placeholder_text="Volitelný popis klíčového slova…").grid(
            row=4, column=1, padx=(0, 16), pady=6, sticky="ew")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="e")

        ctk.CTkButton(btn_frame, text="OK", width=80,
                      command=self._ok).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Zrušit", width=80,
                      fg_color="transparent", border_width=1,
                      text_color=("black", "white"),
                      hover_color=("#c0392b", "#c0392b"),
                      command=self.destroy).pack(side="left")

    def _ok(self):
        kw = self._kw_var.get().strip()
        if not kw:
            messagebox.showwarning("Chyba", "Zadejte klíčové slovo.", parent=self)
            return

        cat_key = self._cat_var.get()
        cat_id = self._cat_display_map.get(cat_key)
        if cat_id is None:
            messagebox.showwarning("Chyba", "Vyberte kategorii.", parent=self)
            return

        field_display = self._field_var.get()
        field = FIELD_VALUES[FIELD_DISPLAY.index(field_display)] if field_display in FIELD_DISPLAY else 'all'

        try:
            priority = int(self._priority_var.get())
        except ValueError:
            priority = 0

        note = self._note_var.get().strip()
        self.result = (kw, cat_id, field, priority, note)
        self.destroy()
