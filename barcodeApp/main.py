"""
Точка входа в приложение.
Запускает главное окно и запускает цикл Tkinter.
"""

import tkinter as tk
from ui.main_window import MainWindow


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()