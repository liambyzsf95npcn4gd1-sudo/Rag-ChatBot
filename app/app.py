# -*- coding: utf-8 -*-
"""
Основной файл приложения для запуска чат-бота с документами.

Этот файл содержит класс `ChatApp`, который инкапсулирует всю логику
приложения Streamlit. Он отвечает за настройку интерфейса, обработку
загрузки документов, взаимодействие с чат-ботом и управление состоянием сессии.
"""

import streamlit as st
import os
from utils.save_docs import save_docs_to_vectordb
from utils.session_state import initialize_session_state_variables
from utils.prepare_vectordb import get_vectorstore
from utils.chatbot import chat
from utils.send_email import send_email
from utils.price_merge import load_price_csv, merge_products_with_prices
from langchain_core.documents import Document
import shutil
import logging
from utils.config import GOOGLE_API_KEY, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MANAGER_EMAIL, CHROMA_PERSIST_DIR
import pandas as pd

# Настройка логирования для отладки и мониторинга
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Проверка наличия обязательной переменной окружения
# GOOGLE_API_KEY необходим для работы с моделями Google
if not GOOGLE_API_KEY:
    raise RuntimeError("Отсутствует переменная окружения: GOOGLE_API_KEY — пожалуйста, создайте файл .env с этой переменной. Вы можете получить ключ на https://aistudio.google.com/app/apikey")

