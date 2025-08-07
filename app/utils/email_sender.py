import os
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

def sanitize_input(text):
    """Removes newlines and other control characters from a string."""
    return re.sub(r'[\r\n\t]', '', text).strip()

def send_order_email(name, client_email, order_file_name, order_file_content):
    """
    Sends two emails: one to the manager with the order details and attachment,
    and a confirmation to the client. Inputs are sanitized.

    Returns:
        bool: True if emails were sent successfully, False otherwise.
        str: A message indicating success or failure.
    """
    # Sanitize all string inputs as a security measure
    name = sanitize_input(name)
    client_email = sanitize_input(client_email)
    order_file_name = sanitize_input(order_file_name)

    load_dotenv()

    # Load SMTP configuration from .env file
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    manager_email = os.getenv("MANAGER_EMAIL")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, manager_email]):
        error_msg = "Ошибка: Конфигурация SMTP не задана в .env файле."
        print(error_msg)
        return False, error_msg

    try:
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)

        # --- Email to Manager ---
        msg_manager = MIMEMultipart()
        msg_manager['From'] = smtp_user
        msg_manager['To'] = manager_email
        msg_manager['Subject'] = f"Новый заказ от {name}"

        body_manager = f"""
Здравствуйте,

Поступил новый заказ.

Данные клиента:
- Имя: {name}
- Email: {client_email}

Файл с деталями заказа прикреплен к этому письму.
"""
        msg_manager.attach(MIMEText(body_manager, 'plain'))

        # Attach the order file
        attachment = MIMEApplication(order_file_content, Name=order_file_name)
        attachment['Content-Disposition'] = f'attachment; filename="{order_file_name}"'
        msg_manager.attach(attachment)

        server.send_message(msg_manager)

        # --- Email to Client ---
        msg_client = MIMEMultipart()
        msg_client['From'] = smtp_user
        msg_client['To'] = client_email
        msg_client['Subject'] = "Ваш заказ получен"

        body_client = f"""
Уважаемый(ая) {name},

Ваш заказ был успешно получен и передан в обработку.
Мы скоро свяжемся с вами для уточнения деталей.

Спасибо за ваш заказ!
"""
        msg_client.attach(MIMEText(body_client, 'plain'))

        server.send_message(msg_client)

        server.quit()

        success_msg = "Письма успешно отправлены."
        return True, success_msg

    except Exception as e:
        error_msg = f"Ошибка при отправке письма: {e}"
        print(error_msg)
        return False, error_msg
