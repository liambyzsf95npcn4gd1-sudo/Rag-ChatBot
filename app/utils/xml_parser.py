from lxml import etree
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def parse_products_from_xml(path: str) -> List[Dict]:
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    try:
        tree = etree.parse(path, parser=parser)
        root = tree.getroot()
    except (etree.XMLSyntaxError, OSError) as e:
        logger.exception("XML parse error: %s", e)
        raise

    products = []
    # Example: find elements regardless of namespace
    for el in root.findall(".//{*}product"):
        try:
            pid = el.findtext(".//{*}id") or ""
            name = el.findtext(".//{*}name") or ""
            desc = el.findtext(".//{*}description") or ""
            products.append({"id": pid.strip(), "name": name.strip(), "description": desc.strip()})
        except Exception:
            logger.exception("Error parsing product element")
    return products
