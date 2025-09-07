"""
Глобальные настройки приложения: пути, API, стили, лимиты.
"""

# --- API ---
API_BASE_URL = "https://www.sima-land.ru/api/v5"
MAX_REQUESTS_PER_SECOND = 75
MAX_ERRORS_PER_10_SECONDS = 50
SAVE_INTERVAL = 10

# --- Пути ---
APP_NAME = "📦 Обработка артикулов"
WINDOW_SIZE = "1000x800"
MIN_WINDOW_SIZE = (800, 600)

# --- Цвета ---
COLOR_BG = "#1e1e1e"
COLOR_HEADER = "#0078D7"
COLOR_CARD = "#2d2d2d"
COLOR_TEXT = "white"
COLOR_LOG_BG = "#101010"
COLOR_BUTTON_ACCENT = "#0078D7"
COLOR_BUTTON_SUCCESS = "#28a745"
COLOR_BUTTON_WARNING = "#ffc107"
COLOR_BUTTON_DANGER = "#dc3545"

# --- Шрифты ---
FONT_LABEL = ("Segoe UI", 14)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_BUTTON = ("Segoe UI", 12, "bold")
FONT_LOG = ("Consolas", 14)