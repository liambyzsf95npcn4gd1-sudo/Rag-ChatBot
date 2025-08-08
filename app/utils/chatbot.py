# -*- coding: utf-8 -*-
"""
Модуль для реализации функциональности чат-бота.

Этот модуль содержит функции для создания цепочки ретривера,
получения ответов от модели и управления ходом чата в приложении Streamlit.
"""

import streamlit as st
from collections import defaultdict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import logging

def get_context_retriever_chain(vectordb, google_api_key):
    """
    Создает цепочку ретривера для генерации ответов на основе истории чата и векторной базы данных.

    Args:
        vectordb: Векторная база данных, используемая для извлечения контекста.
        google_api_key (str): API-ключ для доступа к Google Generative AI.

    Returns:
        retrieval_chain: Цепочка ретривера для генерации ответов.
    """
    # Инициализация модели, ретривера и шаблона для чат-бота
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=google_api_key, temperature=0.2, convert_system_message_to_human=True)
    retriever = vectordb.as_retriever()

    # Шаблон промпта, который определяет поведение чат-бота
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Вы — чат-бот. Вы получите промпт, включающий историю чата и извлеченный контент из векторной базы данных на основе вопроса пользователя. Ваша задача — ответить на вопрос пользователя, используя информацию из векторной базы данных, как можно меньше полагаясь на собственные знания. Если по какой-то причине вы не знаете ответа на вопрос или на вопрос нельзя ответить из-за отсутствия контекста, попросите пользователя предоставить больше деталей. Не придумывайте ответ. Отвечайте на вопросы, используя следующий контекст: {context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    # Создание цепочки для генерации ответов и цепочки ретривера
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retrieval_chain = create_retrieval_chain(retriever, chain)
    return retrieval_chain

def get_response(question, chat_history, vectordb, google_api_key):
    """
    Генерирует ответ на вопрос пользователя на основе истории чата и векторной базы данных.

    Args:
        question (str): Вопрос пользователя.
        chat_history (list): Список предыдущих сообщений в чате.
        vectordb: Векторная база данных, используемая для извлечения контекста.
        google_api_key (str): API-ключ для доступа к Google Generative AI.

    Returns:
        tuple: Кортеж, содержащий сгенерированный ответ и контекст, использованный для ответа.
    """
    try:
        chain = get_context_retriever_chain(vectordb, google_api_key)
        response = chain.invoke({"input": question, "chat_history": chat_history})
        return response["answer"], response["context"]
    except Exception as e:
        logging.exception("Ошибка LLM")
        return f"Ошибка при получении ответа от LLM: {e}", []

def chat(chat_history, vectordb, google_api_key):
    """
    Обрабатывает функциональность чата в приложении.

    Args:
        chat_history (list): Список предыдущих сообщений в чате.
        vectordb: Векторная база данных, используемая для извлечения контекста.
        google_api_key (str): API-ключ для доступа к Google Generative AI.

    Returns:
        list: Обновленная история чата.
    """
    user_query = st.chat_input("Задайте вопрос:")
    if user_query is not None and user_query != "":
        logging.info(f"Запрос пользователя: {user_query}")

        # Генерация ответа на основе запроса пользователя, истории чата и векторного хранилища
        response, context = get_response(user_query, chat_history, vectordb, google_api_key)

        # Обновление истории чата. Модель использует до 10 предыдущих сообщений для формирования ответа.
        chat_history = chat_history + [HumanMessage(content=user_query), AIMessage(content=response)]

        # Отображение источника ответа на боковой панели
        with st.sidebar:
                metadata_dict = defaultdict(list)
                for metadata in [doc.metadata for doc in context]:
                    metadata_dict[metadata['source']].append(metadata['page'])
                for source, pages in metadata_dict.items():
                    st.write(f"Источник: {source}")
                    st.write(f"Страницы: {', '.join(map(str, pages))}")

    # Отображение истории чата
    for message in chat_history:
            with st.chat_message("AI" if isinstance(message, AIMessage) else "Human"):
                st.write(message.content)
    return chat_history