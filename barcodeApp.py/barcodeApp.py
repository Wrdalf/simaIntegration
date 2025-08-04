import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# --- Настройки ---
API_BASE_URL = "https://www.sima-land.ru/api/v5"
API_KEY = "4c0859bef4a9209b57aa315bedee9b9d722607a65c432f2c448b458d74cff4a41494381ae77672df136bd3b6545ba5779a3257aa8ac683fb8e7f2ae0f87f6331"
MAX_REQUESTS_PER_SECOND = 75
MAX_ERRORS_PER_10_SECONDS = 50
SAVE_INTERVAL = 10

# --- Глобальные переменные ---
request_count = 0
error_count = 0
start_time = time.time()
error_start_time = time.time()

# --- Основное окно ---
root = tk.Tk()
root.title("📦 Обработка артикулов")
root.geometry("1000x800")
root.minsize(800, 600)
root.configure(bg="#1e1e1e")

# --- Стили ---
style = ttk.Style()
style.theme_use("clam")

style.configure("TLabel", font=("Segoe UI", 14), background="#1e1e1e", foreground="white")
style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=10)
style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), padding=15, background="#0078D7")
style.map("Accent.TButton", background=[("active", "#005a9e")])

style.configure("Success.TButton", background="#28a745", foreground="white", font=("Segoe UI", 12))
style.map("Success.TButton", background=[("active", "#208a3a")])

style.configure("Warning.TButton", background="#ffc107", foreground="black", font=("Segoe UI", 12))
style.map("Warning.TButton", background=[("active", "#e0a800")])

style.configure("Danger.TButton", background="#dc3545", foreground="white", font=("Segoe UI", 12))
style.map("Danger.TButton", background=[("active", "#c82333")])

style.configure("Card.TFrame", background="#2d2d2d", relief="flat", borderwidth=1)
style.configure("Log.TFrame", background="#101010")

# --- Всплывающие подсказки ---
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=5,
            pady=3
        )
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# --- Заголовок ---
header = tk.Frame(root, bg="#0078D7", height=80)
header.pack(fill=tk.X)
header.pack_propagate(False)

title_label = tk.Label(header, text="📦 Обработка артикулов", font=("Segoe UI", 20, "bold"), bg="#0078D7", fg="white")
title_label.pack(side=tk.LEFT, padx=20, pady=10)

# --- Основной контент ---
main_container = tk.Frame(root, bg="#1e1e1e")
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
main_container.columnconfigure(0, weight=1)
main_container.columnconfigure(1, weight=1)
main_container.rowconfigure(0, weight=1)

# --- Левая часть — ввод артикулов ---
left_frame = ttk.Frame(main_container, style="Card.TFrame")
left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), ipadx=5, ipady=5)

ttk.Label(left_frame, text="📋 Введите артикулы (по одному на строку):", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
text_area = tk.Text(
    left_frame,
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
text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

btn_frame = tk.Frame(left_frame, bg="#2d2d2d")
btn_frame.pack(pady=10, padx=10, fill=tk.X)

add_btn = ttk.Button(
    btn_frame,
    text="➕ Создать сборку",
    command=lambda: add_collection(),
    style="Success.TButton"
)
add_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
Tooltip(add_btn, "Создать сборку из введённых артикулов")

# --- Правая часть — сборки ---
right_frame = ttk.Frame(main_container, style="Card.TFrame")
right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), ipadx=5, ipady=5)

