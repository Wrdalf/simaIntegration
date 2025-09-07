
"""
Виджет: Панель логов.
"""

import tkinter as tk
from tkinter import ttk


class LogPanelWidget:
    def __init__(self, parent, title="📝 Логи операций"):
        self.parent = parent
        self.frame = ttk.Frame(parent, style="Log.TFrame")
        self.create_widgets(title)

    def create_widgets(self, title):
        # Заголовок
        ttk.Label(
            self.frame,
            text=title,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Текстовое поле
        self.text_widget = tk.Text(
            self.frame,
            height=8,
            bg="#101010",
            fg="white",
            font=("Consolas", 14),
            relief="flat",
            bd=1,
            highlightbackground="#333",
            highlightthickness=1,
            state="disabled"
        )
        self.text_widget.pack(padx=10, pady=5, fill=tk.X)

    def log(self, message):
        """Добавляет сообщение в лог."""
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, f"• {message}\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")

    def clear(self):
        """Очищает лог."""
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.config(state="disabled")