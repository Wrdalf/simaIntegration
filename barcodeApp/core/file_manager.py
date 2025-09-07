"""
Вспомогательные функции.
"""

import os
from datetime import datetime


def get_data_dir():
    """Возвращает путь к папке data в корне проекта."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(current_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_current_date_tag():
    """Возвращает текущую дату в формате ДД.ММ.ГГ"""
    return datetime.now().strftime("%d.%m.%y")