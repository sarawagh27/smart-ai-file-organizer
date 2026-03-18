"""
gui.py
------
Tkinter GUI for the Smart AI File Organizer.

Run: python gui.py

Features:
  - Browse and organise any folder
  - Preview (dry run) mode — safe, no files moved
  - Organise Now — moves files into category folders
  - Watch Mode — monitors folder in real-time, auto-organises new files
  - Recursive scanning
  - Live colour-coded activity log
  - Stats bar
"""

import logging
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, messagebox, scrolledtext

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from organizer import FileOrganizer
from utils import scan_directory
from watcher import FolderWatcher

# ── colour palette ──────────────────────────────────────────────────────────
BG          = "#1e1e2e"
SURFACE     = "#2a2a3e"
SURFACE2    = "#313147"
ACCENT      = "#7c6af7"
ACCENT_DARK = "#5a48d4"
WATCH_CLR   = "#06b6d4"   # cyan for watch mode
WATCH_DARK  = "#0891b2"
SUCCESS     = "#4ade80"
WARNING     = "#fbbf24"
ERROR       = "#f87171"
INFO        = "#93c5fd"
TEXT        = "#e2e8f0"
MUTED       = "#64748b"
WHITE       = "#ffffff"


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class SmartOrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart AI File Organizer")
        self.geometry("820x700")
        self.minsize(700, 600)
        self.configure(bg=BG)

        self._folder    = tk.StringVar()
        self._dry_run   = tk.BooleanVar(value=True)
        self._recursive = tk.BooleanVar(value=False)
        self._running   = False
        self._watching  = False
        self._watcher   = None
        self._watch_thread = None
        self._log_queue : queue.Queue = queue.Queue()

        self._build_fonts()
        self._build_header()
        self._build_folder_row()
        self._build_options_row()
        self._build_file_types_row()
        self._build_action_buttons()
        self._build_log_area()
        self._build_stats_bar()
        self._setup_logging()
        self._poll_log_queue()

        # Handle window close — stop watcher if running
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_fonts(self):
        self.font_title = font.Font(family="Segoe UI", size=16, weight="bold")
        self.font_sub   = font.Font(family="Segoe UI", size=9)
        self.font_label = font.Font(family="Segoe UI", size=10)
        self.font_btn   = font.Font(family="Segoe UI", size=10, weight="bold")
        self.font_mono  = font.Font(family="Consolas",  size=9)
        self.font_stat  = font.Font(family="Segoe UI", size=10, weight="bold")
        self.font_badge = font.Font(family="Segoe UI", size=8)

    def _build_header(self):
        hdr = tk.Frame(self, bg=SURFACE, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🗂  Smart AI File Organizer",
                 font=self.font_title, bg=SURFACE, fg=WHITE).pack()
        tk.Label(hdr,
                 text="Supports PDF · DOCX · TXT · XLSX · PPTX · CSV · Images",
                 font=self.font_sub, bg=SURFACE, fg=MUTED).pack(pady=(2, 0))

    def _build_folder_row(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=12)
        frame.pack(fill="x")
        tk.Label(frame, text="Target Folder", font=self.font_label,
                 bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w", pady=(0, 4))

        ef = tk.Frame(frame, bg=SURFACE, highlightthickness=1,
                      highlightbackground=ACCENT)
        ef.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        frame.columnconfigure(0, weight=1)

        self._folder_entry = tk.Entry(
            ef, textvariable=self._folder,
            font=self.font_label, bg=SURFACE, fg=TEXT,
            insertbackground=WHITE, bd=0, relief="flat",
        )
        self._folder_entry.pack(fill="x", padx=8, pady=6)

        tk.Button(frame, text="Browse…", font=self.font_label,
                  bg=ACCENT, fg=WHITE, activebackground=ACCENT_DARK,
                  activeforeground=WHITE, bd=0, padx=14, pady=6,
                  cursor="hand2", relief="flat",
                  command=self._browse).grid(row=1, column=1)

    def _build_options_row(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=2)
        frame.pack(fill="x")

        tk.Label(frame, text="Mode:", font=self.font_label,
                 bg=BG, fg=TEXT).pack(side="left", padx=(0, 10))

        rb_style = dict(bg=BG, fg=TEXT, activebackground=BG,
                        activeforeground=WHITE, selectcolor=SURFACE,
                        font=self.font_label, cursor="hand2", bd=0)

        tk.Radiobutton(frame, text="🔍 Preview (safe)",
                       variable=self._dry_run, value=True,
                       **rb_style).pack(side="left", padx=(0, 18))

        tk.Radiobutton(frame, text="⚡ Organise Now",
                       variable=self._dry_run, value=False,
                       **rb_style).pack(side="left", padx=(0, 30))

        tk.Checkbutton(
            frame, text="📂 Include sub-folders",
            variable=self._recursive,
            bg=BG, fg=TEXT, activebackground=BG, activeforeground=WHITE,
            selectcolor=SURFACE, font=self.font_label, cursor="hand2", bd=0,
        ).pack(side="left")

    def _build_file_types_row(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=6)
        frame.pack(fill="x")

        tk.Label(frame, text="Supports:", font=self.font_badge,
                 bg=BG, fg=MUTED).pack(side="left", padx=(0, 6))

        types = [
            ("PDF",   "#ef4444"), ("DOCX",  "#3b82f6"), ("TXT",  "#10b981"),
            ("XLSX",  "#22c55e"), ("PPTX",  "#f97316"), ("CSV",  "#06b6d4"),
            ("PNG",   "#8b5cf6"), ("JPG",   "#ec4899"),
        ]
        for label, color in types:
            badge = tk.Frame(frame, bg=color, padx=6, pady=2)
            badge.pack(side="left", padx=2)
            tk.Label(badge, text=label, font=self.font_badge,
                     bg=color, fg=WHITE).pack()

    def _build_action_buttons(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=8)
        frame.pack(fill="x")

        # Run button
        self._btn_run = tk.Button(
            frame, text="▶  Run",
            font=self.font_btn, bg=ACCENT, fg=WHITE,
            activebackground=ACCENT_DARK, activeforeground=WHITE,
            bd=0, padx=24, pady=8, cursor="hand2", relief="flat",
            command=self._run,
        )
        self._btn_run.pack(side="left", padx=(0, 10))

        # Watch Mode button
        self._btn_watch = tk.Button(
            frame, text="👁  Watch Mode",
            font=self.font_btn, bg=WATCH_CLR, fg=WHITE,
            activebackground=WATCH_DARK, activeforeground=WHITE,
            bd=0, padx=20, pady=8, cursor="hand2", relief="flat",
            command=self._toggle_watch,
        )
        self._btn_watch.pack(side="left", padx=(0, 10))

        # Clear Log button
        tk.Button(frame, text="🗑  Clear Log",
                  font=self.font_btn, bg=SURFACE2, fg=TEXT,
                  activebackground=BG, activeforeground=WHITE,
                  bd=0, padx=18, pady=8, cursor="hand2", relief="flat",
                  command=self._clear_log).pack(side="left")

        self._spinner_lbl = tk.Label(frame, text="", font=self.font_label,
                                     bg=BG, fg=WARNING)
        self._spinner_lbl.pack(side="left", padx=14)

    def _build_log_area(self):
        frame = tk.Frame(self, bg=BG, padx=20)
        frame.pack(fill="both", expand=True, pady=(0, 4))

        tk.Label(frame, text="Activity Log", font=self.font_label,
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 4))

        self._log_text = scrolledtext.ScrolledText(
            frame, font=self.font_mono, bg=SURFACE2, fg=TEXT,
            insertbackground=WHITE, bd=0, relief="flat",
            state="disabled", wrap="word", padx=10, pady=8,
        )
        self._log_text.pack(fill="both", expand=True)

        self._log_text.tag_config("INFO",    foreground=INFO)
        self._log_text.tag_config("WARNING", foreground=WARNING)
        self._log_text.tag_config("ERROR",   foreground=ERROR)
        self._log_text.tag_config("DEBUG",   foreground=MUTED)
        self._log_text.tag_config("SUCCESS", foreground=SUCCESS)
        self._log_text.tag_config("WATCH",   foreground=WATCH_CLR)
        self._log_text.tag_config("TIME",    foreground=MUTED)

    def _build_stats_bar(self):
        bar = tk.Frame(self, bg=SURFACE, pady=8)
        bar.pack(fill="x", side="bottom")

        self._stat_vars = {
            "total":  tk.StringVar(value="Files: —"),
            "moved":  tk.StringVar(value="Moved: —"),
            "dupes":  tk.StringVar(value="Duplicates: —"),
            "errors": tk.StringVar(value="Errors: —"),
            "mode":   tk.StringVar(value=""),
        }
        colours = {
            "total": TEXT, "moved": SUCCESS,
            "dupes": WARNING, "errors": ERROR, "mode": WATCH_CLR,
        }
        for key, var in self._stat_vars.items():
            tk.Label(bar, textvariable=var, font=self.font_stat,
                     bg=SURFACE, fg=colours[key], padx=16).pack(side="left")

    def _setup_logging(self):
        self._q_handler = QueueHandler(self._log_queue)
        self._q_handler.setLevel(logging.DEBUG)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()
        root_logger.addHandler(self._q_handler)

    def _poll_log_queue(self):
        try:
            while True:
                record = self._log_queue.get_nowait()
                self._write_log(record)
        except queue.Empty:
            pass
        self.after(80, self._poll_log_queue)

    def _write_log(self, record):
        self._log_text.configure(state="normal")
        formatter = logging.Formatter("%(asctime)s")
        timestamp = formatter.format(record)[:19]
        level     = record.levelname
        message   = record.getMessage()

        self._log_text.insert("end", f"{timestamp}  ", "TIME")
        self._log_text.insert("end", f"[{level:<7}]  ", level)

        # Colour logic
        if "WATCH MODE" in message or "👁" in message or "Watching" in message:
            tag = "WATCH"
        elif "Run complete" in message or "Moved '" in message or "✅" in message:
            tag = "SUCCESS"
        else:
            tag = level

        self._log_text.insert("end", message + "\n", tag)
        self._log_text.configure(state="disabled")
        self._log_text.see("end")

    # ── browse ───────────────────────────────────────────────────────────────
    def _browse(self):
        folder = filedialog.askdirectory(title="Select folder to organise")
        if folder:
            self._folder.set(folder)
            files = scan_directory(folder, recursive=self._recursive.get())
            self._append_info(
                f"📁 Selected: {folder}  →  {len(files)} supported file(s) found."
            )

    # ── run (organise once) ──────────────────────────────────────────────────
    def _run(self):
        if self._watching:
            messagebox.showwarning("Watch Mode Active",
                                   "Stop Watch Mode first before running a one-time organise.")
            return

        folder = self._folder.get().strip()
        if not folder:
            messagebox.showwarning("No folder selected", "Please select a folder first.")
            return
        if not Path(folder).is_dir():
            messagebox.showerror("Invalid folder", f"Folder not found:\n{folder}")
            return
        if self._running:
            return

        if not self._dry_run.get():
            ok = messagebox.askyesno(
                "Confirm Organise",
                f"Files in:\n  {folder}\n\nwill be MOVED into category sub-folders.\n\nContinue?"
            )
            if not ok:
                return

        self._running = True
        self._btn_run.configure(state="disabled", text="⏳  Running…")
        self._spinner_lbl.configure(text="Processing…")
        self._reset_stats()

        thread = threading.Thread(
            target=self._run_organizer,
            args=(folder, self._dry_run.get(), self._recursive.get()),
            daemon=True,
        )
        thread.start()

    def _run_organizer(self, folder, dry_run, recursive):
        try:
            organizer = FileOrganizer(
                target_dir=folder, dry_run=dry_run, recursive=recursive
            )
            stats = organizer.run()
            self.after(0, self._on_run_complete, stats, dry_run)
        except Exception as exc:
            logging.getLogger(__name__).error("Unexpected error: %s", exc)
            self.after(0, self._on_run_error, str(exc))

    def _on_run_complete(self, stats, dry_run):
        self._running = False
        self._btn_run.configure(state="normal", text="▶  Run")
        self._spinner_lbl.configure(text="")

        label = "Would move" if dry_run else "Moved"
        self._stat_vars["total"].set(f"Files: {stats['total_files']}")
        self._stat_vars["moved"].set(f"{label}: {stats['moved']}")
        self._stat_vars["dupes"].set(f"Duplicates: {stats['duplicates']}")
        self._stat_vars["errors"].set(f"Errors: {stats['errors']}")

        mode = "DRY RUN complete" if dry_run else "✅ Done"
        self._append_info(
            f"\n{mode} — {stats['moved']} file(s) {'would be moved' if dry_run else 'moved'}."
        )

        if not dry_run and stats["moved"] > 0:
            messagebox.showinfo(
                "Done!",
                f"✅ Organised {stats['moved']} file(s)!\n\n"
                f"Duplicates skipped : {stats['duplicates']}\n"
                f"Errors             : {stats['errors']}",
            )

    def _on_run_error(self, message):
        self._running = False
        self._btn_run.configure(state="normal", text="▶  Run")
        self._spinner_lbl.configure(text="")
        messagebox.showerror("Error", f"Something went wrong:\n\n{message}")

    # ── watch mode ───────────────────────────────────────────────────────────
    def _toggle_watch(self):
        if self._watching:
            self._stop_watch()
        else:
            self._start_watch()

    def _start_watch(self):
        folder = self._folder.get().strip()
        if not folder:
            messagebox.showwarning("No folder selected", "Please select a folder first.")
            return
        if not Path(folder).is_dir():
            messagebox.showerror("Invalid folder", f"Folder not found:\n{folder}")
            return
        if self._running:
            messagebox.showwarning("Busy", "Wait for the current run to finish first.")
            return

        self._watching = True
        self._btn_watch.configure(text="⛔  Stop Watching", bg=ERROR,
                                  activebackground="#dc2626")
        self._btn_run.configure(state="disabled")
        self._stat_vars["mode"].set("👁 WATCH MODE ACTIVE")
        self._spinner_lbl.configure(text="")

        self._append_watch(
            f"\n👁  Watch Mode started — monitoring: {folder}\n"
            f"   Drop files into the folder and they will be organised automatically.\n"
        )

        self._watch_thread = threading.Thread(
            target=self._run_watcher,
            args=(folder, self._recursive.get()),
            daemon=True,
        )
        self._watch_thread.start()

    def _run_watcher(self, folder, recursive):
        try:
            self._watcher = FolderWatcher(
                target_dir=folder,
                delay=2.0,
                recursive=recursive,
            )
            self._watcher.start()   # blocks until stopped
        except Exception as exc:
            logging.getLogger(__name__).error("Watcher error: %s", exc)
            self.after(0, self._on_watch_error, str(exc))

    def _stop_watch(self):
        if self._watcher and self._watcher.observer.is_alive():
            self._watcher.observer.stop()

        self._watching = False
        self._btn_watch.configure(text="👁  Watch Mode", bg=WATCH_CLR,
                                  activebackground=WATCH_DARK)
        self._btn_run.configure(state="normal")
        self._stat_vars["mode"].set("")
        self._append_watch("\n⛔  Watch Mode stopped.\n")

    def _on_watch_error(self, message):
        self._watching = False
        self._btn_watch.configure(text="👁  Watch Mode", bg=WATCH_CLR,
                                  activebackground=WATCH_DARK)
        self._btn_run.configure(state="normal")
        self._stat_vars["mode"].set("")
        messagebox.showerror("Watch Mode Error", f"Something went wrong:\n\n{message}")

    # ── helpers ──────────────────────────────────────────────────────────────
    def _append_info(self, text):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", text + "\n", "INFO")
        self._log_text.configure(state="disabled")
        self._log_text.see("end")

    def _append_watch(self, text):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", text + "\n", "WATCH")
        self._log_text.configure(state="disabled")
        self._log_text.see("end")

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _reset_stats(self):
        for k, label in [("total", "Files: …"), ("moved", "Moved: …"),
                          ("dupes", "Duplicates: …"), ("errors", "Errors: …")]:
            self._stat_vars[k].set(label)

    def _on_close(self):
        if self._watching:
            self._stop_watch()
        self.destroy()


def main():
    app = SmartOrganizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
