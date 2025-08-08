# -*- coding: utf-8 -*-
"""
Тесты для модуля отправки электронной почты.

Этот файл содержит тесты для функции `send_email` из модуля `app.utils.send_email`.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from app.utils.send_email import send_email

@pytest.fixture
def smtp_env_vars(monkeypatch):
    """
    Фикстура для установки переменных окружения SMTP.
    Использует `monkeypatch` для временной установки переменных на время теста.
    """
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASS", "password")

@patch('smtplib.SMTP')
def test_send_email_success(mock_smtp, smtp_env_vars):
    """
    Тестирует успешную отправку письма.
    Использует `patch` для мокирования `smtplib.SMTP`, чтобы избежать реальной отправки.
    Проверяет, что все методы SMTP вызываются с правильными аргументами.
    """
    # Создаем мок-экземпляр SMTP
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    # Вызываем функцию отправки письма
    send_email(
        subject="Test Subject",
        body="Test Body",
        to_emails=["recipient@example.com"]
    )

    # Проверяем, что конструктор SMTP был вызван с правильными параметрами
    mock_smtp.assert_called_with("smtp.example.com", 587, timeout=30)
    # Проверяем вызовы методов для установки соединения и аутентификации
    mock_smtp_instance.ehlo.assert_called()
    mock_smtp_instance.starttls.assert_called()
    mock_smtp_instance.login.assert_called_with("user@example.com", "password")
    # Проверяем, что метод отправки сообщения был вызван один раз
    mock_smtp_instance.send_message.assert_called_once()

    # Проверяем содержимое отправленного сообщения
    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Test Subject"
    assert sent_msg["To"] == "recipient@example.com"
    assert sent_msg["From"] == "user@example.com"
    assert sent_msg.get_content().strip() == "Test Body"

def test_send_email_missing_config():
    """
    Тестирует поведение функции при отсутствующей конфигурации SMTP.
    Проверяет, что возбуждается исключение `RuntimeError`.
    """
    with pytest.raises(RuntimeError, match="SMTP configuration incomplete"):
        send_email(subject="Test", body="Test", to_emails=["test@test.com"])
