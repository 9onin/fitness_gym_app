import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Загрузка переменных из .env файла
load_dotenv()

# Получение настроек из переменных окружения
smtp_server = os.environ.get('MAIL_SERVER')
smtp_port = int(os.environ.get('MAIL_PORT', 465))
use_tls = os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', 'yes', '1')
use_ssl = os.environ.get('MAIL_USE_SSL', 'True').lower() in ('true', 'yes', '1')
username = os.environ.get('MAIL_USERNAME')
password = os.environ.get('MAIL_PASSWORD')
sender = os.environ.get('MAIL_DEFAULT_SENDER')

# Создание сообщения
msg = MIMEMultipart()
msg['From'] = sender
msg['To'] = username  # Отправляем тестовое письмо самому себе
msg['Subject'] = 'Тестовое письмо из Python'
body = 'Это тестовое письмо для проверки настроек SMTP сервера Yandex.'
msg.attach(MIMEText(body, 'plain'))

print(f"Настройки подключения:")
print(f"SMTP сервер: {smtp_server}")
print(f"Порт: {smtp_port}")
print(f"TLS: {use_tls}")
print(f"SSL: {use_ssl}")
print(f"Пользователь: {username}")
print(f"Отправитель: {sender}")

try:
    # Выбор типа подключения (SSL или TLS)
    if use_ssl:
        print("Используем SSL подключение")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    else:
        print("Используем обычное подключение с TLS")
        server = smtplib.SMTP(smtp_server, smtp_port)
        if use_tls:
            server.starttls()
    
    # Вывод информации о подключении
    server.set_debuglevel(1)
    
    # Авторизация на сервере
    print("Выполняем вход...")
    server.login(username, password)
    
    # Отправка письма
    print("Отправляем письмо...")
    text = msg.as_string()
    server.sendmail(sender, username, text)
    
    # Закрытие соединения
    server.quit()
    print("Письмо успешно отправлено!")
    
except Exception as e:
    print(f"Ошибка при отправке письма: {e}") 