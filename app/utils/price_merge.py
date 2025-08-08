import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_price_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding='utf-8-sig', dtype=str)
    except Exception as e:
        logger.exception("Failed to read CSV: %s", e)
        raise
    df.columns = [c.strip().lower() for c in df.columns]
    # Trim whitespace in all string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str)
    elif 'sku' in df.columns:
        df['sku'] = df['sku'].astype(str)
    return df

def merge_products_with_prices(products: list, price_df: pd.DataFrame) -> list:
    p_df = pd.DataFrame(products)
    if 'id' in p_df.columns:
        key = 'id'
    elif 'sku' in p_df.columns:
        key = 'sku'
    else:
        raise ValueError("No id/sku in products")
    merged = p_df.merge(price_df, how='left', on=key)
    return merged.to_dict(orient='records')