ttk.Label(right_frame, text="📦 Сборки", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

collections_frame = tk.Frame(right_frame, bg="#2d2d2d")
collections_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Структура: (tag=дата, name=название_сборки, articles)
collections = []

def update_collections():
    for widget in collections_frame.winfo_children():
        widget.destroy()

    if not collections:
        placeholder = tk.Label(collections_frame, text="Пока нет сборок", font=("Segoe UI", 14), bg="#2d2d2d", fg="#888")
        placeholder.pack(pady=20)
        return

    for idx, (tag, name, articles) in enumerate(collections):
        item_frame = tk.Frame(collections_frame, bg="#333333", height=50)
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

        # Название сборки
        name_label = tk.Label(
            item_frame,
            text=name,
            bg="#333333",
            fg="white",
            font=("Segoe UI", 12)
        )
        name_label.pack(side=tk.LEFT, padx=10)

        # Количество артикулов
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
            bg="#d41e30",
            fg="white",
            font=("Segoe UI", 14),
            relief="flat",
            bd=0,
            width=3,
            command=lambda i=idx: delete_collection(i)
        )
        delete_btn.pack(side=tk.RIGHT, padx=10)
        delete_btn.bind("<Enter>", lambda e, b=delete_btn: b.configure(bg="#c82333"))
        delete_btn.bind("<Leave>", lambda e, b=delete_btn: b.configure(bg="#dc3545"))
        Tooltip(delete_btn, "Удалить эту сборку")

def delete_collection(index):
    if 0 <= index < len(collections):
        name = collections[index][1]
        collections.pop(index)
        update_collections()
        log_action(f"🗑️ Удалена сборка: {name}")

def log_action(message):
    log_text.config(state="normal")
    log_text.insert(tk.END, f"• {message}\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")
    root.update()

# --- Настройка API ---
def open_api_window():
    api_window = tk.Toplevel(root)
    api_window.title("🔐 API-токен")
    api_window.geometry("400x160")
    api_window.resizable(False, False)
    api_window.configure(bg="#1e1e1e")
    api_window.transient(root)
    api_window.grab_set()

    ttk.Label(api_window, text="API-токен:", font=("Segoe UI", 12)).pack(pady=15)
    api_entry = ttk.Entry(api_window, width=40, show="•", font=("Consolas", 12))
    api_entry.insert(0, API_KEY)
    api_entry.pack(pady=5)

    def save_token():
        global API_KEY
        new_token = api_entry.get().strip()
        if new_token:
            API_KEY = new_token
            log_action("🔑 API-токен обновлён")
            api_window.destroy()
        else:
            messagebox.showwarning("Ошибка", "Токен не может быть пустым!")

    ttk.Button(api_window, text="💾 Сохранить", command=save_token, style="Success.TButton").pack(pady=15)
    Tooltip(ttk.Button, "Сохранить API-ключ")

# --- Добавление сборки ---
def add_collection():
    articles_text = text_area.get("1.0", tk.END).strip()
    if not articles_text:
        messagebox.showwarning("⚠️ Внимание", "Введите хотя бы один артикул!")
        return

    articles = [line.strip() for line in articles_text.splitlines() if line.strip()]

    tag_window = tk.Toplevel(root)
    tag_window.title("➕ Новая сборка")
    tag_window.geometry("300x150")
    tag_window.resizable(False, False)
    tag_window.configure(bg="#1e1e1e")
    tag_window.transient(root)
    tag_window.grab_set()

    ttk.Label(tag_window, text="Название сборки (до 10 символов):", font=("Segoe UI", 12)).pack(pady=10)
    name_entry = ttk.Entry(tag_window, width=20, font=("Segoe UI", 12))
    name_entry.pack(pady=5)

    def save_tag():
        name = name_entry.get().strip()[:10]
        if not name:
            messagebox.showwarning("Ошибка", "Введите название сборки!")
            return

        tag = datetime.now().strftime("%d.%m.%y")  # Формат: 31.07.25
        collections.append((tag, name, articles))
        update_collections()
        text_area.delete("1.0", tk.END)  # ✅ Очистка поля после добавления
        log_action(f"✅ Сборка '{name}' добавлена ({len(articles)} арт.)")
        tag_window.destroy()

    create_btn = ttk.Button(tag_window, text="Создать сборку", command=save_tag, style="Success.TButton")
    create_btn.pack(pady=10)
    Tooltip(create_btn, "Добавить эту группу артикулов как сборку")

# --- Нижняя панель ---
bottom_container = tk.Frame(root, bg="#1e1e1e")
bottom_container.pack(fill=tk.X, padx=20, pady=(0, 10))

