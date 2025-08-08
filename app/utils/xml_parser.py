# -*- coding: utf-8 -*-
"""
Модуль для парсинга XML-файлов.

Этот модуль содержит функцию для извлечения информации о продуктах
из XML-файла.
"""

from lxml import etree
from typing import List, Dict
import logging

# Настройка логгера для этого модуля
logger = logging.getLogger(__name__)

def parse_products_from_xml(path: str) -> List[Dict]:
    """
    Парсит информацию о продуктах из XML-файла.

    Args:
        path (str): Путь к XML-файлу.

    Returns:
        List[Dict]: Список словарей, где каждый словарь представляет продукт.

    Raises:
        etree.XMLSyntaxError: Если в XML-файле синтаксическая ошибка.
        OSError: Если файл не найден или не может быть прочитан.
    """
    # Создание парсера с возможностью восстановления и указанием кодировки
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    try:
        # Парсинг XML-файла
        tree = etree.parse(path, parser=parser)
        root = tree.getroot()
    except (etree.XMLSyntaxError, OSError) as e:
        logger.exception("Ошибка парсинга XML: %s", e)
        raise

    products = []
    # Пример: поиск элементов независимо от пространства имен
    for el in root.findall(".//{*}product"):
        try:
            # Извлечение данных о продукте: id, name, description
            pid = el.findtext(".//{*}id") or ""
            name = el.findtext(".//{*}name") or ""
            desc = el.findtext(".//{*}description") or ""
            # Добавление продукта в список с удалением лишних пробелов
            products.append({"id": pid.strip(), "name": name.strip(), "description": desc.strip()})
        except Exception:
            logger.exception("Ошибка парсинга элемента product")

    return products
