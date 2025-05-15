from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Инициализация объекта базы данных
db = SQLAlchemy()

def init_db(app):
    """
    Инициализирует базу данных
    """
    db.init_app(app)
    
    # Создаем все таблицы в базе данных
    with app.app_context():
        db.create_all() 