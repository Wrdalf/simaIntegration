"""
Виджет: Поле ввода артикулов.
"""

import tkinter as tk
from tkinter import ttk


class TextInputWidget:
    def __init__(self, parent, title="📋 Введите артикулы"):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.create_widgets(title)

    def create_widgets(self, title):
        # Заголовок
        ttk.Label(
            self.frame,
            text=title,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Текстовое поле
        self.text_area = tk.Text(
            self.frame,
            height=12,
            width=40,
            bg="#101010",
            fg="white",
            insertbackground="white",
            font=("Consolas", 14),
            relief="flat",
            bd=2,
            highlightbackground="#333",
            highlightthickness=1
        )
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def get_articles(self):
        """Возвращает список артикулов из поля."""
        text = self.text_area.get("1.0", tk.END).strip()
        return [line.strip() for line in text.splitlines() if line.strip()]

    def clear(self):
        """Очищает поле ввода."""
        self.text_area.delete("1.0", tk.END)

    def insert(self, text):
        """Вставляет текст в поле."""
        self.text_area.insert("1.0", text)