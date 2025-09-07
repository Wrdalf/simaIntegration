"""
Управление секретами приложения (API-ключи, пароли).
Загружает из .env файла.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# --- API ---
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY не найден в файле .env")

# --- Сервер (заготовка на будущее) ---
SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = int(os.getenv("SERVER_PORT", 22))
SERVER_USER = os.getenv("SERVER_USER")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")