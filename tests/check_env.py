from dotenv import load_dotenv
import os

# Загрузка переменных из .env файла
print("Загружаем переменные окружения из .env файла...")
load_dotenv()

# Проверка загруженных переменных
print("\nНастройки почтового сервера:")
print(f"MAIL_SERVER = {os.environ.get('MAIL_SERVER', 'Не установлено')}")
print(f"MAIL_PORT = {os.environ.get('MAIL_PORT', 'Не установлено')}")
print(f"MAIL_USE_TLS = {os.environ.get('MAIL_USE_TLS', 'Не установлено')}")
print(f"MAIL_USE_SSL = {os.environ.get('MAIL_USE_SSL', 'Не установлено')}")
print(f"MAIL_USERNAME = {os.environ.get('MAIL_USERNAME', 'Не установлено')}")
print(f"MAIL_PASSWORD = {'*' * len(os.environ.get('MAIL_PASSWORD', '')) if os.environ.get('MAIL_PASSWORD') else 'Не установлено'}")
print(f"MAIL_DEFAULT_SENDER = {os.environ.get('MAIL_DEFAULT_SENDER', 'Не установлено')}")
print(f"MAIL_SUPPRESS_SEND = {os.environ.get('MAIL_SUPPRESS_SEND', 'Не установлено')}")

# Проверка других переменных
print("\nДругие переменные:")
print(f"SECRET_KEY = {'*' * len(os.environ.get('SECRET_KEY', '')) if os.environ.get('SECRET_KEY') else 'Не установлено'}")
print(f"DATABASE_URI = {os.environ.get('DATABASE_URI', 'Не установлено')}")

# Проверка пути к .env файлу
import pathlib
current_dir = pathlib.Path().absolute()
env_file = current_dir / '.env'
print(f"\nТекущий рабочий каталог: {current_dir}")
print(f"Путь к .env файлу: {env_file}")
print(f"Файл .env существует: {env_file.exists()}")

if env_file.exists():
    print("\nСодержимое файла .env (первые 5 строк):")
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:5]):
                # Скрываем пароли в выводе
                if 'PASSWORD' in line:
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        line = f"{parts[0]}={'*' * len(parts[1].strip())}"
                print(f"{i+1}: {line.strip()}")
            if len(lines) > 5:
                print("...")
    except Exception as e:
        print(f"Ошибка при чтении .env файла: {e}") 