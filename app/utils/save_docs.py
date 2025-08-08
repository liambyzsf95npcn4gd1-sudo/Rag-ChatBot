# -*- coding: utf-8 -*-
"""
Модуль для сохранения загруженных документов.

Этот модуль содержит функции для сохранения загруженных файлов
в локальную директорию и их последующей обработки для
создания или обновления векторного хранилища.
"""

import streamlit as st
import os
import hashlib
from utils.prepare_vectordb import get_vectorstore
import logging

def file_hash(file_bytes):
    """
    Вычисляет MD5-хеш для содержимого файла.

    Args:
        file_bytes (bytes): Содержимое файла в байтах.

    Returns:
        str: MD5-хеш в виде шестнадцатеричной строки.
    """
    return hashlib.md5(file_bytes).hexdigest()

def save_docs_to_vectordb(uploaded_files, upload_docs):
    """
    Сохраняет загруженные документы в папку 'docs' и создает или обновляет векторное хранилище.

    Args:
        uploaded_files (list): Список загруженных файлов (объекты UploadedFile от Streamlit).
        upload_docs (list): Список имен ранее загруженных документов.
    """
    new_files_to_process = []
    if uploaded_files:
        for f in uploaded_files:
            file_bytes = f.read()
            # Вычисляем хеш, чтобы избежать повторной обработки того же файла
            h = file_hash(file_bytes)
            if h in st.session_state.get("processed_files", set()):
                st.write(f"{f.name} — уже обработан")
                continue

            # Сохраняем файл в docs/ с уникальным именем и обрабатываем его
            file_path = os.path.join("docs", f.name)
            with open(file_path, "wb") as f_out:
                f_out.write(file_bytes)

            # Добавляем хеш в множество обработанных файлов в состоянии сессии
            st.session_state.setdefault("processed_files", set()).add(h)
            new_files_to_process.append(f.name)

    # Если есть новые файлы для обработки и нажата кнопка "Process"
    if new_files_to_process and st.button("Обработать"):
        with st.spinner("Обработка..."):
            logging.info(f"Обработка новых файлов: {new_files_to_process}")
            # get_vectorstore(new_files_to_process) # Эта строка закомментирована, так как вызов get_vectorstore происходит в app.py
            st.success(f"Файлы успешно обработаны.")
            # Необходимо перезапустить приложение, чтобы обновить пользовательский интерфейс
            st.rerun()