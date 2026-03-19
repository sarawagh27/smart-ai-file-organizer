"""
stats.py
--------
Statistics Dashboard for the Smart AI File Organizer.

Parses organizer.log to build run history and category breakdowns,
then renders charts using matplotlib embedded in a Tkinter window.

Charts
------
  1. Pie chart    — all-time files by category
  2. Bar chart    — files organised per run (history)
  3. Summary row  — total files, runs, most active category

Usage
-----
    from stats import StatsDashboard
    dashboard = StatsDashboard(log_path="D:/Downloads/organizer.log")
    dashboard.show()   # opens a Tkinter window
"""

import re
import tkinter as tk
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tkinter import font, messagebox
from typing import Dict, List, Tuple

# ── Log parsing ──────────────────────────────────────────────────────────────

# Matches: 2026-03-18 10:22:01 | INFO  | utils | Moved 'file.pdf' → '/path/Finance/file.pdf'
MOVE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Moved '(.+?)' → '(.+?)'"
)

# Matches run complete lines
RUN_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Run complete.*Moved: (\d+)"
)


def parse_log(log_path: str) -> Tuple[Dict[str, int], List[Tuple[str, int]]]:
    """
    Parse organizer.log and return:
      category_totals : dict  {category: total_files_moved}
      run_history     : list  [(date_str, files_moved), ...]
    """
    category_totals: Dict[str, int] = defaultdict(int)
    run_history:     List[Tuple[str, int]] = []

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Count moves by category
                m = MOVE_RE.search(line)
                if m:
                    dest = m.group(3)
                    # Extract category from path (second-to-last part)
                    parts = Path(dest).parts
                    if len(parts) >= 2:
                        category = parts[-2]
                        category_totals[category] += 1

                # Track run history
                r = RUN_RE.search(line)
                if r:
                    dt_str = r.group(1)[:10]  # just the date
                    moved  = int(r.group(2))
                    run_history.append((dt_str, moved))

    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Log parse error: {e}")

    return dict(category_totals), run_history


# ── Dashboard window ─────────────────────────────────────────────────────────

