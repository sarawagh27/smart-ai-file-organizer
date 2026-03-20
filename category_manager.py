"""
category_manager.py
-------------------
GUI window for managing categories and their training keywords.

Features
--------
  - View all existing categories
  - Add a new category with keywords
  - Edit keywords for an existing category
  - Delete a category
  - All changes saved instantly to config.json

Usage
-----
    from category_manager import CategoryManager
    CategoryManager(parent_window, config_path="config.json")
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import font, messagebox, scrolledtext, ttk

BG      = "#1e1e2e"
SURFACE = "#2a2a3e"
SURFACE2= "#313147"
ACCENT  = "#7c6af7"
ACCENT_D= "#5a48d4"
SUCCESS = "#4ade80"
WARNING = "#fbbf24"
ERROR   = "#f87171"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
WHITE   = "#ffffff"


class CategoryManager(tk.Toplevel):
    """
    Popup window for managing categories in config.json.
    Opens as a child of the main GUI window.
    """

    def __init__(self, parent, config_path: str):
        super().__init__(parent)
        self.title("Manage Categories")
        self.geometry("780x560")
        self.minsize(680, 480)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.config_path = Path(config_path)
        self._config     = self._load_config()

        self._font_title = font.Font(family="Segoe UI", size=13, weight="bold")
        self._font_label = font.Font(family="Segoe UI", size=10)
        self._font_btn   = font.Font(family="Segoe UI", size=9, weight="bold")
        self._font_mono  = font.Font(family="Consolas",  size=9)
        self._font_small = font.Font(family="Segoe UI", size=9)

        self._selected_cat = None  # currently selected category

        self._build_ui()
        self._refresh_list()

    # ── Config helpers ───────────────────────────────────────────────────────
    def _load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙️  Manage Categories",
                 font=self._font_title, bg=SURFACE, fg=WHITE).pack()
        tk.Label(hdr, text="Add, edit or delete categories. Changes are saved instantly to config.json.",
                 font=self._font_small, bg=SURFACE, fg=MUTED).pack(pady=(2, 0))

        # Main area — left list + right editor
        main = tk.Frame(self, bg=BG, padx=16, pady=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Left panel: category list ────────────────────────────────────────
        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(left, text="Categories", font=self._font_label,
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 6))

        list_frame = tk.Frame(left, bg=SURFACE, highlightthickness=1,
                               highlightbackground=ACCENT)
        list_frame.pack(fill="both", expand=True)

        self._listbox = tk.Listbox(
            list_frame, bg=SURFACE, fg=TEXT, selectbackground=ACCENT,
            selectforeground=WHITE, font=self._font_label,
            bd=0, relief="flat", activestyle="none",
            width=20,
        )
        self._listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        # List action buttons
        btn_row = tk.Frame(left, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        tk.Button(btn_row, text="＋ Add", font=self._font_btn,
                  bg=SUCCESS, fg="#14532d", activebackground="#22c55e",
                  bd=0, padx=10, pady=6, cursor="hand2", relief="flat",
                  command=self._add_category).pack(side="left", padx=(0, 6))

        self._btn_delete = tk.Button(btn_row, text="✕ Delete", font=self._font_btn,
                  bg=ERROR, fg="#7f1d1d", activebackground="#f87171",
                  bd=0, padx=10, pady=6, cursor="hand2", relief="flat",
                  command=self._delete_category, state="disabled")
        self._btn_delete.pack(side="left")

        # ── Right panel: keyword editor ──────────────────────────────────────
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        self._editor_title = tk.Label(right, text="Select a category to edit",
                                       font=self._font_label, bg=BG, fg=MUTED)
        self._editor_title.pack(anchor="w", pady=(0, 6))

        tk.Label(right, text="Training keywords (one sentence per line — the more descriptive the better):",
                 font=self._font_small, bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 4))

        self._editor = scrolledtext.ScrolledText(
            right, font=self._font_mono, bg=SURFACE2, fg=TEXT,
            insertbackground=WHITE, bd=0, relief="flat",
            wrap="word", padx=10, pady=8, state="disabled",
        )
        self._editor.pack(fill="both", expand=True)

        # Save button
        btn_frame = tk.Frame(right, bg=BG, pady=8)
        btn_frame.pack(fill="x")

        self._btn_save = tk.Button(btn_frame, text="💾  Save Changes",
                  font=self._font_btn, bg=ACCENT, fg=WHITE,
                  activebackground=ACCENT_D, activeforeground=WHITE,
                  bd=0, padx=18, pady=7, cursor="hand2", relief="flat",
                  command=self._save_keywords, state="disabled")
        self._btn_save.pack(side="left")

        self._save_lbl = tk.Label(btn_frame, text="", font=self._font_small,
                                   bg=BG, fg=SUCCESS)
        self._save_lbl.pack(side="left", padx=10)

        # Hint
        tk.Label(right,
                 text="💡 Tip: Use rich, keyword-dense sentences for better accuracy.\n"
                      "   Example: \"invoice payment bank account balance tax revenue profit loss\"",
                 font=self._font_small, bg=BG, fg=MUTED,
                 justify="left").pack(anchor="w", pady=(4, 0))

    # ── List management ──────────────────────────────────────────────────────
    def _refresh_list(self):
        """Reload the category listbox from config."""
        self._listbox.delete(0, "end")
        for cat in self._config.get("categories", []):
            self._listbox.insert("end", f"  {cat}")

    def _on_select(self, event=None):
        sel = self._listbox.curselection()
        if not sel:
            return

        cat = self._listbox.get(sel[0]).strip()
        self._selected_cat = cat

        # Update editor title
        self._editor_title.configure(text=f"Keywords for: {cat}", fg=TEXT)

        # Load existing keywords into editor
        keywords = self._config.get("training_data", {}).get(cat, [])
        self._editor.configure(state="normal")
        self._editor.delete("1.0", "end")
        self._editor.insert("end", "\n".join(keywords))

        # Enable buttons
        self._btn_save.configure(state="normal")
        self._btn_delete.configure(state="normal")
        self._save_lbl.configure(text="")

    # ── Add category ─────────────────────────────────────────────────────────
    def _add_category(self):
        """Open a small dialog to get the new category name."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Category")
        dialog.geometry("360x160")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="New category name:", font=self._font_label,
                 bg=BG, fg=TEXT).pack(pady=(20, 6))

        entry_frame = tk.Frame(dialog, bg=SURFACE, highlightthickness=1,
                                highlightbackground=ACCENT)
        entry_frame.pack(padx=30, fill="x")
        entry = tk.Entry(entry_frame, font=self._font_label, bg=SURFACE, fg=TEXT,
                         insertbackground=WHITE, bd=0, relief="flat")
        entry.pack(fill="x", padx=8, pady=6)
        entry.focus()

        def confirm():
            name = entry.get().strip()
            if not name:
                return
            if name in self._config.get("categories", []):
                messagebox.showwarning("Exists", f"Category '{name}' already exists.", parent=dialog)
                return

            # Add to config
            self._config.setdefault("categories", []).append(name)
            self._config.setdefault("training_data", {})[name] = [
                f"add your keywords for {name} here"
            ]
            self._save_config()
            self._refresh_list()

            # Select the new category
            idx = self._config["categories"].index(name)
            self._listbox.selection_clear(0, "end")
            self._listbox.selection_set(idx)
            self._listbox.see(idx)
            self._on_select()
            dialog.destroy()

        tk.Button(dialog, text="Add Category", font=self._font_btn,
                  bg=ACCENT, fg=WHITE, activebackground=ACCENT_D,
                  bd=0, padx=16, pady=7, cursor="hand2", relief="flat",
                  command=confirm).pack(pady=14)

        entry.bind("<Return>", lambda e: confirm())

    # ── Delete category ──────────────────────────────────────────────────────
    def _delete_category(self):
        if not self._selected_cat:
            return

        cat = self._selected_cat

        # Protect "Other" — it's the fallback
        if cat == "Other":
            messagebox.showwarning("Cannot Delete",
                                   "'Other' is the fallback category and cannot be deleted.",
                                   parent=self)
            return

        ok = messagebox.askyesno(
            "Confirm Delete",
            f"Delete category '{cat}'?\n\nFiles already organised into {cat}/ will NOT be moved back.",
            parent=self,
        )
        if not ok:
            return

        # Remove from config
        if cat in self._config.get("categories", []):
            self._config["categories"].remove(cat)
        self._config.get("training_data", {}).pop(cat, None)
        self._save_config()

        # Reset editor
        self._selected_cat = None
        self._editor.configure(state="disabled")
        self._editor.delete("1.0", "end")
        self._editor_title.configure(text="Select a category to edit", fg=MUTED)
        self._btn_save.configure(state="disabled")
        self._btn_delete.configure(state="disabled")
        self._refresh_list()

    # ── Save keywords ────────────────────────────────────────────────────────
    def _save_keywords(self):
        if not self._selected_cat:
            return

        cat  = self._selected_cat
        text = self._editor.get("1.0", "end").strip()

        # Split by newlines, filter empty lines
        keywords = [line.strip() for line in text.split("\n") if line.strip()]

        if not keywords:
            messagebox.showwarning("Empty",
                                   "Please add at least one keyword sentence.",
                                   parent=self)
            return

        self._config.setdefault("training_data", {})[cat] = keywords
        self._save_config()

        self._save_lbl.configure(text=f"✅ Saved {len(keywords)} keyword(s)")
        self.after(3000, lambda: self._save_lbl.configure(text=""))
