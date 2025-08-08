import pytest
import os
from unittest.mock import patch, MagicMock
from app.utils.send_email import send_email

@pytest.fixture
def smtp_env_vars(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASS", "password")

@patch('smtplib.SMTP')
def test_send_email_success(mock_smtp, smtp_env_vars):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    send_email(
        subject="Test Subject",
        body="Test Body",
        to_emails=["recipient@example.com"]
    )

    mock_smtp.assert_called_with("smtp.example.com", 587, timeout=30)
    mock_smtp_instance.ehlo.assert_called()
    mock_smtp_instance.starttls.assert_called()
    mock_smtp_instance.login.assert_called_with("user@example.com", "password")
    mock_smtp_instance.send_message.assert_called_once()

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Test Subject"
    assert sent_msg["To"] == "recipient@example.com"
    assert sent_msg["From"] == "user@example.com"
    assert sent_msg.get_content().strip() == "Test Body"

def test_send_email_missing_config():
    with pytest.raises(RuntimeError, match="SMTP configuration incomplete"):
        send_email(subject="Test", body="Test", to_emails=["test@test.com"])