action_frame = tk.Frame(bottom_container, bg="#1e1e1e")
action_frame.pack(fill=tk.X, pady=(0, 10))

btn_open = ttk.Button(
    action_frame,
    text="📂 Открыть выгрузку",
    command=lambda: open_input_file(),
    style="Accent.TButton"
)
btn_open.pack(side=tk.LEFT, padx=5)
Tooltip(btn_open, "Загрузить артикулы из файла")

btn_dir = ttk.Button(
    action_frame,
    text="📍 Путь сохранения",
    command=lambda: select_output_dir(),
    style="Accent.TButton"
)
btn_dir.pack(side=tk.LEFT, padx=5)
Tooltip(btn_dir, "Выбрать папку для сохранения")

btn_api = ttk.Button(
    action_frame,
    text="🔑 API-токен",
    command=open_api_window,
    style="Accent.TButton"
)
btn_api.pack(side=tk.LEFT, padx=5)
Tooltip(btn_api, "Изменить API-ключ")

btn_download = ttk.Button(
    action_frame,
    text="📤 Загрузить шк",
    command=lambda: start_download(),
    style="Warning.TButton"
)
btn_download.pack(side=tk.RIGHT, padx=5)
Tooltip(btn_download, "Загрузить штрихкоды для всех артикулов")

# --- Логи ---
log_container = ttk.Frame(root, style="Log.TFrame")
log_container.pack(fill=tk.X, padx=20, pady=(0, 20))

