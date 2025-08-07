import streamlit as st
import os
import xmltodict
import pandas as pd
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

def parse_xml_files(xml_files):
    """
    Parses multiple XML files and extracts product data with basic validation.

    Args:
        xml_files (list): A list of paths to XML files.

    Returns:
        list: A list of dictionaries, where each dictionary represents a product.
    """
    products = []
    for file_path in xml_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = xmltodict.parse(file.read())

                # Basic validation: Check for top-level product container
                if 'products' in data and 'product' in data['products']:
                    product_list = data['products']['product']
                    # Ensure product_list is a list
                    if not isinstance(product_list, list):
                        product_list = [product_list]

                    for p in product_list:
                        if isinstance(p, dict) and 'product_id' in p:
                            products.append(p)
                        else:
                            print(f"Warning: Skipping malformed product entry in {file_path}")

                elif 'product' in data:
                    # Handle case where root is a single product
                    product_entry = data['product']
                    if isinstance(product_entry, dict) and 'product_id' in product_entry:
                        products.append(product_entry)
                    else:
                        print(f"Warning: Skipping malformed single product entry in {file_path}")
                else:
                    print(f"Warning: No 'products' or 'product' tag found in {file_path}. Skipping file.")

        except Exception as e:
            print(f"Error parsing XML file {file_path}: {e}")
    return products

def parse_price_list(price_file_path):
    """
    Parses a CSV or XLSX price list into a dictionary.

    Args:
        price_file_path (str): The path to the price list file.

    Returns:
        dict: A dictionary mapping product_id to price.
    """
    if not price_file_path or not os.path.exists(price_file_path):
        return {}

    try:
        if price_file_path.endswith('.csv'):
            df = pd.read_csv(price_file_path)
        elif price_file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(price_file_path)
        else:
            return {}

        df['product_id'] = df['product_id'].astype(str)
        return pd.Series(df.price.values, index=df.product_id).to_dict()
    except Exception as e:
        print(f"Error parsing price file {price_file_path}: {e}")
        return {}


def create_product_documents(products, prices):
    """
    Creates LangChain Document objects from product and price data.

    Args:
        products (list): A list of product dictionaries.
        prices (dict): A dictionary mapping product_id to price.

    Returns:
        list: A list of LangChain Document objects.
    """
    documents = []
    for product in products:
        product_id = product.get("product_id")
        price = prices.get(str(product_id), "Цена не указана")

        characteristics_str = ""
        if 'characteristics' in product and isinstance(product['characteristics'], dict):
            characteristics_str = "\n".join([f"  - {key}: {value}" for key, value in product['characteristics'].items()])

        content = f"""Название: {product.get("name", "Без названия")}
Описание: {product.get("description", "Нет описания")}
Характеристики:
{characteristics_str}
Цена: {price} руб.""".strip()

        doc = Document(
            page_content=content,
            metadata={
                "source": "products",
                "product_id": str(product_id),
                "product_name": product.get("name", "Без названия")
            }
        )
        documents.append(doc)
    return documents

def get_text_chunks(docs):
    """
    Split text into chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""])
    chunks = text_splitter.split_documents(docs)
    return chunks

import streamlit as st

# (keeping other imports as they are)

@st.cache_resource
def load_vectorstore():
    """
    Loads the vectorstore from disk. Uses Streamlit's caching to avoid reloading.
    """
    load_dotenv()
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    persist_directory = "Vector_DB_Products"

    if os.path.exists(persist_directory):
        print("Loading cached vectorstore from disk.")
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
        return vectordb
    return None

def create_vectorstore(product_xml_paths, price_file_path):
    """
    Creates a new vectorstore and returns it along with the parsed product data.
    """
    load_dotenv()
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    persist_directory = "Vector_DB_Products"

    products_data = parse_xml_files(product_xml_paths)
    price_data = parse_price_list(price_file_path)

    if not products_data:
        print("No product data found. Vectorstore not created.")
        return None, None

    documents = create_product_documents(products_data, price_data)
    chunks = get_text_chunks(documents)

    print("Creating new vectorstore...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=persist_directory
    )
    # Clear the cache for the loader function, so it reloads the new DB on the next run
    load_vectorstore.clear()
    return vectordb, products_data
