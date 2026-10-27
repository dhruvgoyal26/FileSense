"""
Styling, Colors, and Theme configuration for FileSense GUI.
Modern dark navy sidebar + clean light workspace.
"""

import tkinter as tk
from tkinter import ttk

# ==========================================================
# Color Palette
# ==========================================================
COLORS = {
    # Sidebar
    "sidebar_bg": "#0f172a",        # Very dark navy slate
    "sidebar_active": "#1e293b",    # Active item bg
    "sidebar_hover": "#334155",     # Hover item bg
    "sidebar_text": "#e2e8f0",      # Light slate text
    "sidebar_subtext": "#94a3b8",   # Muted slate text
    "sidebar_border": "#1e293b",    # Subtle separator

    # Main Workspace
    "bg_main": "#f8fafc",           # Light crisp background
    "bg_card": "#ffffff",           # Pure white card background
    "bg_card_secondary": "#f1f5f9", # Secondary card/panel bg
    "border_light": "#e2e8f0",      # Border color for cards & tables
    "border_focus": "#3b82f6",      # Focus border

    # Text
    "text_primary": "#0f172a",      # Near black text
    "text_secondary": "#475569",    # Charcoal secondary text
    "text_muted": "#64748b",        # Gray muted text
    "text_light": "#ffffff",        # White text

    # Accent Colors
    "primary": "#2563eb",           # Vibrant Royal Blue
    "primary_hover": "#1d4ed8",
    "primary_light": "#dbeafe",
    "secondary": "#4f46e5",         # Indigo
    "success": "#10b981",           # Emerald Green
    "success_light": "#d1fae5",
    "warning": "#f59e0b",           # Amber Yellow
    "warning_light": "#fef3c7",
    "danger": "#ef4444",            # Crimson Rose
    "danger_light": "#fee2e2",
    "info": "#06b6d4",              # Cyan
    "purple": "#8b5cf6",            # Violet
}

# ==========================================================
# Typography
# ==========================================================
FONTS = {
    "title_xl": ("Segoe UI", 18, "bold"),
    "title_large": ("Segoe UI", 14, "bold"),
    "title_medium": ("Segoe UI", 12, "bold"),
    "body_bold": ("Segoe UI", 10, "bold"),
    "body": ("Segoe UI", 10),
    "body_small": ("Segoe UI", 9),
    "caption": ("Segoe UI", 8),
    "mono": ("Consolas", 9),
    "mono_bold": ("Consolas", 10, "bold"),
    "stat_number": ("Segoe UI", 20, "bold"),
}


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Configure modern ttk theme and component styles."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Global background
    root.configure(bg=COLORS["bg_main"])

    # TTK Frame
    style.configure("TFrame", background=COLORS["bg_main"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="solid", borderwidth=1)
    style.configure("Sidebar.TFrame", background=COLORS["sidebar_bg"])

    # TTK Label
    style.configure(
        "TLabel",
        background=COLORS["bg_main"],
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
    )
    style.configure(
        "Card.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["text_primary"],
        font=FONTS["title_medium"],
    )
    style.configure(
        "StatNum.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["primary"],
        font=FONTS["stat_number"],
    )
    style.configure(
        "StatSub.TLabel",
        background=COLORS["bg_card"],
        foreground=COLORS["text_muted"],
        font=FONTS["body_small"],
    )
    style.configure(
        "Sidebar.TLabel",
        background=COLORS["sidebar_bg"],
        foreground=COLORS["sidebar_text"],
        font=FONTS["body"],
    )
    style.configure(
        "SidebarTitle.TLabel",
        background=COLORS["sidebar_bg"],
        foreground="#ffffff",
        font=FONTS["title_medium"],
    )
    style.configure(
        "PageTitle.TLabel",
        background=COLORS["bg_main"],
        foreground=COLORS["text_primary"],
        font=FONTS["title_xl"],
    )

    # TTK Buttons
    style.configure(
        "Primary.TButton",
        font=FONTS["body_bold"],
        background=COLORS["primary"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("disabled", "#94a3b8")],
        foreground=[("disabled", "#ffffff")],
    )

    style.configure(
        "Success.TButton",
        font=FONTS["body_bold"],
        background=COLORS["success"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(10, 5),
    )
    style.map("Success.TButton", background=[("active", "#059669")])

    style.configure(
        "Danger.TButton",
        font=FONTS["body_bold"],
        background=COLORS["danger"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(10, 5),
    )
    style.map("Danger.TButton", background=[("active", "#dc2626")])

    style.configure(
        "Secondary.TButton",
        font=FONTS["body"],
        background=COLORS["bg_card_secondary"],
        foreground=COLORS["text_primary"],
        borderwidth=1,
        relief="solid",
        padding=(10, 5),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#e2e8f0")],
    )

    # TTK Treeview (Tables)
    style.configure(
        "Treeview",
        background="#ffffff",
        foreground=COLORS["text_primary"],
        fieldbackground="#ffffff",
        rowheight=26,
        font=FONTS["body_small"],
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["bg_card_secondary"],
        foreground=COLORS["text_primary"],
        font=FONTS["body_bold"],
        relief="flat",
        padding=(6, 4),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary_light"])],
        foreground=[("selected", COLORS["primary"])],
    )

    # TTK Entry & Combobox
    style.configure("TEntry", fieldbackground="#ffffff", padding=5)
    style.configure("TCombobox", padding=4)

    # TTK Progressbar
    style.configure(
        "Horizontal.TProgressbar",
        background=COLORS["primary"],
        troughcolor="#e2e8f0",
        borderwidth=0,
        thickness=8,
    )

    # TTK Notebook (Tabs)
    style.configure(
        "TNotebook",
        background=COLORS["bg_main"],
        tabmargins=[2, 5, 2, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background=COLORS["bg_card_secondary"],
        foreground=COLORS["text_secondary"],
        padding=[14, 6],
        font=FONTS["body_bold"],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#ffffff")],
        foreground=[("selected", COLORS["primary"])],
    )

    return style
