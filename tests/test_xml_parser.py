# -*- coding: utf-8 -*-
"""
Тесты для модуля парсинга XML.

Этот файл содержит тесты для функции `parse_products_from_xml`
из модуля `app.utils.xml_parser`.
"""

import pytest
import os
from app.utils.xml_parser import parse_products_from_xml
from lxml import etree

# Пример корректного содержимого XML-файла
SAMPLE_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<ns:root xmlns:ns="http://www.example.com/ns">
    <ns:products>
        <ns:product>
            <ns:id>1</ns:id>
            <ns:name>Product A</ns:name>
            <ns:description>Description for A</ns:description>
        </ns:product>
        <ns:product>
            <ns:id>2</ns:id>
            <ns:name>Product B</ns:name>
            <ns:description>Description for B</ns:description>
        </ns:product>
    </ns:products>
</ns:root>
"""

# Пример некорректного (поврежденного) содержимого XML-файла
MALFORMED_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<ns:root xmlns:ns="http://www.example.com/ns">
    <ns:products>
        <ns:product>
            <ns:id>1</ns:id>
            <ns:name>Product A</ns:name>
            <ns:description>Description for A</ns:description>
        </ns:product>
    </ns:products>
</ns:root
"""

@pytest.fixture
def sample_xml_file(tmp_path):
    """
    Фикстура для создания временного корректного XML-файла.
    """
    file_path = tmp_path / "sample.xml"
    file_path.write_text(SAMPLE_XML_CONTENT, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def malformed_xml_file(tmp_path):
    """
    Фикстура для создания временного поврежденного XML-файла.
    """
    file_path = tmp_path / "malformed.xml"
    file_path.write_text(MALFORMED_XML_CONTENT, encoding="utf-8")
    return str(file_path)

def test_parse_products_from_xml_success(sample_xml_file):
    """
    Тестирует успешный парсинг корректного XML-файла.
    Проверяет, что количество продуктов и их данные соответствуют ожидаемым.
    """
    products = parse_products_from_xml(sample_xml_file)
    assert len(products) == 2
    assert products[0] == {"id": "1", "name": "Product A", "description": "Description for A"}
    assert products[1] == {"id": "2", "name": "Product B", "description": "Description for B"}

def test_parse_products_from_xml_malformed(malformed_xml_file):
    """
    Тестирует парсинг поврежденного XML-файла.
    Проверяет, что парсер `lxml` с опцией `recover=True` может обработать
    файл и извлечь часть данных.
    """
    products = parse_products_from_xml(malformed_xml_file)
    assert len(products) == 1
    assert products[0] == {"id": "1", "name": "Product A", "description": "Description for A"}

def test_parse_products_from_xml_file_not_found():
    """
    Тестирует поведение функции при попытке открыть несуществующий файл.
    Проверяет, что возбуждается исключение `OSError`.
    """
    with pytest.raises(OSError):
        parse_products_from_xml("non_existent_file.xml")
