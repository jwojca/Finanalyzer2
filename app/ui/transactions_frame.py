"""
Transactions view frame for FinAnalazer2.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import threading
import customtkinter as ctk

from app import database as db
from app.ui.widgets import SearchableDropdown


def _apply_treeview_style():
    is_dark = ctk.get_appearance_mode().lower() == "dark"
    bg       = "#2b2b2b" if is_dark else "#f5f5f5"
    fg       = "white"   if is_dark else "#1a1a1a"
    head_bg  = "#3b3b3b" if is_dark else "#e0e0e0"

    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        "Treeview",
        background=bg, foreground=fg,
        fieldbackground=bg, rowheight=28, borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background=head_bg, foreground=fg, relief="flat"
    )
    style.map(
        "Treeview",
        background=[('selected', '#1f538d')],
        foreground=[('selected', 'white')]
    )


MONTHS = {
    0: "Všechny",
    1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben",
    5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen",
    9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec"
}

PAGE_SIZE = 200


class TransactionsFrame(ctk.CTkFrame):
    def __init__(self, parent, on_category_change: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.on_category_change = on_category_change
        self._offset = 0
        self._total_count = 0
        self._current_rows: list = []
        self._sort_col: str = 'date'
        self._sort_dir: str = 'desc'

        _apply_treeview_style()
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Filter bar ───────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(self, height=50)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        filter_frame.grid_columnconfigure(7, weight=1)

        col = 0

        ctk.CTkLabel(filter_frame, text="Rok:").grid(
            row=0, column=col, padx=(12, 4), pady=8)
        col += 1
        self._year_var = tk.StringVar(value="Všechny")
        self._year_cb = SearchableDropdown(
            filter_frame, variable=self._year_var, width=120,
            command=lambda _: self._on_filter_change()
        )
        self._year_cb.grid(row=0, column=col, padx=4, pady=8)
        col += 1

        ctk.CTkLabel(filter_frame, text="Měsíc:").grid(
            row=0, column=col, padx=(8, 4), pady=8)
        col += 1
        self._month_var = tk.StringVar(value="Všechny")
        self._month_cb = SearchableDropdown(
            filter_frame, variable=self._month_var, width=120,
            values=list(MONTHS.values()),
            command=lambda _: self._on_filter_change()
        )
        self._month_cb.grid(row=0, column=col, padx=4, pady=8)
        col += 1

        ctk.CTkLabel(filter_frame, text="Typ:").grid(
            row=0, column=col, padx=(8, 4), pady=8)
        col += 1
        self._type_var = tk.StringVar(value="Vše")
        SearchableDropdown(
            filter_frame, variable=self._type_var, width=120,
            values=["Vše", "Příjmy", "Výdaje"],
            command=lambda _: self._on_filter_change()
        ).grid(row=0, column=col, padx=4, pady=8)
        col += 1

        ctk.CTkLabel(filter_frame, text="Kategorie:").grid(
            row=0, column=col, padx=(4, 2), pady=8)
        col += 1
        self._cat_var = tk.StringVar(value="Všechny")
        self._cat_cb = SearchableDropdown(
            filter_frame, variable=self._cat_var, width=160,
            command=lambda _: self._on_filter_change()
        )
        self._cat_cb.grid(row=0, column=col, padx=4, pady=8)
        col += 1

        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', lambda *_: self._on_filter_change())
        ctk.CTkEntry(
            filter_frame, textvariable=self._search_var,
            placeholder_text="Hledat…", width=180
        ).grid(row=0, column=col, padx=(8, 12), pady=8, sticky="ew")

        # ── Stats row ────────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self, height=36, fg_color=("#e8e8e8", "#1e1e1e"))
        stats_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        stats_frame.grid_columnconfigure(3, weight=1)

        self._income_var = tk.StringVar(value="Příjmy: 0,00 Kč")
        self._expense_var = tk.StringVar(value="Výdaje: 0,00 Kč")
        self._balance_var = tk.StringVar(value="Bilance: 0,00 Kč")
        self._count_var = tk.StringVar(value="Transakcí: 0")

        for i, (var, color) in enumerate([
            (self._income_var, "#2ecc71"),
            (self._expense_var, "#e74c3c"),
            (self._balance_var, "#3498db"),
            (self._count_var, "gray"),
        ]):
            ctk.CTkLabel(
                stats_frame, textvariable=var,
                text_color=color, font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=i, padx=16, pady=6, sticky="w")

        # ── Treeview ─────────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("date", "description", "message", "payer", "amount", "category")
        self._tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="extended"
        )
        self._col_labels = {
            'date': 'Datum',
            'description': 'Popis',
            'message': 'Zpráva',
            'payer': 'Plátce/Příjemce',
            'amount': 'Částka',
            'category': 'Kategorie',
        }
        for col in self._col_labels:
            self._tree.heading(col, text=self._col_labels[col],
                               command=lambda c=col: self._on_sort(c))

        self._tree.column("date", width=100, minwidth=80, stretch=False)
        self._tree.column("description", width=200, minwidth=120)
        self._tree.column("message", width=180, minwidth=100)
        self._tree.column("payer", width=180, minwidth=100)
        self._tree.column("amount", width=110, minwidth=80, anchor="e", stretch=False)
        self._tree.column("category", width=150, minwidth=100)

        # Tags for coloring
        self._apply_tag_colors()
        self._build_scrollbars(tree_frame)

    def _apply_tag_colors(self):
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        self._tree.tag_configure("income",       foreground="#2ecc71")
        self._tree.tag_configure("expense",      foreground="#e74c3c")
        self._tree.tag_configure("uncategorized", background="#4a3800" if is_dark else "#fff3cd")
        self._tree.tag_configure("transfer",     foreground="#888888")

    def _build_scrollbars(self, tree_frame):
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Loading overlay
        self._loading_label = ctk.CTkLabel(
            tree_frame, text="Načítám...",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#cccccc", "#2b2b2b"), corner_radius=8,
            text_color=("black", "white"), width=160, height=40
        )
        self._loading_dots = 0
        self._loading_job = None
        self._wait_job = None
        self.bind("<Destroy>", self._on_destroy)

        # Context menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="Přiřadit kategorii…", command=self._assign_category)
        self._ctx_menu.add_command(label="Vytvořit pravidlo…", command=self._create_rule)
        self._ctx_menu.add_command(label="Označit jako převod", command=self._mark_transfer)
        self._ctx_menu.add_command(label="Zrušit kategorii", command=self._clear_category)

        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Double-1>", lambda e: self._assign_category())

        # ── Pagination controls ───────────────────────────────────────────────
        pg_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        pg_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(2, 8))

        self._page_info_var = tk.StringVar(value="")
        ctk.CTkLabel(pg_frame, textvariable=self._page_info_var,
                     font=ctk.CTkFont(size=11), text_color="gray").pack(side="left", padx=12)

        self._load_more_btn = ctk.CTkButton(
            pg_frame, text="Načíst další", width=120,
            command=self._load_more
        )
        self._load_more_btn.pack(side="right", padx=12)

        self._refresh_btn = ctk.CTkButton(
            pg_frame, text="Obnovit", width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self.refresh
        )
        self._refresh_btn.pack(side="right", padx=4)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_filters(self) -> dict:
        filters: dict = {}

        year_str = self._year_var.get()
        if year_str not in ("Všechny", ""):
            try:
                filters['year'] = int(year_str)
            except ValueError:
                pass

        month_str = self._month_var.get()
        month_num = next((k for k, v in MONTHS.items() if v == month_str and k != 0), 0)
        if month_num:
            filters['month'] = month_num

        type_str = self._type_var.get()
        if type_str == "Příjmy":
            filters['type'] = 'income'
        elif type_str == "Výdaje":
            filters['type'] = 'expense'
        else:
            filters['type'] = 'all'

        cat_str = self._cat_var.get()
        if cat_str == "Bez kategorie":
            filters['category_id'] = 0
        elif cat_str not in ("Všechny", ""):
            # Find category_id by name
            cat_id = self._cat_name_to_id.get(cat_str)
            if cat_id is not None:
                filters['category_id'] = cat_id

        search = self._search_var.get().strip()
        if search:
            filters['search'] = search

        filters['order_by'] = self._sort_col
        filters['order_dir'] = self._sort_dir

        return filters

    def _on_sort(self, col: str):
        if self._sort_col == col:
            self._sort_dir = 'asc' if self._sort_dir == 'desc' else 'desc'
        else:
            self._sort_col = col
            self._sort_dir = 'asc' if col != 'date' else 'desc'
        self._update_sort_headings()
        self._offset = 0
        self._load_transactions()

    def _update_sort_headings(self):
        indicator = {'asc': ' ▲', 'desc': ' ▼'}
        for col, label in self._col_labels.items():
            text = label + (indicator[self._sort_dir] if col == self._sort_col else '')
            self._tree.heading(col, text=text)

    def _on_filter_change(self):
        self._offset = 0
        self._load_transactions()

    def _on_destroy(self, event):
        if event.widget is self:
            if self._loading_job:
                self.after_cancel(self._loading_job)
                self._loading_job = None
            if self._wait_job:
                self.after_cancel(self._wait_job)
                self._wait_job = None

    def _show_loading(self):
        self._loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self._loading_label.lift()
        if not self._loading_job:
            self._animate_loading()

    def _animate_loading(self):
        dots = "." * (self._loading_dots % 4)
        self._loading_label.configure(text=f"Načítám{dots}")
        self._loading_dots += 1
        self._loading_job = self.after(400, self._animate_loading)

    def _hide_loading(self):
        if self._loading_job:
            self.after_cancel(self._loading_job)
            self._loading_job = None
        self._loading_label.place_forget()

    def _load_transactions(self):
        if self._wait_job:
            self.after_cancel(self._wait_job)
            self._wait_job = None
        filters = self._get_filters()
        filters['limit'] = PAGE_SIZE
        filters['offset'] = self._offset

        self._show_loading()
        result: dict = {}

        def fetch():
            try:
                result['rows'] = db.get_transactions(filters)
                count_filters = dict(filters)
                count_filters.pop('limit', None)
                count_filters.pop('offset', None)
                result['count'] = db.get_transaction_count(count_filters)
            except Exception as e:
                result['error'] = e

        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
        self._wait_for_load(thread, result)

    def _wait_for_load(self, thread, result):
        if thread.is_alive():
            self._wait_job = self.after(50, lambda: self._wait_for_load(thread, result))
            return
        self._wait_job = None

        self._hide_loading()

        if 'error' in result:
            messagebox.showerror("Chyba", f"Nelze načíst transakce:\n{result['error']}")
            return

        rows = result['rows']
        self._total_count = result['count']

        if self._offset == 0:
            self._current_rows = list(rows)
            for item in self._tree.get_children():
                self._tree.delete(item)
        else:
            self._current_rows.extend(rows)

        for row in rows:
            self._insert_row(row)

        shown = len(self._current_rows)
        self._page_info_var.set(f"Zobrazeno {shown} z {self._total_count} transakcí")
        self._load_more_btn.configure(
            state="normal" if shown < self._total_count else "disabled"
        )

        self._update_stats()

    def _insert_row(self, row):
        amount = row['amount'] or 0.0
        cat_name = row['category_name'] or ""
        is_transfer = row['cat_is_transfer']
        is_uncategorized = not row['category_id']

        amount_str = f"{amount:+,.2f} Kč".replace(",", " ").replace(".", ",")
        # Reformat: Python's , as thousands sep, . as decimal
        # We want: space as thousands, comma as decimal
        amount_str = f"{amount:+.2f}".replace(".", ",")
        # Add thousands separator
        parts = amount_str.split(",")
        int_part = parts[0]
        sign = ""
        if int_part[0] in ("+", "-"):
            sign = int_part[0]
            int_part = int_part[1:]
        # Format with spaces
        formatted = ""
        for i, ch in enumerate(reversed(int_part)):
            if i > 0 and i % 3 == 0:
                formatted = " " + formatted
            formatted = ch + formatted
        amount_str = f"{sign}{formatted},{parts[1]} Kč"

        tags = []
        if is_transfer:
            tags.append("transfer")
        elif amount >= 0:
            tags.append("income")
        else:
            tags.append("expense")
        if is_uncategorized:
            tags.append("uncategorized")

        self._tree.insert(
            "", "end",
            iid=str(row['id']),
            values=(
                row['date_posted'] or "",
                row['description'] or "",
                row['message'] or "",
                row['payer_payee'] or "",
                amount_str,
                cat_name,
            ),
            tags=tuple(tags)
        )

    def _update_stats(self):
        try:
            filters = self._get_filters()
            stats = db.get_summary_stats(
                year=filters.get('year'),
                month=filters.get('month'),
            )
            # Format helper
            def fmt(v):
                s = f"{abs(v):,.2f}".replace(",", " ").replace(".", ",")
                return s

            income = stats['income']
            expense = stats['expense']
            balance = stats['balance']
            self._income_var.set(f"Příjmy: +{fmt(income)} Kč")
            self._expense_var.set(f"Výdaje: -{fmt(abs(expense))} Kč")
            sign = "+" if balance >= 0 else "-"
            self._balance_var.set(f"Bilance: {sign}{fmt(abs(balance))} Kč")
            self._count_var.set(f"Transakcí: {self._total_count}")
        except Exception:
            pass

    def _show_context_menu(self, event):
        item = self._tree.identify_row(event.y)
        if item:
            if item not in self._tree.selection():
                self._tree.selection_set(item)
            self._ctx_menu.post(event.x_root, event.y_root)

    def _get_selected_ids(self) -> list[int]:
        selected = self._tree.selection()
        ids = []
        for iid in selected:
            try:
                ids.append(int(iid))
            except ValueError:
                pass
        return ids

    def _assign_category(self):
        ids = self._get_selected_ids()
        if not ids:
            return

        dialog = CategoryAssignDialog(self, title="Přiřadit kategorii")
        self.wait_window(dialog)

        if dialog.result is not None:
            cat_id = dialog.result
            try:
                for tx_id in ids:
                    db.update_transaction_category(tx_id, cat_id, is_manual=True)
                self.refresh()
                if self.on_category_change:
                    self.on_category_change()
            except Exception as e:
                messagebox.showerror("Chyba", f"Nelze uložit kategorii:\n{e}")

    def _create_rule(self):
        ids = self._get_selected_ids()
        if len(ids) != 1:
            messagebox.showinfo("Pravidlo", "Vyberte právě jednu transakci.")
            return
        tx_id = ids[0]
        row = next((r for r in self._current_rows if r['id'] == tx_id), None)
        if not row:
            return

        from app.ui.keywords_frame import KeywordDialog
        keyword = row['message'] or row['description'] or row['payer_payee'] or ''
        dialog = KeywordDialog(self, title="Vytvořit pravidlo z transakce", keyword=keyword)
        self.wait_window(dialog)

        if dialog.result:
            kw, cat_id, field, priority, note = dialog.result
            try:
                db.add_keyword(kw, cat_id, field, priority, note)
                messagebox.showinfo("Pravidlo", f"Pravidlo '{kw}' bylo ulozeno.")
                if self.on_category_change:
                    self.on_category_change()
            except Exception as e:
                messagebox.showerror("Chyba", str(e))

    def _mark_transfer(self):
        ids = self._get_selected_ids()
        if not ids:
            return
        try:
            # Find 'Převod' category id
            transfer_cat = None
            for cat in db.get_all_categories():
                if cat['is_transfer']:
                    transfer_cat = cat['id']
                    break
            if transfer_cat is None:
                messagebox.showwarning("Upozornění",
                                       "Nenalezena kategorie Převod.")
                return
            for tx_id in ids:
                db.update_transaction_category(tx_id, transfer_cat, is_manual=True)
            self.refresh()
            if self.on_category_change:
                self.on_category_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _clear_category(self):
        ids = self._get_selected_ids()
        if not ids:
            return
        if not messagebox.askyesno("Potvrdit", "Zrušit kategorii u vybraných transakcí?"):
            return
        try:
            for tx_id in ids:
                db.update_transaction_category(tx_id, None, is_manual=False)
            self.refresh()
            if self.on_category_change:
                self.on_category_change()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def _load_more(self):
        self._offset += PAGE_SIZE
        self._load_transactions()

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._refresh_year_combo()
        self._refresh_category_combo()
        self._offset = 0
        self._load_transactions()

    def _refresh_year_combo(self):
        try:
            years = db.get_available_years()
            values = ["Všechny"] + [str(y) for y in years]
            current = self._year_var.get()
            self._year_cb.configure(values=values)
            if current not in values:
                self._year_var.set("Všechny")
        except Exception:
            pass

    def _refresh_category_combo(self):
        try:
            cats = db.get_all_categories()
            self._cat_name_to_id: dict[str, int] = {}
            values = ["Všechny", "Bez kategorie"]
            for cat in cats:
                prefix = "  └ " if cat['parent_id'] else ""
                display = prefix + cat['name']
                values.append(display)
                self._cat_name_to_id[display] = cat['id']
                self._cat_name_to_id[cat['name']] = cat['id']

            current = self._cat_var.get()
            self._cat_cb.configure(values=values)
            if current not in values:
                self._cat_var.set("Všechny")
        except Exception:
            self._cat_name_to_id = {}


# ── Category Assignment Dialog ────────────────────────────────────────────────

class CategoryAssignDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Přiřadit kategorii"):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x180")
        self.resizable(False, False)
        self.result = None

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
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Vyberte kategorii:",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=20, pady=(20, 8), sticky="w")

        try:
            cats = db.get_all_categories()
        except Exception:
            cats = []

        self._cat_map: dict[str, int] = {}
        values = []
        for cat in cats:
            prefix = "  └ " if cat['parent_id'] else ""
            display = prefix + cat['name']
            values.append(display)
            self._cat_map[display] = cat['id']
            self._cat_map[cat['name']] = cat['id']

        self._cat_var = tk.StringVar(value=values[0] if values else "")
        self._cb = SearchableDropdown(self, values=values, variable=self._cat_var, width=340)
        self._cb.grid(row=1, column=0, padx=20, pady=8)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="e")

        ctk.CTkButton(btn_frame, text="OK", width=80,
                      command=self._ok).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Zrušit", width=80,
                      fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left")

    def _ok(self):
        key = self._cat_var.get()
        self.result = self._cat_map.get(key)
        self.destroy()
