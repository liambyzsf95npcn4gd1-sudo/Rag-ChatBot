# -*- coding: utf-8 -*-
"""
Тесты для модуля слияния цен.

Этот файл содержит тесты для функций `load_price_csv` и `merge_products_with_prices`
из модуля `app.utils.price_merge`.
"""

import pytest
import pandas as pd
from app.utils.price_merge import load_price_csv, merge_products_with_prices

# Пример содержимого CSV-файла для тестов
SAMPLE_CSV_CONTENT = """"ID","Price ","Currency"
"1","10.99","USD"
"2","20.50","USD"
"""

# Пример содержимого CSV-файла с BOM (Byte Order Mark)
SAMPLE_CSV_WITH_BOM = u'\ufeff' + SAMPLE_CSV_CONTENT

@pytest.fixture
def sample_csv_file(tmp_path):
    """
    Фикстура для создания временного CSV-файла.
    """
    file_path = tmp_path / "prices.csv"
    file_path.write_text(SAMPLE_CSV_CONTENT, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def sample_csv_file_with_bom(tmp_path):
    """
    Фикстура для создания временного CSV-файла с BOM.
    """
    file_path = tmp_path / "prices_bom.csv"
    file_path.write_text(SAMPLE_CSV_WITH_BOM, encoding="utf-8-sig")
    return str(file_path)

def test_load_price_csv(sample_csv_file):
    """
    Тестирует загрузку данных из обычного CSV-файла.
    Проверяет, что колонки правильно названы, тип данных корректен,
    и количество строк соответствует ожидаемому.
    """
    df = load_price_csv(sample_csv_file)
    assert 'id' in df.columns
    assert 'price' in df.columns
    assert 'currency' in df.columns
    assert df['id'].dtype == 'object'
    assert len(df) == 2

def test_load_price_csv_with_bom(sample_csv_file_with_bom):
    """
    Тестирует загрузку данных из CSV-файла с BOM.
    Проверяет, что BOM корректно обрабатывается и данные загружаются.
    """
    df = load_price_csv(sample_csv_file_with_bom)
    assert 'id' in df.columns
    assert len(df) == 2

def test_merge_products_with_prices():
    """
    Тестирует слияние данных о продуктах с данными о ценах.
    Проверяет, что цены правильно присоединяются к продуктам
    и что для продуктов без цен значение цены равно NaN.
    """
    products = [
        {"id": "1", "name": "Product A", "description": "Desc A"},
        {"id": "2", "name": "Product B", "description": "Desc B"},
        {"id": "3", "name": "Product C", "description": "Desc C"},
    ]
    price_data = {
        'id': ['1', '2'],
        'price': ['10.99', '20.50'],
        'currency': ['USD', 'USD']
    }
    price_df = pd.DataFrame(price_data)

    merged_products = merge_products_with_prices(products, price_df)
    assert len(merged_products) == 3
    assert merged_products[0]['price'] == '10.99'
    assert merged_products[1]['price'] == '20.50'
    # Проверяем, что цена для третьего продукта отсутствует (NaN)
    assert pd.isna(merged_products[2]['price'])
