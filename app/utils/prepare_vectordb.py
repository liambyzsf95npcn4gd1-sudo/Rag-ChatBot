# -*- coding: utf-8 -*-
"""
Модуль для подготовки векторной базы данных.

Этот модуль содержит функции для извлечения текста из документов,
разделения текста на фрагменты и создания или получения векторного хранилища.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
import logging
from pathlib import Path
from langchain_core.documents import Document
from .xml_parser import parse_products_from_xml

def extract_text(docs_files):
    """
    Извлекает текст из документов PDF и XML.

    Args:
        docs_files (list): Список имен файлов документов.

    Returns:
        list: Список объектов Document, содержащих извлеченный текст.
    """
    docs = []
    for doc_file in docs_files:
        file_path = os.path.join("docs", doc_file)
        if doc_file.endswith(".pdf"):
            # Загрузка и извлечение текста из PDF
            docs.extend(PyPDFLoader(file_path).load())
        elif doc_file.endswith(".xml"):
            # Парсинг продуктов из XML и создание документов
            products = parse_products_from_xml(file_path)
            for product in products:
                content = f"ID: {product['id']}\nНазвание: {product['name']}\nОписание: {product['description']}"
                docs.append(Document(page_content=content, metadata={"source": doc_file, **product}))
    return docs

def get_text_chunks(docs):
    """
    Разделяет текст на фрагменты (чанки).

    Args:
        docs (list): Список текстовых документов.

    Returns:
        list: Список фрагментов текста.
    """
    # Размер чанка настроен как приближение к лимиту модели в 2048 токенов
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=800, separators=["\n\n", "\n", " ", ""])
    chunks = text_splitter.split_documents(docs)
    return chunks

def get_vectorstore(google_api_key, persist_directory, docs_files=None, documents=None, from_session_state=False):
    """
    Создает или извлекает векторное хранилище из документов.

    Args:
        google_api_key (str): API-ключ для Google Generative AI.
        persist_directory (str): Директория для сохранения/загрузки векторного хранилища.
        docs_files (list, optional): Список имен файлов документов. Defaults to None.
        documents (list, optional): Список уже загруженных документов. Defaults to None.
        from_session_state (bool, optional): Флаг, указывающий, следует ли загружать из состояния сессии. Defaults to False.

    Returns:
        Chroma or None: Созданное или извлеченное векторное хранилище.
                         Возвращает None, если загрузка из состояния сессии не удалась.
    """
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    persist_dir = Path(persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True) # Создаем директорию, если она не существует

    if from_session_state and persist_dir.exists() and any(persist_dir.iterdir()):
        # Извлечение векторного хранилища из существующего
        logging.info(f"Загрузка векторного хранилища из {persist_directory}")
        vectordb = Chroma(persist_directory=str(persist_dir), embedding_function=embedding)
        return vectordb
    elif not from_session_state:
        logging.info("Создание нового векторного хранилища.")
        # Если документы не переданы, извлекаем их из файлов
        if documents is None and docs_files is not None:
            documents = extract_text(docs_files)

        if documents:
            chunks = get_text_chunks(documents)
            try:
                # Создание векторного хранилища из чанков и сохранение его
                logging.info("Встраивание документов.")
                vectordb = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory=str(persist_dir))
                return vectordb
            except Exception as e:
                logging.exception("Ошибка встраивания")
                raise RuntimeError("Ошибка при создании встраивания — проверьте API-ключ и сеть") from e

    logging.warning("Векторное хранилище не было создано или загружено.")
    return None