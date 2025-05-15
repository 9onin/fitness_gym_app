from flask import current_app
from flask_mail import Message, Mail
from datetime import datetime, timedelta
from models.models import User, Workout, Booking
from models.database import db
import logging

# Инициализация объекта для отправки электронной почты
mail = Mail()

def init_mail(app):
    """
    Инициализирует почтовый сервис с приложением Flask
    """
    mail.init_app(app)

def send_email(to, subject, template):
    """
    Отправляет электронное письмо пользователю
    
    Args:
        to (str): Email получателя
        subject (str): Тема письма
        template (str): HTML шаблон письма
    """
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    try:
        # Проверяем, включена ли отправка писем в конфигурации
        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            current_app.logger.info(f"Email sending suppressed: {subject} to {to}")
            return True
            
        # Проверяем, настроены ли учетные данные для отправки писем
        if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
            current_app.logger.warning("Email credentials not configured. Skipping email send.")
            return False
        
        # Логируем текущие настройки почтового сервера
        current_app.logger.info(f"Attempting to send email using: " 
                               f"SERVER={current_app.config.get('MAIL_SERVER')}, "
                               f"PORT={current_app.config.get('MAIL_PORT')}, "
                               f"TLS={current_app.config.get('MAIL_USE_TLS')}, "
                               f"SSL={current_app.config.get('MAIL_USE_SSL')}")
            
        mail.send(msg)
        current_app.logger.info(f"Email sent: {subject} to {to}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        current_app.logger.error(f"Email configuration: "
                                f"SERVER={current_app.config.get('MAIL_SERVER')}, "
                                f"PORT={current_app.config.get('MAIL_PORT')}, "
                                f"TLS={current_app.config.get('MAIL_USE_TLS')}, "
                                f"SSL={current_app.config.get('MAIL_USE_SSL')}, "
                                f"USERNAME={current_app.config.get('MAIL_USERNAME')}")
        return False

def send_booking_confirmation(user, workout):
    """
    Отправляет подтверждение бронирования тренировки
    
    Args:
        user (User): Объект пользователя
        workout (Workout): Объект тренировки
    """
    subject = "Подтверждение записи на тренировку"
    
    # Форматирование даты и времени
    start_time = workout.start_time.strftime('%d.%m.%Y %H:%M')
    end_time = workout.end_time.strftime('%H:%M')
    
    template = f"""
    <h2>Подтверждение записи на тренировку</h2>
    <p>Здравствуйте, {user.first_name}!</p>
    <p>Вы успешно записались на тренировку:</p>
    <ul>
        <li><strong>Тип тренировки:</strong> {workout.workout_type.name}</li>
        <li><strong>Тренер:</strong> {workout.trainer.first_name} {workout.trainer.last_name}</li>
        <li><strong>Дата и время:</strong> {start_time} - {end_time}</li>
    </ul>
    <p>Если у вас возникнут вопросы или вам нужно отменить запись, пожалуйста, сделайте это в личном кабинете.</p>
    <p>С уважением,<br>Команда фитнес сети</p>
    """
    
    # Игнорируем результат отправки, чтобы не блокировать запись на тренировку
    send_email(user.email, subject, template)

def send_schedule_update_notification(user, workout, is_cancelled=False):
    """
    Отправляет уведомление об изменении в расписании тренировки
    
    Args:
        user (User): Объект пользователя
        workout (Workout): Объект тренировки
        is_cancelled (bool): Флаг отмены тренировки
    """
    if is_cancelled:
        subject = "Отмена тренировки"
        
        # Форматирование даты и времени
        start_time = workout.start_time.strftime('%d.%m.%Y %H:%M')
        
        template = f"""
        <h2>Отмена тренировки</h2>
        <p>Здравствуйте, {user.first_name}!</p>
        <p>К сожалению, мы вынуждены сообщить вам, что следующая тренировка была отменена:</p>
        <ul>
            <li><strong>Тип тренировки:</strong> {workout.workout_type.name}</li>
            <li><strong>Тренер:</strong> {workout.trainer.first_name} {workout.trainer.last_name}</li>
            <li><strong>Дата и время:</strong> {start_time}</li>
        </ul>
        <p>Приносим свои извинения за доставленные неудобства.</p>
        <p>С уважением,<br>Команда фитнес сети</p>
        """
    else:
        subject = "Изменения в расписании"
        
        # Форматирование даты и времени
        start_time = workout.start_time.strftime('%d.%m.%Y %H:%M')
        end_time = workout.end_time.strftime('%H:%M')
        
        template = f"""
        <h2>Изменения в расписании</h2>
        <p>Здравствуйте, {user.first_name}!</p>
        <p>Обращаем ваше внимание на изменения в расписании тренировки, на которую вы записаны:</p>
        <ul>
            <li><strong>Тип тренировки:</strong> {workout.workout_type.name}</li>
            <li><strong>Тренер:</strong> {workout.trainer.first_name} {workout.trainer.last_name}</li>
            <li><strong>Новое время:</strong> {start_time} - {end_time}</li>
        </ul>
        <p>Если у вас возникнут вопросы или новое время вам не подходит, вы можете отменить запись в личном кабинете.</p>
        <p>С уважением,<br>Команда фитнес сети</p>
        """
    
    # Игнорируем результат отправки, чтобы не блокировать обновление расписания
    send_email(user.email, subject, template)

def send_upcoming_workout_reminder():
    """
    Отправляет напоминания о предстоящих тренировках
    Эта функция должна вызываться по расписанию (например, через планировщик задач)
    """
    # Получаем тренировки, которые состоятся через 24 часа
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    upcoming_bookings = Booking.query.join(Workout).filter(
        Workout.start_time >= start_time,
        Workout.start_time <= end_time
    ).all()
    
    sent_count = 0
    error_count = 0
    
    for booking in upcoming_bookings:
        user = booking.user
        workout = booking.workout
        
        subject = "Напоминание о тренировке"
        
        # Форматирование даты и времени
        start_time = workout.start_time.strftime('%d.%m.%Y %H:%M')
        end_time = workout.end_time.strftime('%H:%M')
        
        template = f"""
        <h2>Напоминание о тренировке</h2>
        <p>Здравствуйте, {user.first_name}!</p>
        <p>Напоминаем вам, что завтра у вас запланирована тренировка:</p>
        <ul>
            <li><strong>Тип тренировки:</strong> {workout.workout_type.name}</li>
            <li><strong>Тренер:</strong> {workout.trainer.first_name} {workout.trainer.last_name}</li>
            <li><strong>Дата и время:</strong> {start_time} - {end_time}</li>
        </ul>
        <p>Будем рады видеть вас!</p>
        <p>С уважением,<br>Команда фитнес сети</p>
        """
        
        if send_email(user.email, subject, template):
            sent_count += 1
        else:
            error_count += 1
    
    current_app.logger.info(f"Sent {sent_count} workout reminders with {error_count} errors") 