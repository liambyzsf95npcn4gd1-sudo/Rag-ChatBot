# -*- coding: utf-8 -*-
"""
Модуль для отправки электронной почты.

Этот модуль содержит функцию для отправки электронных писем
с использованием SMTP-сервера.
"""

import os
import logging
import smtplib
from email.message import EmailMessage

# Настройка логгера для этого модуля
logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, to_emails: list, from_email: str = None, attachments: list = None):
    """
    Отправляет электронное письмо.

    Args:
        subject (str): Тема письма.
        body (str): Тело письма.
        to_emails (list): Список email-адресов получателей.
        from_email (str, optional): Email-адрес отправителя. Если не указан, используется SMTP_USER.
        attachments (list, optional): Список вложений. Каждое вложение - это кортеж (имя, данные, mime-тип).

    Raises:
        RuntimeError: Если конфигурация SMTP неполная.
        Exception: Если не удалось отправить письмо или прикрепить файл.
    """
    # Загрузка конфигурации SMTP из переменных окружения
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    # Проверка полноты конфигурации SMTP
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        logger.error("Конфигурация SMTP неполная")
        raise RuntimeError("Конфигурация SMTP неполная")

    # Создание объекта сообщения
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email or SMTP_USER
    msg["To"] = ", ".join(to_emails if isinstance(to_emails, (list,tuple)) else [to_emails])
    msg.set_content(body)

    # Добавление вложений, если они есть
    if attachments:
        for name, data, mime in attachments:
            try:
                maintype, subtype = mime.split("/")
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
            except Exception:
                logger.exception("Не удалось прикрепить файл")
                raise

    # Отправка письма через SMTP-сервер
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            # Использование TLS для защищенного соединения
            if SMTP_PORT == 587:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
            logger.info(f"Письмо отправлено на {msg['To']}")
    except Exception:
        logger.exception("Отправка письма не удалась")
        raise
