# -*- coding: utf-8 -*-
"""
Модуль для инициализации переменных состояния сессии.

Этот модуль содержит функцию для установки начальных значений
переменных в состоянии сессии Streamlit (`st.session_state`).
"""

import os
from utils.prepare_vectordb import get_vectorstore
from utils.save_docs import file_hash
from utils.config import GOOGLE_API_KEY, CHROMA_PERSIST_DIR

def initialize_session_state_variables(st):
    """
    Инициализирует переменные состояния сессии для приложения Streamlit.

    Args:
        st: Объект Streamlit, используемый для доступа к `session_state`.
    """
    # Получаем список уже загруженных документов
    upload_docs = os.listdir("docs")

    # Инициализация множества для хранения хешей обработанных файлов
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
        # Заполняем множество хешами уже существующих файлов
        for filename in upload_docs:
            file_path = os.path.join("docs", filename)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    st.session_state.processed_files.add(file_hash(f.read()))

    # Инициализация истории чата
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Инициализация списка загруженных PDF-файлов (может быть устаревшим, но сохранено для совместимости)
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = []

    # Инициализация списка обработанных документов
    if "processed_documents" not in st.session_state:
        st.session_state.processed_documents = upload_docs

    # Инициализация векторного хранилища
    if "vectordb" not in st.session_state:
        st.session_state.vectordb = get_vectorstore(
            google_api_key=GOOGLE_API_KEY,
            persist_directory=CHROMA_PERSIST_DIR,
            docs_files=upload_docs,
            from_session_state=True
        )

    # Инициализация счетчика количества загруженных документов для отслеживания изменений
    if "previous_upload_docs_length" not in st.session_state:
        st.session_state.previous_upload_docs_length = len(upload_docs)