from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from models.models import Workout, Booking, WorkoutType
from models.database import db
from forms.booking_forms import BookingForm
from datetime import datetime, timedelta
from services.notification_service import send_booking_confirmation

# Создание блюпринта для пользовательских маршрутов
user_bp = Blueprint('user', __name__)

@user_bp.route('/schedule')
@login_required
def schedule():
    """
    Обработчик маршрута расписания пользователя
    """
    # Получаем текущую дату
    today = datetime.now().date()
    
    # Получаем будущие записи пользователя
    future_bookings = Booking.query.join(Workout).filter(
        Booking.user_id == current_user.id,
        Workout.start_time >= today
    ).order_by(Workout.start_time).all()
    
    # Получаем прошедшие записи пользователя
    past_bookings = Booking.query.join(Workout).filter(
        Booking.user_id == current_user.id,
        Workout.start_time < today
    ).order_by(Workout.start_time.desc()).all()
    
    return render_template('user/schedule.html', 
                         title='Моё расписание',
                         future_bookings=future_bookings,
                         past_bookings=past_bookings)

@user_bp.route('/workouts')
@login_required
def workouts():
    """
    Обработчик маршрута просмотра доступных тренировок
    """
    # Получаем параметр фильтра по типу тренировки
    workout_type_id = request.args.get('type', type=int)
    
    # Базовый запрос на получение будущих тренировок
    base_query = Workout.query.filter(Workout.start_time >= datetime.now())
    
    # Применяем фильтр, если он есть
    if workout_type_id:
        base_query = base_query.filter(Workout.workout_type_id == workout_type_id)
    
    # Получаем тренировки, сортируя по дате начала
    workouts = base_query.order_by(Workout.start_time).all()
    
    # Получаем все типы тренировок для фильтра
    workout_types = WorkoutType.query.all()
    
    return render_template('user/workouts.html',
                         title='Доступные тренировки',
                         workouts=workouts,
                         workout_types=workout_types,
                         selected_type=workout_type_id)

@user_bp.route('/book/<int:workout_id>', methods=['GET', 'POST'])
@login_required
def book_workout(workout_id):
    """
    Обработчик маршрута записи на тренировку
    """
    workout = Workout.query.get_or_404(workout_id)
    
    # Проверяем, не записан ли пользователь уже на эту тренировку
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        workout_id=workout.id
    ).first()
    
    if existing_booking:
        flash('Вы уже записаны на эту тренировку', 'warning')
        return redirect(url_for('user.workouts'))
    
    # Проверяем, есть ли свободные места
    if workout.is_full:
        flash('На данную тренировку не осталось свободных мест', 'danger')
        return redirect(url_for('user.workouts'))
    
    form = BookingForm()
    
    if form.validate_on_submit():
        # Создаем новую запись
        booking = Booking(
            user_id=current_user.id,
            workout_id=workout.id
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Отправляем уведомление о записи
        send_booking_confirmation(current_user, workout)
        
        flash('Вы успешно записались на тренировку', 'success')
        return redirect(url_for('user.schedule'))
    
    return render_template('user/book_workout.html',
                         title='Запись на тренировку',
                         form=form,
                         workout=workout)

@user_bp.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Обработчик маршрута отмены записи на тренировку
    """
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем, принадлежит ли запись текущему пользователю
    if booking.user_id != current_user.id:
        flash('У вас нет прав для отмены этой записи', 'danger')
        return redirect(url_for('user.schedule'))
    
    # Проверяем, не прошла ли уже тренировка
    if booking.workout.start_time < datetime.now():
        flash('Невозможно отменить запись на прошедшую тренировку', 'danger')
        return redirect(url_for('user.schedule'))
    
    # Удаляем запись
    db.session.delete(booking)
    db.session.commit()
    
    flash('Запись на тренировку успешно отменена', 'success')
    return redirect(url_for('user.schedule')) 