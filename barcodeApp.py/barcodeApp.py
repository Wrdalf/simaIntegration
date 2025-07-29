import tkinter as tk
from tkinter import messagebox
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# Настройки
API_BASE_URL = "https://www.sima-land.ru/api/v5"
API_KEY = ""
INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.txt"
YML_OUTPUT_FILE = "output.yml"
MAX_REQUESTS_PER_SECOND = 75
MAX_ERRORS_PER_10_SECONDS = 50
SAVE_INTERVAL = 100

# Создание директории, если не существует
os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)

headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}

# Переменные для отслеживания
request_count = 0
error_count = 0
start_time = time.time()
error_start_time = time.time()

def read_articles(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]

def get_item_data(sid):
    global request_count, error_count, start_time, error_start_time
    url = f"{API_BASE_URL}/item/{sid}?by_sid=true"
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
            print(f"Приближаемся к лимиту ошибок, ждём {sleep_time:.2f} секунд...")
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
            print(f"Ошибка для SID {sid}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        error_count += 1
        if error_count == 1:
            error_start_time = time.time()
        print(f"Ошибка запроса для SID {sid}: {e}")
        return None

def process_articles(articles, status_label):
    processed_count = 0
    buffer = []
    status_label.config(text="Обработка артикулов...")
    root.update()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        for sid in articles:
            item_data = get_item_data(sid)
            if item_data:
                minimum_order_quantity = item_data.get("minimum_order_quantity", "1")
                name = item_data.get("name", "Не указано")
                barcodes = item_data.get("barcodes", [])
                processed_count += 1
                line = f"{minimum_order_quantity}|{sid}|{name}|{'|'.join(barcodes) if barcodes else 'Нет штрихкодов'}\n"
                buffer.append(line)

                print(f"Min Qty: {minimum_order_quantity}")
                print(f"SID: {sid}")
                print(f"Name: {name}")
                print(f"Barcodes: {'|'.join(barcodes) if barcodes else 'Нет штрихкодов'}")
                print(f"Обработано: {processed_count}")
                print("---")

                if processed_count % SAVE_INTERVAL == 0:
                    file.writelines(buffer)
                    buffer.clear()
                    status_label.config(text=f"Обработано: {processed_count} артикулов")
                    root.update()

        if buffer:
            file.writelines(buffer)
    
    status_label.config(text=f"Обработка завершена. Обработано: {processed_count} артикулов")
    root.update()

def parse_line(line):
    parts = line.strip().split("|")
    if len(parts) < 4:
        return None
    min_qty = parts[0]
    sid = parts[1]
    name = parts[2]
    barcodes = parts[3:] if parts[3] != "Нет штрихкодов" else []
    return {"min_qty": min_qty, "sid": sid, "name": name, "barcodes": barcodes}

def create_yml(build_name, custom_tag_value, status_label):
    result = []
    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            data = parse_line(line)
            if data:
                result.append(data)

    root_xml = ET.Element("yml_catalog", date=datetime.utcnow().isoformat() + "+00:00")
    shop = ET.SubElement(root_xml, "shop")
    offers = ET.SubElement(shop, "offers")

    for item in result:
        offer = ET.SubElement(offers, "offer", id=str(item["sid"]))
        ET.SubElement(offer, "name").text = item["name"]
        if build_name:
            oshiptag = ET.SubElement(offer, "oshiptag")
            oshiptag.set("color", "yellow")
            oshiptag.text = build_name[:10]
        try:
            min_qty_int = int(item["min_qty"])
            if min_qty_int > 1:
                oshiptag = ET.SubElement(offer, "oshiptag")
                oshiptag.set("color", "green")
                oshiptag.text = str(item["min_qty"])[:10]
        except ValueError:
            print(f"Предупреждение: min_qty для SID {item['sid']} не является числом: {item['min_qty']}")
        if custom_tag_value:
            oshiptag = ET.SubElement(offer, "oshiptag")
            oshiptag.set("color", "yellow")
            oshiptag.text = custom_tag_value[:10]
        for barcode in item["barcodes"]:
            ET.SubElement(offer, "barcode").text = barcode

    tree = ET.ElementTree(root_xml)
    ET.indent(tree, space="  ")
    tree.write(YML_OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    status_label.config(text=f"YML сохранён в {YML_OUTPUT_FILE}")
    root.update()

def load_articles():
    articles_text = text_area.get("1.0", tk.END).strip()
    if not articles_text:
        messagebox.showerror("Ошибка", "Пожалуйста, введите артикулы.")
        return

    # Сохраняем артикулы во временный input.txt
    with open(INPUT_FILE, "w", encoding="utf-8") as file:
        file.write(articles_text)

    # Показываем поля для тегов и кнопки
    tag_frame.pack(pady=10)
    build_name_label.pack(side=tk.LEFT)
    build_name_entry.pack(side=tk.LEFT, padx=5)
    custom_tag_label.pack(side=tk.LEFT)
    custom_tag_entry.pack(side=tk.LEFT, padx=5)
    process_button.pack(pady=5)
    skip_tags_button.pack(pady=5)

    text_area.config(state="disabled")
    load_button.config(state="disabled")

def process_with_tags():
    build_name = build_name_entry.get().strip()
    custom_tag_value = custom_tag_entry.get().strip()
    
    articles = read_articles(INPUT_FILE)
    if not articles:
        messagebox.showerror("Ошибка", "Файл с артикулами пуст или не найден.")
        return

    try:
        process_articles(articles, status_label)
        create_yml(build_name, custom_tag_value, status_label)
        messagebox.showinfo("Успех", f"Обработка завершена. YML сохранён в {YML_OUTPUT_FILE}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    finally:
        reset_ui()

def skip_tags():
    articles = read_articles(INPUT_FILE)
    if not articles:
        messagebox.showerror("Ошибка", "Файл с артикулами пуст или не найден.")
        return

    try:
        process_articles(articles, status_label)
        create_yml("", "", status_label)
        messagebox.showinfo("Успех", f"Обработка завершена. YML сохранён в {YML_OUTPUT_FILE}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    finally:
        reset_ui()

def reset_ui():
    text_area.config(state="normal")
    text_area.delete("1.0", tk.END)
    load_button.config(state="normal")
    tag_frame.pack_forget()
    status_label.config(text="")

# Создание GUI
root = tk.Tk()
root.title("Обработка артикулов")
root.geometry("600x400")

# Поле ввода артикулов
text_area = tk.Text(root, height=10, width=50)
text_area.pack(pady=10)

# Кнопка "Загрузить артикулы"
load_button = tk.Button(root, text="Загрузить артикулы", command=load_articles)
load_button.pack(pady=5)

# Фрейм для тегов
tag_frame = tk.Frame(root)
build_name_label = tk.Label(tag_frame, text="Название сборки (до 10 символов):")
build_name_entry = tk.Entry(tag_frame, width=20)
custom_tag_label = tk.Label(tag_frame, text="Дополнительный тег (до 10 символов):")
custom_tag_entry = tk.Entry(tag_frame, width=20)
process_button = tk.Button(tag_frame, text="Обработать с тегами", command=process_with_tags)
skip_tags_button = tk.Button(tag_frame, text="Не добавлять теги", command=skip_tags)

# Метка статуса
status_label = tk.Label(root, text="")
status_label.pack(pady=10)

# Запуск приложения
root.mainloop()