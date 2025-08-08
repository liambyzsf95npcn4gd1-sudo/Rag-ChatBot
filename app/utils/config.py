# -*- coding: utf-8 -*-
"""
Модуль конфигурации.

Этот модуль загружает переменные окружения из файла .env
и предоставляет их для использования в других частях приложения.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# API-ключ для доступа к сервисам Google
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Параметры SMTP-сервера для отправки электронной почты
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Email менеджера для получения уведомлений
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL")

# Директория для хранения данных ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
