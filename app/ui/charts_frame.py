"""
Charts frame for FinAnalazer2.
Displays pie, bar, and line charts using matplotlib embedded in tkinter.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
import customtkinter as ctk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app import database as db

DARK_BG = '#2b2b2b'
DARK_FG = '#cccccc'
DARK_AXES = '#333333'
GRID_COLOR = '#444444'

plt.style.use('dark_background')

MONTHS_SHORT = ["Sty", "Úno", "Bře", "Dub", "Kvě", "Čvn",
                "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]


class ChartsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._current_chart = "pie"
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Controls bar ──────────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, height=52)
        ctrl.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        ctrl.grid_columnconfigure(8, weight=1)

        col = 0
        ctk.CTkLabel(ctrl, text="Rok:").grid(row=0, column=col, padx=(12, 4), pady=10)
        col += 1
        self._year_var = tk.StringVar(value="Všechny")
        self._year_cb = ctk.CTkComboBox(
            ctrl, variable=self._year_var, width=100,
            command=lambda _: self._draw_chart()
        )
        self._year_cb.grid(row=0, column=col, padx=4, pady=10)
        col += 1

        ctk.CTkLabel(ctrl, text="Měsíc:").grid(row=0, column=col, padx=(8, 4), pady=10)
        col += 1
        self._month_var = tk.StringVar(value="Všechny")
        month_values = ["Všechny"] + [f"{i:02d} – {MONTHS_SHORT[i-1]}" for i in range(1, 13)]
        self._month_cb = ctk.CTkComboBox(
            ctrl, variable=self._month_var, width=130,
            values=month_values,
            command=lambda _: self._draw_chart()
        )
        self._month_cb.grid(row=0, column=col, padx=4, pady=10)
        col += 1

        # Chart type tabs
        ctk.CTkLabel(ctrl, text="Graf:").grid(row=0, column=col, padx=(16, 4), pady=10)
        col += 1
        self._chart_type_var = tk.StringVar(value="Koláčový")
        chart_type_cb = ctk.CTkComboBox(
            ctrl, variable=self._chart_type_var, width=130,
            values=["Koláčový", "Sloupcový", "Liniový"],
            command=lambda _: self._draw_chart()
        )
        chart_type_cb.grid(row=0, column=col, padx=4, pady=10)
        col += 1

        # Toggles
        self._excl_transfers_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            ctrl, text="Bez převodů",
            variable=self._excl_transfers_var,
            command=self._draw_chart
        ).grid(row=0, column=col, padx=(16, 4), pady=10)
        col += 1

        self._incl_income_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            ctrl, text="Zahrnout příjmy",
            variable=self._incl_income_var,
            command=self._draw_chart
        ).grid(row=0, column=col, padx=4, pady=10)
        col += 1

        ctk.CTkButton(
            ctrl, text="Obnovit", width=80,
            fg_color="transparent", border_width=1,
            command=self.refresh
        ).grid(row=0, column=col, padx=(8, 12), pady=10)

        # ── Chart canvas ──────────────────────────────────────────────────────
        canvas_frame = ctk.CTkFrame(self, fg_color=DARK_BG)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(0, weight=1)

        self._fig, self._ax = plt.subplots(figsize=(10, 5.5))
        self._fig.patch.set_facecolor(DARK_BG)
        self._ax.set_facecolor(DARK_AXES)

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=canvas_frame)
        self._mpl_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # ── No-data label ─────────────────────────────────────────────────────
        self._no_data_var = tk.StringVar(value="")
        self._no_data_label = ctk.CTkLabel(
            canvas_frame, textvariable=self._no_data_var,
            font=ctk.CTkFont(size=16), text_color="gray"
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._update_year_combo()
        self._draw_chart()

    def _update_year_combo(self):
        try:
            years = db.get_available_years()
            values = ["Všechny"] + [str(y) for y in years]
            current = self._year_var.get()
            self._year_cb.configure(values=values)
            if current not in values:
                self._year_var.set("Všechny")
        except Exception:
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_year(self) -> Optional[int]:
        v = self._year_var.get()
        try:
            return int(v) if v not in ("Všechny", "") else None
        except ValueError:
            return None

    def _get_month(self) -> Optional[int]:
        v = self._month_var.get()
        if v == "Všechny" or not v:
            return None
        try:
            return int(v.split(" ")[0])
        except (ValueError, IndexError):
            return None

    def _draw_chart(self):
        chart_type = self._chart_type_var.get()
        try:
            if chart_type == "Koláčový":
                self._draw_pie()
            elif chart_type == "Sloupcový":
                self._draw_bar()
            elif chart_type == "Liniový":
                self._draw_line()
        except Exception as e:
            self._show_error(str(e))

    def _clear_axes(self):
        self._fig.clear()
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(DARK_AXES)
        self._no_data_label.place_forget()

    def _show_no_data(self, msg="Žádná data"):
        self._ax.clear()
        self._ax.set_facecolor(DARK_BG)
        self._ax.axis('off')
        self._mpl_canvas.draw()

    def _show_error(self, msg: str):
        self._ax.clear()
        self._ax.set_facecolor(DARK_BG)
        self._ax.axis('off')
        self._ax.text(0.5, 0.5, f"Chyba: {msg}", ha='center', va='center',
                      color='red', fontsize=12, transform=self._ax.transAxes)
        self._mpl_canvas.draw()

    # ── Pie Chart ─────────────────────────────────────────────────────────────

    def _draw_pie(self):
        year = self._get_year()
        month = self._get_month()
        excl_transfers = self._excl_transfers_var.get()
        expense_only = not self._incl_income_var.get()

        data = db.get_category_totals(
            year=year, month=month,
            expense_only=expense_only,
            exclude_transfers=excl_transfers
        )

        self._clear_axes()

        if not data:
            self._show_no_data("Žádná data pro vybrané období")
            return

        # Filter out zero
        data = [d for d in data if abs(d['total']) > 0.001]
        if not data:
            self._show_no_data()
            return

        labels = [d['category_name'] for d in data]
        values = [abs(d['total']) for d in data]
        colors = [d['color'] for d in data]

        total_sum = sum(values)

        # Use a layout with pie on left, legend on right
        self._fig.clear()
        gs = self._fig.add_gridspec(1, 2, width_ratios=[1.8, 1], wspace=0.1)
        ax_pie = self._fig.add_subplot(gs[0])
        ax_leg = self._fig.add_subplot(gs[1])
        ax_pie.set_facecolor(DARK_BG)
        ax_leg.set_facecolor(DARK_BG)
        ax_leg.axis('off')

        wedge_props = {'linewidth': 1, 'edgecolor': DARK_BG}
        wedges, texts, autotexts = ax_pie.pie(
            values,
            labels=None,
            colors=colors,
            autopct=lambda p: f'{p:.1f}%' if p >= 3 else '',
            startangle=90,
            wedgeprops=wedge_props,
            pctdistance=0.75,
            textprops={'color': DARK_FG, 'fontsize': 9}
        )
        for at in autotexts:
            at.set_color(DARK_BG)
            at.set_fontweight('bold')

        ax_pie.set_facecolor(DARK_BG)

        # Period title
        period = self._format_period(year, month)
        ax_pie.set_title(f"Výdaje podle kategorií – {period}",
                         color=DARK_FG, fontsize=13, pad=12)

        # Custom legend
        legend_lines = []
        for i, (label, value) in enumerate(zip(labels, values)):
            pct = value / total_sum * 100
            line = f"{label:<22}  {value:>10,.0f} Kč  ({pct:.1f}%)"
            legend_lines.append((colors[i], line))

        y_pos = 0.98
        ax_leg.text(0.02, y_pos, f"Celkem: {total_sum:,.0f} Kč",
                    transform=ax_leg.transAxes, color=DARK_FG,
                    fontsize=10, fontweight='bold', va='top')
        y_pos -= 0.06
        for color, line in legend_lines:
            ax_leg.add_patch(
                plt.Rectangle((0.02, y_pos - 0.015), 0.04, 0.03,
                               color=color, transform=ax_leg.transAxes)
            )
            ax_leg.text(0.09, y_pos, line,
                        transform=ax_leg.transAxes, color=DARK_FG,
                        fontsize=8.5, va='center', family='monospace')
            y_pos -= 0.055
            if y_pos < 0.02:
                break

        self._fig.patch.set_facecolor(DARK_BG)
        self._mpl_canvas.draw()

    # ── Bar Chart ─────────────────────────────────────────────────────────────

    def _draw_bar(self):
        year = self._get_year()
        excl_transfers = self._excl_transfers_var.get()

        data = db.get_monthly_category_totals(year=year, exclude_transfers=excl_transfers)

        self._clear_axes()

        if not data:
            self._show_no_data()
            return

        # Build matrix: months x categories
        # Find top N categories by total
        cat_totals: dict[int, float] = {}
        cat_names: dict[int, str] = {}
        cat_colors: dict[int, str] = {}
        monthly_data: dict[int, dict[int, float]] = {}  # month -> {cat_id -> total}

        for row in data:
            m = row['month']
            cid = row['category_id']
            cat_totals[cid] = cat_totals.get(cid, 0) + row['total']
            cat_names[cid] = row['category_name']
            cat_colors[cid] = row['color']
            monthly_data.setdefault(m, {})[cid] = row['total']

        # Top 8 categories
        TOP_N = 8
        top_cats = sorted(cat_totals, key=lambda c: -cat_totals[c])[:TOP_N]

        months = sorted(monthly_data.keys())
        if not months:
            self._show_no_data()
            return

        import numpy as np
        n_cats = len(top_cats)
        n_months = len(months)
        bar_width = 0.8 / max(n_cats, 1)
        x = np.arange(n_months)

        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor(DARK_AXES)
        self._fig.patch.set_facecolor(DARK_BG)

        for i, cat_id in enumerate(top_cats):
            values = [monthly_data.get(m, {}).get(cat_id, 0) for m in months]
            offset = (i - n_cats / 2 + 0.5) * bar_width
            bars = ax.bar(
                x + offset, values, bar_width * 0.9,
                label=cat_names[cat_id],
                color=cat_colors[cat_id],
                alpha=0.85
            )

        ax.set_xticks(x)
        ax.set_xticklabels(
            [MONTHS_SHORT[m - 1] if 1 <= m <= 12 else str(m) for m in months],
            color=DARK_FG
        )
        ax.tick_params(colors=DARK_FG)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f"{v:,.0f}"
        ))
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        ax.grid(axis='y', color=GRID_COLOR, alpha=0.4)

        period = f"{year}" if year else "Vše"
        ax.set_title(f"Měsíční výdaje podle kategorií – {period}",
                     color=DARK_FG, fontsize=13)
        ax.set_ylabel("Kč", color=DARK_FG)

        ax.legend(
            loc='upper right', facecolor=DARK_BG,
            labelcolor=DARK_FG, fontsize=8, ncol=2,
            edgecolor=GRID_COLOR
        )

        self._mpl_canvas.draw()

    # ── Line Chart ────────────────────────────────────────────────────────────

    def _draw_line(self):
        year = self._get_year()
        excl_transfers = self._excl_transfers_var.get()

        data = db.get_monthly_totals(year=year, exclude_transfers=excl_transfers)

        self._clear_axes()

        if not data:
            self._show_no_data()
            return

        import numpy as np
        months = [d['month'] for d in data]
        income = [d['income'] for d in data]
        expense = [abs(d['expense']) for d in data]
        balance = [i + e for i, e in zip(income, [d['expense'] for d in data])]

        x = np.arange(len(months))

        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor(DARK_AXES)
        self._fig.patch.set_facecolor(DARK_BG)

        ax.plot(x, income, 'o-', color='#2ecc71', label='Příjmy',
                linewidth=2, markersize=6)
        ax.plot(x, expense, 's-', color='#e74c3c', label='Výdaje',
                linewidth=2, markersize=6)
        ax.plot(x, balance, '^--', color='#3498db', label='Bilance',
                linewidth=2, markersize=6, alpha=0.7)
        ax.axhline(0, color=GRID_COLOR, linewidth=1, linestyle='--', alpha=0.5)

        ax.fill_between(x, 0, income, alpha=0.08, color='#2ecc71')
        ax.fill_between(x, 0, expense, alpha=0.08, color='#e74c3c')

        ax.set_xticks(x)
        ax.set_xticklabels(
            [MONTHS_SHORT[m - 1] if 1 <= m <= 12 else str(m) for m in months],
            color=DARK_FG
        )
        ax.tick_params(colors=DARK_FG)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f"{v:,.0f}"
        ))
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        ax.grid(color=GRID_COLOR, alpha=0.3)

        period = f"{year}" if year else "Vše"
        ax.set_title(f"Příjmy vs. výdaje po měsících – {period}",
                     color=DARK_FG, fontsize=13)
        ax.set_ylabel("Kč", color=DARK_FG)

        ax.legend(
            facecolor=DARK_BG, labelcolor=DARK_FG,
            fontsize=10, edgecolor=GRID_COLOR
        )

        self._mpl_canvas.draw()

    @staticmethod
    def _format_period(year: Optional[int], month: Optional[int]) -> str:
        if year and month and 1 <= month <= 12:
            return f"{MONTHS_SHORT[month - 1]} {year}"
        elif year:
            return str(year)
        return "Vše"
