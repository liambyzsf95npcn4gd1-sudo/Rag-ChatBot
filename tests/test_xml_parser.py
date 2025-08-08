import pytest
import os
from app.utils.xml_parser import parse_products_from_xml

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
    file_path = tmp_path / "sample.xml"
    file_path.write_text(SAMPLE_XML_CONTENT, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def malformed_xml_file(tmp_path):
    file_path = tmp_path / "malformed.xml"
    file_path.write_text(MALFORMED_XML_CONTENT, encoding="utf-8")
    return str(file_path)

def test_parse_products_from_xml_success(sample_xml_file):
    products = parse_products_from_xml(sample_xml_file)
    assert len(products) == 2
    assert products[0] == {"id": "1", "name": "Product A", "description": "Description for A"}
    assert products[1] == {"id": "2", "name": "Product B", "description": "Description for B"}

def test_parse_products_from_xml_malformed(malformed_xml_file):
    # The lxml parser with recover=True should still be able to parse the file
    products = parse_products_from_xml(malformed_xml_file)
    assert len(products) == 1
    assert products[0] == {"id": "1", "name": "Product A", "description": "Description for A"}

def test_parse_products_from_xml_file_not_found():
    with pytest.raises(OSError):
        parse_products_from_xml("non_existent_file.xml")