class StatsDashboard(tk.Toplevel):
    """
    Tkinter window showing statistics charts.
    Opens as a child of the main GUI window.
    """

    BG      = "#1e1e2e"
    SURFACE = "#2a2a3e"
    TEXT    = "#e2e8f0"
    MUTED   = "#64748b"
    ACCENT  = "#7c6af7"

    # Category colours (matches badge colours in main GUI)
    CAT_COLORS = {
        "Finance":  "#ef4444",
        "Resume":   "#3b82f6",
        "AI":       "#10b981",
        "Research": "#f97316",
        "Personal": "#8b5cf6",
        "Legal":    "#ec4899",
        "Medical":  "#06b6d4",
        "Other":    "#64748b",
    }

    def __init__(self, parent, log_path: str):
        super().__init__(parent)
        self.title("Statistics Dashboard")
        self.geometry("860x620")
        self.minsize(720, 500)
        self.configure(bg=self.BG)
        self.resizable(True, True)

        self.log_path = log_path
        self._font_title = font.Font(family="Segoe UI", size=14, weight="bold")
        self._font_label = font.Font(family="Segoe UI", size=10)
        self._font_big   = font.Font(family="Segoe UI", size=22, weight="bold")
        self._font_small = font.Font(family="Segoe UI", size=9)

        self._build_ui()
        self._load_and_render()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.SURFACE, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📊  Statistics Dashboard",
                 font=self._font_title, bg=self.SURFACE, fg="#ffffff").pack()
        tk.Label(hdr, text=f"Log: {self.log_path}",
                 font=self._font_small, bg=self.SURFACE, fg=self.MUTED).pack()

        # Summary row (3 stat cards)
        self._summary_frame = tk.Frame(self, bg=self.BG, padx=20, pady=12)
        self._summary_frame.pack(fill="x")

        self._stat_cards = {}
        for key, label in [("total", "Total Files Organised"),
                            ("runs",  "Total Runs"),
                            ("top",   "Most Active Category")]:
            card = tk.Frame(self._summary_frame, bg=self.SURFACE,
                            padx=20, pady=14)
            card.pack(side="left", expand=True, fill="x", padx=6)
            val_lbl = tk.Label(card, text="—", font=self._font_big,
                               bg=self.SURFACE, fg=self.ACCENT)
            val_lbl.pack()
            tk.Label(card, text=label, font=self._font_small,
                     bg=self.SURFACE, fg=self.MUTED).pack()
            self._stat_cards[key] = val_lbl

        # Charts area (matplotlib embedded)
        self._chart_frame = tk.Frame(self, bg=self.BG)
        self._chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Refresh button
        tk.Button(self, text="🔄  Refresh",
                  font=self._font_label, bg=self.ACCENT, fg="#fff",
                  activebackground="#5a48d4", activeforeground="#fff",
                  bd=0, padx=16, pady=6, cursor="hand2", relief="flat",
                  command=self._load_and_render).pack(pady=(0, 14))

    def _load_and_render(self):
        """Parse log and redraw all charts."""
        category_totals, run_history = parse_log(self.log_path)

        # Update summary cards
        total = sum(category_totals.values())
        runs  = len(run_history)
        top   = max(category_totals, key=category_totals.get) if category_totals else "—"

        self._stat_cards["total"].configure(text=str(total))
        self._stat_cards["runs"].configure(text=str(runs))
        self._stat_cards["top"].configure(text=top)

        if not category_totals:
            self._show_empty()
            return

        # Clear previous charts
        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        self._draw_charts(category_totals, run_history)

    def _show_empty(self):
        for widget in self._chart_frame.winfo_children():
            widget.destroy()
        tk.Label(
            self._chart_frame,
            text="No data yet.\nRun the organiser on a folder first.",
            font=self._font_label, bg=self.BG, fg=self.MUTED,
            justify="center",
        ).pack(expand=True)

    def _draw_charts(self, category_totals: Dict, run_history: List):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Dark style
            plt.rcParams.update({
                "figure.facecolor":  self.BG,
                "axes.facecolor":    self.SURFACE,
                "axes.edgecolor":    "#3a3a5e",
                "axes.labelcolor":   self.TEXT,
                "text.color":        self.TEXT,
                "xtick.color":       self.MUTED,
                "ytick.color":       self.MUTED,
                "grid.color":        "#2a2a3e",
                "font.family":       "DejaVu Sans",
                "font.size":         9,
            })

            has_history = len(run_history) > 0

            if has_history:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2),
                                                facecolor=self.BG)
            else:
                fig, ax1 = plt.subplots(1, 1, figsize=(5, 4.2),
                                        facecolor=self.BG)

            # ── Pie chart ────────────────────────────────────────────────────
            labels = list(category_totals.keys())
            sizes  = list(category_totals.values())
            colors = [self.CAT_COLORS.get(l, "#64748b") for l in labels]

            wedges, texts, autotexts = ax1.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
                startangle=140,
                pctdistance=0.82,
                wedgeprops=dict(width=0.6, edgecolor=self.BG, linewidth=2),
            )
            for t in texts:
                t.set_color(self.TEXT)
                t.set_fontsize(8)
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_fontsize(7)
                at.set_fontweight("bold")

            ax1.set_title("Files by Category", color=self.TEXT,
                          fontsize=10, pad=12)

            # ── Bar chart (run history) ──────────────────────────────────────
            if has_history:
                dates  = [r[0] for r in run_history[-10:]]  # last 10 runs
                counts = [r[1] for r in run_history[-10:]]

                bars = ax2.bar(range(len(dates)), counts,
                               color=self.ACCENT, alpha=0.85,
                               edgecolor=self.BG, linewidth=1.2)

                # Value labels on bars
                for bar, count in zip(bars, counts):
                    if count > 0:
                        ax2.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.1,
                            str(count),
                            ha="center", va="bottom",
                            color=self.TEXT, fontsize=8,
                        )

                ax2.set_xticks(range(len(dates)))
                ax2.set_xticklabels(dates, rotation=30, ha="right", fontsize=7)
                ax2.set_ylabel("Files moved", color=self.MUTED, fontsize=8)
                ax2.set_title("Files per Run (last 10)", color=self.TEXT,
                              fontsize=10, pad=12)
                ax2.yaxis.grid(True, alpha=0.3)
                ax2.set_axisbelow(True)

            fig.tight_layout(pad=2.0)

            # Embed in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

        except ImportError:
            tk.Label(
                self._chart_frame,
                text="matplotlib not installed.\nRun: pip install matplotlib",
                font=self._font_label, bg=self.BG, fg=self.MUTED,
                justify="center",
            ).pack(expand=True)
        except Exception as e:
            tk.Label(
                self._chart_frame,
                text=f"Chart error: {e}",
                font=self._font_label, bg=self.BG, fg="#f87171",
                justify="center",
            ).pack(expand=True)