class ChatApp:
    """
    Приложение Streamlit для общения с документами в формате PDF и XML.

    Этот класс инкапсулирует функциональность для загрузки документов, их обработки
    и предоставления пользователям возможности общаться с документами с помощью чат-бота.
    Он управляет инициализацией конфигураций Streamlit и переменных состояния сессии,
    а также пользовательским интерфейсом для загрузки документов и взаимодействия в чате.
    """
    def __init__(self):
        """
        Инициализирует класс ChatApp.

        Этот метод обеспечивает наличие папки 'docs', устанавливает конфигурации
        страницы Streamlit и инициализирует переменные состояния сессии.
        """
        logging.info("Запуск ChatApp")
        # Убеждаемся, что папка 'docs' существует, если нет - создаем
        if not os.path.exists("docs"):
            os.makedirs("docs")

        # Конфигурации и инициализация состояния сессии
        st.set_page_config(page_title="Чат с вашими документами :books:")
        st.title("Чат с вашими документами :books:")
        initialize_session_state_variables(st)  # Инициализация переменных сессии
        self.docs_files = st.session_state.processed_documents

    def run(self):
        """
        Запускает приложение Streamlit для общения с PDF-файлами.

        Этот метод управляет пользовательским интерфейсом для загрузки документов,
        разблокирует чат после загрузки документов и блокирует его до тех пор,
        пока документы не будут загружены.
        """
        upload_docs = os.listdir("docs")
        # Боковая панель для загрузки документов
        with st.sidebar:
            st.subheader("Ваши документы")
            if upload_docs:
                st.write("Загруженные документы:")
                st.text(", ".join(upload_docs))
            else:
                st.info("Документы еще не загружены.")
            st.subheader("Загрузка документов")
            uploaded_files = st.file_uploader("Выберите документ и нажмите 'Обработать'", type=['pdf', 'xml'], accept_multiple_files=True)

            # Проверяем, были ли загружены новые файлы
            if 'last_uploaded_files' not in st.session_state:
                st.session_state['last_uploaded_files'] = []

            if uploaded_files and uploaded_files != st.session_state.last_uploaded_files:
                st.session_state.last_uploaded_files = uploaded_files
                save_docs_to_vectordb(uploaded_files, upload_docs)
                st.rerun()  # Перезапуск скрипта для обновления интерфейса

            st.subheader("Загрузка CSV с ценами")
            uploaded_csv = st.file_uploader("Выберите CSV с ценами", type=['csv'])
            if uploaded_csv and uploaded_csv.name != st.session_state.get("last_uploaded_csv_name"):
                st.session_state["last_uploaded_csv_name"] = uploaded_csv.name
                st.session_state["price_df"] = load_price_csv(uploaded_csv)

            # Если есть DataFrame с ценами, показываем кнопку для объединения
            if st.session_state.get("price_df") is not None and st.button("Объединить цены"):
                with st.spinner("Объединение цен и обновление базы данных..."):
                    # Эта часть предполагает, что данные о продуктах хранятся в векторной базе данных
                    # и мы можем извлечь их для объединения с данными о ценах.
                    # Это упрощение. В реальном приложении потребуется более надежный
                    # способ получения данных о продуктах.
                    retrieved_docs = st.session_state.vectordb.get()
                    products = [metadata for metadata in retrieved_docs['metadatas']]
                    merged_products = merge_products_with_prices(products, st.session_state.price_df)

                    # Пересоздание векторного хранилища с объединенными данными
                    # Это также упрощение. В реальном приложении вы бы обновили существующее
                    # векторное хранилище, а не пересоздавали его.
                    if os.path.exists(CHROMA_PERSIST_DIR):
                        shutil.rmtree(CHROMA_PERSIST_DIR)

                    # Создание новых документов с объединенными данными
                    merged_docs = [
                        Document(page_content=f"ID: {p.get('id', '')}\nНазвание: {p.get('name', '')}\nОписание: {p.get('description', '')}\nЦена: {p.get('price', '')}",
                                 metadata=p)
                        for p in merged_products
                    ]

                    st.session_state.vectordb = get_vectorstore(google_api_key=GOOGLE_API_KEY, persist_directory=CHROMA_PERSIST_DIR, documents=merged_docs, from_session_state=False)
                    st.success("Цены объединены, база данных обновлена.")
                    st.rerun()

            st.subheader("Управление базой данных")
            if st.button("Перестроить индекс"):
                with st.spinner("Перестроение индекса..."):
                    if os.path.exists(CHROMA_PERSIST_DIR):
                        shutil.rmtree(CHROMA_PERSIST_DIR)
                    st.session_state.vectordb = get_vectorstore(google_api_key=GOOGLE_API_KEY, persist_directory=CHROMA_PERSIST_DIR, docs_files=upload_docs, from_session_state=False)
                    st.success("Индекс успешно перестроен.")
                    st.rerun()

            # Отправка истории чата по электронной почте
            if st.session_state.chat_history and all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MANAGER_EMAIL]):
                st.subheader("Отправить историю чата")
                recipient_email = st.text_input("Email получателя:")
                if st.button("Отправить Email"):
                    chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in st.session_state.chat_history])
                    try:
                        send_email("История чата", chat_history_str, [recipient_email], from_email=SMTP_USER)
                        st.success("Email успешно отправлен!")
                    except Exception as e:
                        st.error(f"Не удалось отправить email: {e}")

        # Разблокировка чата после загрузки документа
        if self.docs_files or st.session_state.uploaded_pdfs:
            # Проверка, был ли загружен новый документ, для обновления vectordb в состоянии сессии
            if len(upload_docs) > st.session_state.previous_upload_docs_length:
                st.session_state.vectordb = get_vectorstore(upload_docs, GOOGLE_API_KEY, CHROMA_PERSIST_DIR, from_session_state=True)
                st.session_state.previous_upload_docs_length = len(upload_docs)
            st.session_state.chat_history = chat(st.session_state.chat_history, st.session_state.vectordb, GOOGLE_API_KEY)

        # Блокировка чата до загрузки документа
        if not self.docs_files and not st.session_state.uploaded_pdfs:
            st.info("Загрузите PDF-файл, чтобы начать с ним общаться. Вы можете продолжать загружать файлы для общения, и если вам понадобится уйти, вам не придется загружать эти файлы снова.")

if __name__ == "__main__":
    app = ChatApp()
    app.run()