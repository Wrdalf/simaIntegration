"""
Виджет: Список сборок.
"""

import tkinter as tk
from utils.tooltip import Tooltip


class CollectionsListWidget:
    def __init__(self, parent, on_delete_callback, on_item_click=None):
        self.parent = parent
        self.on_delete_callback = on_delete_callback
        self.on_item_click = on_item_click
        self.collections = []  # (tag, name, articles)
        self.frame = tk.Frame(parent, bg="#2d2d2d")
        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        header = tk.Label(
            self.frame,
            text="📦 Сборки",
            font=("Segoe UI", 14, "bold"),
            bg="#2d2d2d",
            fg="white",
            anchor="w"
        )
        header.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Контейнер для списка
        self.canvas = tk.Canvas(self.frame, bg="#2d2d2d", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2d2d2d")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scrollbar.pack(side="right", fill="y")

    def update_list(self):
        """Обновляет отображение списка сборок."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.collections:
            placeholder = tk.Label(
                self.scrollable_frame,
                text="Пока нет сборок",
                font=("Segoe UI", 14),
                bg="#2d2d2d",
                fg="#888"
            )
            placeholder.pack(pady=20)
            return

        for idx, (tag, name, articles) in enumerate(self.collections):
            item_frame = tk.Frame(self.scrollable_frame, bg="#333333", height=50)
            item_frame.pack(fill=tk.X, pady=4)
            item_frame.pack_propagate(False)

            # Тег (дата)
            tag_label = tk.Label(
                item_frame,
                text=f" {tag} ",
                bg="#0078D7",
                fg="white",
                font=("Segoe UI", 12, "bold"),
                padx=8,
                pady=2
            )
            tag_label.pack(side=tk.LEFT, padx=10, pady=5)

            # Название
            name_label = tk.Label(
                item_frame,
                text=name,
                bg="#333333",
                fg="white",
                font=("Segoe UI", 12)
            )
            name_label.pack(side=tk.LEFT, padx=10)

            # Количество
            count_label = tk.Label(
                item_frame,
                text=f"{len(articles)} арт.",
                bg="#333333",
                fg="#bbb",
                font=("Segoe UI", 12)
            )
            count_label.pack(side=tk.LEFT, padx=10)

            # Кнопка удаления
            delete_btn = tk.Button(
                item_frame,
                text="✕",
                bg="#dc3545",
                fg="white",
                font=("Segoe UI", 14),
                relief="flat",
                bd=0,
                width=3,
                command=lambda i=idx: self.on_delete_callback(i)
            )
            delete_btn.pack(side=tk.RIGHT, padx=10)
            delete_btn.bind("<Enter>", lambda e, b=delete_btn: b.configure(bg="#c82333"))
            delete_btn.bind("<Leave>", lambda e, b=delete_btn: b.configure(bg="#dc3545"))
            Tooltip(delete_btn, "Удалить эту сборку")

            # Клик по строке
            if self.on_item_click:
                for widget in item_frame.winfo_children():
                    widget.bind("<Button-1>", lambda e, i=idx: self.on_item_click(i))

    def add_collection(self, tag, name, articles):
        """Добавляет новую сборку."""
        self.collections.append((tag, name, articles))
        self.update_list()

    def remove_collection(self, index):
        """Удаляет сборку по индексу."""
        if 0 <= index < len(self.collections):
            del self.collections[index]
            self.update_list()

    def get_collections(self):
        """Возвращает список всех сборок."""
        return self.collections.copy()