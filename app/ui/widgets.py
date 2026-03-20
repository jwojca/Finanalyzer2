"""
Shared custom widgets for FinAnalazer2.
"""
import tkinter as tk
import customtkinter as ctk


class SearchableDropdown(ctk.CTkFrame):
    """
    Drop-in replacement for CTkComboBox with live search filtering.
    As the user types, the popup list filters to matching options.
    """

    def __init__(self, parent, values=None, variable=None,
                 width=150, command=None, placeholder_text="", **kwargs):
        # outer frame carries the border so it's never clipped
        kwargs.pop("fg_color", None)  # don't override default bg
        super().__init__(parent, width=width,
                         corner_radius=6,
                         border_width=1,
                         border_color=("black", "#2b2b2b"),
                         **kwargs)

        self._all_values: list[str] = list(values or [])
        self._var = variable if variable is not None else tk.StringVar()
        self._command = command
        self._width = width
        self._popup: tk.Toplevel | None = None
        self._listbox: tk.Listbox | None = None
        self._scrollbar: tk.Scrollbar | None = None
        self._ignore_focus_out = False
        self._saved_value: str = ""  # value before user started typing
        self._just_selected = False  # prevents focus-in from clearing after selection
        self._click_handled = False  # Button-1 fired first, FocusIn should skip

        # fix width — CTkFrame ignores width unless propagation is off
        self.grid_propagate(False)
        self.configure(width=width, height=36)

        # ── inner frame — transparent, just for layout ───────────────────────
        self._inner = ctk.CTkFrame(self, fg_color="transparent",
                                   corner_radius=0, width=width, height=34)
        self._inner.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._inner.grid_columnconfigure(0, weight=1)
        self._inner.grid_propagate(False)

        entry_w = max(20, width - 34)
        self._entry = ctk.CTkEntry(
            self._inner,
            textvariable=self._var,
            placeholder_text=placeholder_text,
            border_width=0,
            fg_color="transparent",
            width=entry_w,
            height=34,
        )
        self._entry.grid(row=0, column=0, padx=(6, 0), sticky="ew")

        self._arrow = ctk.CTkButton(
            self._inner, text="▾", width=28, height=34,
            fg_color="transparent", hover=False, corner_radius=0,
            text_color=("black", "white"),
            command=self._toggle_popup,
        )
        self._arrow.grid(row=0, column=1, padx=(0, 2))

        # bindings
        self._entry.bind("<Button-1>", self._on_entry_click)
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<Return>", lambda _: self._select_first())
        self._entry.bind("<Escape>", lambda _: self._cancel())
        self._entry.bind("<Down>", lambda _: self._move_selection(1))
        self._entry.bind("<Up>", lambda _: self._move_selection(-1))

    # ── public API (matches CTkComboBox) ────────────────────────────────────

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        self._var.set(value)

    def configure(self, **kwargs):
        if "values" in kwargs:
            self._all_values = list(kwargs.pop("values"))
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._entry.configure(state=state)
            self._arrow.configure(state=state)
        if "width" in kwargs:
            self._width = kwargs["width"]
            if hasattr(self, "_entry"):
                self._entry.configure(width=max(20, self._width - 34))
            if hasattr(self, "_inner"):
                self._inner.configure(width=self._width)
        super().configure(**kwargs)

    def set_values(self, values: list[str]):
        self._all_values = list(values)

    # ── popup lifecycle ──────────────────────────────────────────────────────

    def _toggle_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._show_popup()

    def _on_entry_click(self, _event=None):
        """Handles both first click (gaining focus) and re-click (already focused)."""
        self._click_handled = True
        if self._just_selected:
            self._just_selected = False
            return  # keep showing selected value on first click after selection
        self._saved_value = self._var.get()
        self._var.set("")
        if not (self._popup and self._popup.winfo_exists()):
            self._show_popup()

    def _on_focus_in(self, _event=None):
        if self._click_handled:
            self._click_handled = False
            return  # Button-1 already handled this
        if self._just_selected:
            self._just_selected = False
            return
        self._saved_value = self._var.get()
        self._var.set("")  # Tab navigation — clear so user types into empty field
        if not (self._popup and self._popup.winfo_exists()):
            self._show_popup()

    def _show_popup(self):
        if self._popup and self._popup.winfo_exists():
            return

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        lb_bg   = "#2b2b2b" if is_dark else "#ffffff"
        lb_fg   = "#ffffff"  if is_dark else "#1a1a1a"
        sel_bg  = "#1f538d"
        brd_clr = "#555555"  if is_dark else "#aaaaaa"

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(bg=brd_clr)

        container = tk.Frame(self._popup, bg=lb_bg)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        self._scrollbar = tk.Scrollbar(container, orient="vertical")
        self._listbox = tk.Listbox(
            container,
            bg=lb_bg, fg=lb_fg,
            selectbackground=sel_bg, selectforeground="white",
            borderwidth=0, highlightthickness=0,
            activestyle="none",
            font=("Segoe UI", 12),
            yscrollcommand=self._scrollbar.set,
        )
        self._scrollbar.configure(command=self._listbox.yview)
        self._scrollbar.pack(side="right", fill="y")
        self._listbox.pack(side="left", fill="both", expand=True)

        self._listbox.bind("<ButtonRelease-1>", self._on_select)
        self._listbox.bind("<Return>", self._on_select)

        self._position_popup()
        self._fill_listbox("")  # show all options on open

        # close when clicking anywhere outside
        self._popup.bind("<FocusOut>", self._schedule_close)
        self._popup.after(50, lambda: self._popup.bind(
            "<Button-1>", lambda e: None))  # absorb clicks inside

        # bind root clicks → close
        root = self.winfo_toplevel()
        self._root_click_id = root.bind("<Button-1>", self._on_root_click, "+")

    def _position_popup(self):
        if not (self._popup and self._popup.winfo_exists()):
            return
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        n = len(self._all_values)
        row_h = 22
        max_rows = 10
        h = min(max_rows, max(2, n)) * row_h + 4
        w = max(self._width, 180)
        self._popup.geometry(f"{w}x{h}+{x}+{y}")

    def _fill_listbox(self, query: str = ""):
        if not self._listbox:
            return
        q = query.strip().lower()
        self._listbox.delete(0, tk.END)
        matches = [v for v in self._all_values
                   if not q or q in v.lower()]
        for v in matches:
            self._listbox.insert(tk.END, v)

        # resize popup to fit
        if self._popup and self._popup.winfo_exists():
            row_h = 22
            max_rows = 10
            n = max(2, min(max_rows, len(matches)))
            h = n * row_h + 4
            w = max(self._width, 180)
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self._popup.geometry(f"{w}x{h}+{x}+{y}")

    def _cancel(self):
        """Close popup and restore the value that was set before typing."""
        self._var.set(self._saved_value)
        self._close_popup()

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            try:
                root = self.winfo_toplevel()
                root.unbind("<Button-1>", self._root_click_id)
            except Exception:
                pass
            self._popup.destroy()
        self._popup = None
        self._listbox = None
        self._scrollbar = None

    def _schedule_close(self, _event=None):
        if self._ignore_focus_out:
            return
        self.after(80, self._maybe_close)

    def _maybe_close(self):
        if not (self._popup and self._popup.winfo_exists()):
            return
        focused = self._popup.focus_displayof()
        if focused is None:
            self._close_popup()

    def _on_root_click(self, event):
        if not (self._popup and self._popup.winfo_exists()):
            return
        # click was inside popup → ignore
        px, py = self._popup.winfo_rootx(), self._popup.winfo_rooty()
        pw, ph = self._popup.winfo_width(), self._popup.winfo_height()
        if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
            return
        # click inside this widget → ignore
        wx, wy = self.winfo_rootx(), self.winfo_rooty()
        ww, wh = self.winfo_width(), self.winfo_height()
        if wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh:
            return
        self._cancel()

    # ── interaction ─────────────────────────────────────────────────────────

    def _on_key(self, _event=None):
        if not (self._popup and self._popup.winfo_exists()):
            self._show_popup()
        self._fill_listbox(self._var.get())

    def _on_select(self, _event=None):
        if not self._listbox:
            return
        sel = self._listbox.curselection()
        if sel:
            value = self._listbox.get(sel[0])
            self._ignore_focus_out = True
            self._just_selected = True
            self._var.set(value)
            self._close_popup()
            self._ignore_focus_out = False
            if self._command:
                self._command(value)

    def _select_first(self):
        if self._listbox and self._listbox.size() > 0:
            self._listbox.selection_clear(0, tk.END)
            self._listbox.selection_set(0)
            self._on_select()

    def _move_selection(self, delta: int):
        if not self._listbox:
            self._show_popup()
            return
        size = self._listbox.size()
        if size == 0:
            return
        sel = self._listbox.curselection()
        idx = (sel[0] + delta) if sel else (0 if delta > 0 else size - 1)
        idx = max(0, min(size - 1, idx))
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(idx)
        self._listbox.see(idx)
