"""
Клиент для работы с API Сималенда.
"""

import requests
import time
from config.settings import API_BASE_URL, MAX_REQUESTS_PER_SECOND, MAX_ERRORS_PER_10_SECONDS
from config.secrets import API_KEY


class APIClient:
    def __init__(self):
        self.headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.error_start_time = time.time()

    def _throttle(self):
        """Ограничение запросов: 75 в секунду."""
        current_time = time.time()
        if self.request_count >= MAX_REQUESTS_PER_SECOND:
            elapsed = current_time - self.start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            self.request_count = 0
            self.start_time = time.time()

    def _error_limit(self):
        """Ограничение ошибок: не более 50 за 10 секунд."""
        current_time = time.time()
        if self.error_count >= MAX_ERRORS_PER_10_SECONDS - 5:
            if current_time - self.error_start_time < 10.0:
                sleep_time = 10.0 - (current_time - self.error_start_time)
                time.sleep(sleep_time)
            self.error_count = 0
            self.error_start_time = time.time()

    def get_item_data(self, sid):
        """Получает данные по артикулу."""
        self._throttle()
        self._error_limit()

        url = f"{API_BASE_URL}/item/{sid}?by_sid=true"
        try:
            response = requests.get(url, headers=self.headers, timeout=3)
            self.request_count += 1
            if response.status_code == 200:
                return response.json()
            else:
                self.error_count += 1
                if self.error_count == 1:
                    self.error_start_time = time.time()
                return None
        except Exception as e:
            self.error_count += 1
            if self.error_count == 1:
                self.error_start_time = time.time()
            return None