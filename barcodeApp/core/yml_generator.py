"""
Генерация YML-файла для ОЗОН.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from utils.helpers import get_data_dir


class YMLGenerator:
    def __init__(self):
        self.data_dir = get_data_dir()

    def generate(self, all_articles, collections, output_path=None):
        """
        Генерирует output.yml.
        :param all_articles: список всех артикулов
        :param collections: список сборок [(tag, name, articles)]
        :param output_path: куда сохранить
        """
        if not output_path:
            output_path = os.path.join(self.data_dir, "output.yml")

        # Чтение данных из output.txt
        data_map = self._load_item_data()
        if not data_map:
            raise RuntimeError("Не удалось загрузить данные из output.txt")

        root = ET.Element("yml_catalog", date=datetime.utcnow().isoformat() + "+00:00")
        shop = ET.SubElement(root, "shop")
        offers = ET.SubElement(shop, "offers")

        for sid in all_articles:
            if sid not in data_map:
                continue
            item = data_map[sid]
            offer = ET.SubElement(offers, "offer", id=sid)
            ET.SubElement(offer, "name").text = item["name"]

            # Теги из сборок
            for tag, name, articles in collections:
                if sid in articles:
                    # Название — жёлтый
                    oshiptag = ET.SubElement(offer, "oshiptag")
                    oshiptag.set("color", "yellow")
                    oshiptag.text = name
                    # Дата — синий
                    oshiptag = ET.SubElement(offer, "oshiptag")
                    oshiptag.set("color", "blue")
                    oshiptag.text = tag

            # min_qty > 1 — зелёный
            try:
                min_qty = int(item["min_qty"])
                if min_qty > 1:
                    oshiptag = ET.SubElement(offer, "oshiptag")
                    oshiptag.set("color", "green")
                    oshiptag.text = str(min_qty)[:10]
            except (ValueError, TypeError):
                pass

            # Штрихкоды
            for barcode in item["barcodes"]:
                ET.SubElement(offer, "barcode").text = barcode

        # Форматирование и сохранение
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path

    def _load_item_data(self):
        """Загружает данные из output.txt."""
        path = os.path.join(self.data_dir, "output.txt")
        data = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        data[parts[1]] = {
                            "min_qty": parts[0],
                            "name": parts[2],
                            "barcodes": parts[3:] if parts[3] != "Нет штрихкодов" else []
                        }
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения output.txt: {e}")
        return data