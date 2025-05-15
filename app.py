import os
from flask import Flask, render_template, flash
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from models.database import db, init_db
from models.models import User
from services.notification_service import mail, init_mail
from datetime import datetime

# Загрузка переменных окружения из .env файла
load_dotenv()

def create_app(test_config=None):
    """
    Создает и настраивает экземпляр приложения Flask
    """
    app = Flask(__name__, 
              instance_relative_config=True,
              static_folder='static',
              template_folder='templates')
    
    # Настройка для работы за прокси
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Базовая конфигурация
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///fitness_gym.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.yandex.ru'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 465)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', 'yes', '1'),
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'True').lower() in ('true', 'yes', '1'),
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', ''),
        MAIL_SUPPRESS_SEND=os.environ.get('MAIL_SUPPRESS_SEND', 'True').lower() in ('true', 'yes', '1'),
    )
    
    # Настраиваем логгер
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Создаем директорию для логов если она не существует
        os.makedirs('logs', exist_ok=True)
        
        file_handler = RotatingFileHandler('logs/fitness_gym.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Fitness Gym startup')
    
    # Применяем тестовую конфигурацию, если она предоставлена
    if test_config is not None:
        app.config.from_mapping(test_config)
    
    # Инициализируем базу данных
    init_db(app)
    
    # Инициализируем почтовый сервис
    init_mail(app)
    
    # Инициализируем Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        Загружает пользователя из базы данных по его ID
        """
        return User.query.get(int(user_id))
    
    # Регистрируем блюпринты
    from controllers.main import main_bp
    from controllers.auth import auth_bp
    from controllers.user import user_bp
    from controllers.admin import admin_bp
    from controllers.analytics import analytics_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Обработчик ошибки 404
    @app.errorhandler(404)
    def page_not_found(e):
        """
        Обработчик ошибки 404 (страница не найдена)
        """
        return render_template('errors/404.html'), 404
    
    # Обработчик ошибки 403
    @app.errorhandler(403)
    def forbidden(e):
        """
        Обработчик ошибки 403 (доступ запрещен)
        """
        return render_template('errors/403.html'), 403
    
    # Обработчик ошибки 500
    @app.errorhandler(500)
    def internal_server_error(e):
        """
        Обработчик ошибки 500 (внутренняя ошибка сервера)
        """
        return render_template('errors/500.html'), 500
    
    # Создаем instance директорию, если она не существует
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Add utility functions for templates
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 