ttk.Label(log_container, text="📝 Логи операций:", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

log_text = tk.Text(
    log_container,
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
log_text.pack(padx=10, pady=5, fill=tk.X)

# --- Пути по умолчанию ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Папка с самим скриптом
current_output_dir = BASE_DIR  # Сохраняем в simaIntegration/

# --- Функции ---
def open_input_file():
    path = filedialog.askopenfilename(title="Выберите файл с артикулами", filetypes=[("Text files", "*.txt")])
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", content)
            log_action(f"📄 Загружен файл: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")

def select_output_dir():
    global current_output_dir
    path = filedialog.askdirectory(title="Выберите папку для сохранения")
    if path:
        current_output_dir = path
        log_action(f"📁 Путь сохранения: {path}")

def get_item_data(sid):
    global request_count, error_count, start_time, error_start_time
    url = f"{API_BASE_URL}/item/{sid}?by_sid=true"
    headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
    current_time = time.time()

    if request_count >= MAX_REQUESTS_PER_SECOND:
        elapsed = current_time - start_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        request_count = 0
        start_time = time.time()

    if error_count >= MAX_ERRORS_PER_10_SECONDS - 5:
        if current_time - error_start_time < 10.0:
            sleep_time = 10.0 - (current_time - error_start_time)
            log_action(f"⏸️ Ограничение ошибок: ждём {sleep_time:.2f} сек...")
            time.sleep(sleep_time)
        error_count = 0
        error_start_time = time.time()

    try:
        response = requests.get(url, headers=headers, timeout=3)
        request_count += 1
        if response.status_code == 200:
            return response.json()
        else:
            error_count += 1
            if error_count == 1:
                error_start_time = time.time()
            log_action(f"❌ Ошибка {response.status_code} для {sid}")
            return None
    except Exception as e:
        error_count += 1
        if error_count == 1:
            error_start_time = time.time()
        log_action(f"⚠️ Ошибка запроса {sid}: {str(e)}")
        return None

def start_download():
    # Все артикулы: из сборок + из текстового поля
    all_articles = []

    # Из сборок
    for _, name, articles in collections:
        all_articles.extend(articles)

    # Из текстового поля
    extra_articles = [line.strip() for line in text_area.get("1.0", tk.END).strip().splitlines() if line.strip()]
    all_articles.extend(extra_articles)

    if not all_articles:
        messagebox.showwarning("⚠️", "Нет артикулов для загрузки!")
        return

    # Убираем дубли
    all_articles = list(dict.fromkeys(all_articles))  # Сохраняет порядок

    log_action(f"🚀 Начинаем загрузку штрихкодов для {len(all_articles)} артикулов...")

    input_path = os.path.join(current_output_dir, "input.txt")
    output_path = os.path.join(current_output_dir, "output.txt")

    try:
        os.makedirs(current_output_dir, exist_ok=True)
        with open(input_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_articles))
        log_action(f"📄 input.txt сохранён ({len(all_articles)} арт.)")

        buffer = []
        processed = 0

        for sid in all_articles:
            item_data = get_item_data(sid)
            if item_data:  # ✅ Исправлено: полное условие
                min_qty = str(item_data.get("minimum_order_quantity", "1"))
                name = item_data.get("name", "Не указано")
                barcodes = item_data.get("barcodes", [])
                line = f"{min_qty}|{sid}|{name}|{'|'.join(barcodes) if barcodes else 'Нет штрихкодов'}\n"
                buffer.append(line)
                processed += 1

                if processed % SAVE_INTERVAL == 0:
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.writelines(buffer)
                    buffer.clear()
                    log_action(f"✅ Сохранено {processed} артикулов")

        if buffer:
            with open(output_path, "a", encoding="utf-8") as f:
                f.writelines(buffer)
            log_action(f"✅ Финальные данные сохранены")

        log_action("✅ Загрузка завершена! Генерируем YML...")
        create_yml_from_last_output(all_articles)

    except Exception as e:
        log_action(f"❌ Ошибка: {str(e)}")

def create_yml_from_last_output(all_articles):
    input_path = os.path.join(current_output_dir, "output.txt")
    yml_path = os.path.join(current_output_dir, "output.yml")

    # Маппинг: sid → min_qty, name, barcodes
    item_data_map = {}
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) < 4:
                    continue
                min_qty, sid, name = parts[0], parts[1], parts[2]
                barcodes = parts[3:] if parts[3] != "Нет штрихкодов" else []
                item_data_map[sid] = {
                    "min_qty": min_qty,
                    "name": name,
                    "barcodes": barcodes
                }
    except Exception as e:
        log_action(f"❌ Ошибка чтения output.txt: {str(e)}")
        return

    root_elem = ET.Element("yml_catalog", date=datetime.utcnow().isoformat() + "+00:00")
    shop = ET.SubElement(root_elem, "shop")
    offers = ET.SubElement(shop, "offers")

    for sid in all_articles:
        if sid not in item_data_map:
            continue
        data = item_data_map[sid]
        offer = ET.SubElement(offers, "offer", id=sid)
        ET.SubElement(offer, "name").text = data["name"]

        # Добавляем теги для каждой сборки, в которой есть этот артикул
        for tag, name, articles in collections:
            if sid in articles:
                # Тег с названием (жёлтый)
                oshiptag_name = ET.SubElement(offer, "oshiptag")
                oshiptag_name.set("color", "yellow")
                oshiptag_name.text = name

                # Тег с датой (синий) — раскомментируй, если нужен
                oshiptag_date = ET.SubElement(offer, "oshiptag")
                oshiptag_date.set("color", "blue")
                oshiptag_date.text = tag  # например: 31.07.25

        # Всегда добавляем min_qty > 1 (зелёный)
        try:
            min_qty_int = int(data["min_qty"])
            if min_qty_int > 1:
                oshiptag = ET.SubElement(offer, "oshiptag")
                oshiptag.set("color", "green")
                oshiptag.text = str(min_qty_int)[:10]
        except ValueError:
            pass

        # Штрихкоды
        for barcode in data["barcodes"]:
            ET.SubElement(offer, "barcode").text = barcode

    tree = ET.ElementTree(root_elem)
    ET.indent(tree, space="  ")
    tree.write(yml_path, encoding="utf-8", xml_declaration=True)
    log_action(f"✅ YML сохранён: {yml_path}")

# --- Инициализация ---
update_collections()

# --- Запуск ---
root.mainloop()