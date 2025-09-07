import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from dotenv import load_dotenv
import pyperclip

# --- Загрузка .env ---
if not os.path.exists(".env"):
    with open(".env", "w") as f:
        f.write("API_KEY=ваш_токен")
    messagebox.showinfo("Настройка", "Создан файл .env. Введите API-ключ и перезапустите.")
    exit()

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY or API_KEY == "ваш_токен":
    messagebox.showerror("Ошибка", "Заполните API_KEY в файле .env")
    exit()

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

ttk.Label(left_frame, text="📋 Введите артикулы:", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
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

ttk.Label(right_frame, text="📦 Сборки", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

collections_frame = tk.Frame(right_frame, bg="#2d2d2d")
collections_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

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

        name_label = tk.Label(
            item_frame,
            text=name,
            bg="#333333",
            fg="white",
            font=("Segoe UI", 12)
        )
        name_label.pack(side=tk.LEFT, padx=10)

        count_label = tk.Label(
            item_frame,
            text=f"{len(articles)} арт.",
            bg="#333333",
            fg="#bbb",
            font=("Segoe UI", 12)
        )
        count_label.pack(side=tk.LEFT, padx=10)

        delete_btn = tk.Button(
            item_frame,
            text="✕",
            bg="#dc3545",
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

    ttk.Label(api_window, text="API-токен (не сохраняется в коде):", font=("Segoe UI", 12)).pack(pady=10)
    ttk.Label(api_window, text="Хранится в .env — не виден в GitHub", foreground="#bbb", font=("Segoe UI", 10)).pack()

    def open_env():
        os.system("notepad .env")  # Для Windows
        messagebox.showinfo("Готово", "Отредактируйте .env и перезапустите приложение")

    ttk.Button(api_window, text="✏️ Открыть .env", command=open_env, style="Accent.TButton").pack(pady=20)

# --- Добавление сборки ---
def add_collection():
    articles_text = text_area.get("1.0", tk.END).strip()
    if not articles_text:
        messagebox.showwarning("⚠️", "Введите артикулы!")
        return
    articles = [line.strip() for line in articles_text.splitlines() if line.strip()]
    tag_window = tk.Toplevel(root)
    tag_window.title("➕ Новая сборка")
    tag_window.geometry("300x150")
    tag_window.resizable(False, False)
    tag_window.configure(bg="#1e1e1e")
    tag_window.transient(root)
    tag_window.grab_set()
    ttk.Label(tag_window, text="Название сборки (до 10 симв.):", font=("Segoe UI", 12)).pack(pady=10)
    name_entry = ttk.Entry(tag_window, width=20, font=("Segoe UI", 12))
    name_entry.pack(pady=5)
    def save_tag():
        name = name_entry.get().strip()[:10]
        if not name:
            messagebox.showwarning("Ошибка", "Введите название!")
            return
        tag = datetime.now().strftime("%d.%m.%y")
        collections.append((tag, name, articles))
        update_collections()
        text_area.delete("1.0", tk.END)
        log_action(f"✅ Сборка '{name}' добавлена ({len(articles)} арт.)")
        tag_window.destroy()
    ttk.Button(tag_window, text="Создать сборку", command=save_tag, style="Success.TButton").pack(pady=10)

# --- Нижняя панель ---
bottom_container = tk.Frame(root, bg="#1e1e1e")
bottom_container.pack(fill=tk.X, padx=20, pady=(0, 10))

action_frame = tk.Frame(bottom_container, bg="#1e1e1e")
action_frame.pack(fill=tk.X, pady=(0, 10))

ttk.Button(
    action_frame,
    text="📂 Открыть выгрузку",
    command=lambda: open_input_file(),
    style="Accent.TButton"
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    action_frame,
    text="📍 Путь сохранения",
    command=lambda: select_output_dir(),
    style="Accent.TButton"
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    action_frame,
    text="🔑 API-токен",
    command=open_api_window,
    style="Accent.TButton"
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    action_frame,
    text="📤 Загрузить шк",
    command=lambda: start_download(),
    style="Warning.TButton"
).pack(side=tk.RIGHT, padx=5)

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

# --- Пути ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

current_output_dir = DATA_DIR  # input.txt и output.txt → в data/
yml_output_path = DATA_DIR  # По умолчанию

# --- Функции ---
def open_input_file():
    path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", f.read())
            log_action(f"📄 Загружен: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Чтение: {e}")

def select_output_dir():
    global yml_output_path
    path = filedialog.askdirectory(initialdir=DATA_DIR, title="Где сохранить output.yml?")
    if path:
        yml_output_path = path
        log_action(f"📁 Путь для output.yml: {path}")

def get_item_data(sid):
    global request_count, error_count, start_time, error_start_time
    url = f"https://www.sima-land.ru/api/v5/item/{sid}?by_sid=true"
    headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
    current_time = time.time()
    if request_count >= 75:
        elapsed = current_time - start_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        request_count = 0
        start_time = time.time()
    if error_count >= 45:
        if current_time - error_start_time < 10.0:
            time.sleep(10.0 - (current_time - error_start_time))
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
        log_action(f"⚠️ Ошибка {sid}: {str(e)}")
        return None

def start_download():
    all_articles = [line.strip() for line in text_area.get("1.0", tk.END).strip().splitlines() if line.strip()]
    for _, _, arts in collections:
        all_articles.extend(arts)
    all_articles = list(dict.fromkeys(all_articles))
    if not all_articles:
        messagebox.showwarning("⚠️", "Нет артикулов!")
        return

    log_action(f"🚀 Загрузка для {len(all_articles)} арт...")

    input_path = os.path.join(DATA_DIR, "input.txt")
    output_path = os.path.join(DATA_DIR, "output.txt")

    try:
        with open(input_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_articles))
        log_action("📄 input.txt сохранён")

        buffer = []
        for sid in all_articles:
            item_data = get_item_data(sid)
            if item_data:
                min_qty = str(item_data.get("minimum_order_quantity", "1"))
                name = item_data.get("name", "Не указано")
                barcodes = item_data.get("barcodes", [])
                line = f"{min_qty}|{sid}|{name}|{'|'.join(barcodes) if barcodes else 'Нет штрихкодов'}\n"
                buffer.append(line)

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(buffer)
        log_action("✅ output.txt сохранён")

        create_yml_from_last_output(all_articles)

    except Exception as e:
        log_action(f"❌ Ошибка: {str(e)}")

def create_yml_from_last_output(all_articles):
    input_path = os.path.join(DATA_DIR, "output.txt")
    yml_path = os.path.join(yml_output_path, "output.yml")

    item_data_map = {}
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    item_data_map[parts[1]] = {
                        "min_qty": parts[0],
                        "name": parts[2],
                        "barcodes": parts[3:] if parts[3] != "Нет штрихкодов" else []
                    }
    except Exception as e:
        log_action(f"❌ Чтение output.txt: {str(e)}")
        return

    root_elem = ET.Element("yml_catalog", date=datetime.utcnow().isoformat() + "+00:00")
    shop = ET.SubElement(root_elem, "shop")
    offers = ET.SubElement(shop, "offers")
    current_date_tag = datetime.now().strftime("%d.%m.%y")

    for sid in all_articles:
        if sid not in item_data_map:
            continue
        data = item_data_map[sid]
        offer = ET.SubElement(offers, "offer", id=sid)
        ET.SubElement(offer, "name").text = data["name"]

        for tag, name, articles in collections:
            if sid in articles:
                t = ET.SubElement(offer, "oshiptag")
                t.set("color", "yellow")
                t.text = name
                t = ET.SubElement(offer, "oshiptag")
                t.set("color", "blue")
                t.text = tag

        try:
            min_qty_int = int(data["min_qty"])
            if min_qty_int > 1:
                t = ET.SubElement(offer, "oshiptag")
                t.set("color", "green")
                t.text = str(min_qty_int)[:10]
        except ValueError:
            pass

        for barcode in data["barcodes"]:
            ET.SubElement(offer, "barcode").text = barcode

    tree = ET.ElementTree(root_elem)
    ET.indent(tree, space="  ")
    tree.write(yml_path, encoding="utf-8", xml_declaration=True)
    log_action(f"✅ YML сохранён: {yml_path}")

    # ✅ Окно с действиями после создания
    show_post_save_window(yml_path)

def show_post_save_window(yml_path):
    win = tk.Toplevel(root)
    win.title("✅ Файл готов")
    win.geometry("400x200")
    win.resizable(False, False)
    win.configure(bg="#1e1e1e")
    win.transient(root)
    win.grab_set()

    ttk.Label(win, text="output.yml создан!", font=("Segoe UI", 16, "bold")).pack(pady=20)

    with open(yml_path, "r", encoding="utf-8") as f:
        content = f.read()

    ttk.Button(
        win,
        text="📋 Скопировать в буфер",
        command=lambda: [pyperclip.copy(content), messagebox.showinfo("Готово", "Скопировано в буфер!"), win.destroy()],
        style="Success.TButton"
    ).pack(pady=5)

    ttk.Button(
        win,
        text="💾 Сохранить как .txt",
        command=lambda: save_as_txt(content),
        style="Accent.TButton"
    ).pack(pady=5)

def save_as_txt(content):
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        title="Сохранить как .txt"
    )
    if path:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Готово", f"Файл сохранён: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

# --- Инициализация ---
update_collections()

# --- Запуск ---
root.mainloop()