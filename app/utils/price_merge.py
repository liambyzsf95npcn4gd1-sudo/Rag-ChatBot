# -*- coding: utf-8 -*-
"""
Модуль для объединения данных о продуктах с ценами.

Этот модуль содержит функции для загрузки данных о ценах из CSV-файла
и их последующего объединения с данными о продуктах.
"""

import pandas as pd
import logging

# Настройка логгера для этого модуля
logger = logging.getLogger(__name__)

def load_price_csv(path: str) -> pd.DataFrame:
    """
    Загружает данные о ценах из CSV-файла.

    Args:
        path (str): Путь к CSV-файлу.

    Returns:
        pd.DataFrame: DataFrame с данными о ценах.

    Raises:
        Exception: Если не удалось прочитать CSV-файл.
    """
    try:
        # Чтение CSV с указанием кодировки и типа данных
        df = pd.read_csv(path, encoding='utf-8-sig', dtype=str)
    except Exception as e:
        logger.exception("Не удалось прочитать CSV: %s", e)
        raise

    # Приведение названий колонок к нижнему регистру и удаление пробелов
    df.columns = [c.strip().lower() for c in df.columns]

    # Удаление пробелов в начале и конце строк во всех строковых колонках
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()

    # Преобразование типа данных для колонок 'id' или 'sku'
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str)
    elif 'sku' in df.columns:
        df['sku'] = df['sku'].astype(str)

    return df

def merge_products_with_prices(products: list, price_df: pd.DataFrame) -> list:
    """
    Объединяет список продуктов с DataFrame цен.

    Args:
        products (list): Список словарей, представляющих продукты.
        price_df (pd.DataFrame): DataFrame с данными о ценах.

    Returns:
        list: Список словарей с объединенными данными о продуктах и ценах.

    Raises:
        ValueError: Если в продуктах нет колонок 'id' или 'sku'.
    """
    # Преобразование списка продуктов в DataFrame
    p_df = pd.DataFrame(products)

    # Определение ключа для объединения ('id' или 'sku')
    if 'id' in p_df.columns:
        key = 'id'
    elif 'sku' in p_df.columns:
        key = 'sku'
    else:
        raise ValueError("В продуктах отсутствуют колонки 'id'/'sku'")

    # Объединение DataFrame продуктов и цен по ключу
    merged = p_df.merge(price_df, how='left', on=key)

    # Возврат результата в виде списка словарей
    return merged.to_dict(orient='records')
