import pytest
import pandas as pd
from app.utils.price_merge import load_price_csv, merge_products_with_prices

SAMPLE_CSV_CONTENT = """"ID","Price ","Currency"
"1","10.99","USD"
"2","20.50","USD"
"""

SAMPLE_CSV_WITH_BOM = u'\ufeff' + SAMPLE_CSV_CONTENT

@pytest.fixture
def sample_csv_file(tmp_path):
    file_path = tmp_path / "prices.csv"
    file_path.write_text(SAMPLE_CSV_CONTENT, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def sample_csv_file_with_bom(tmp_path):
    file_path = tmp_path / "prices_bom.csv"
    file_path.write_text(SAMPLE_CSV_WITH_BOM, encoding="utf-8-sig")
    return str(file_path)

def test_load_price_csv(sample_csv_file):
    df = load_price_csv(sample_csv_file)
    assert 'id' in df.columns
    assert 'price' in df.columns
    assert 'currency' in df.columns
    assert df['id'].dtype == 'object'
    assert len(df) == 2

def test_load_price_csv_with_bom(sample_csv_file_with_bom):
    df = load_price_csv(sample_csv_file_with_bom)
    assert 'id' in df.columns
    assert len(df) == 2

def test_merge_products_with_prices():
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
    assert pd.isna(merged_products[2]['price'])
