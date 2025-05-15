from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from models.models import Workout, Booking, Trainer, WorkoutType, User
from models.database import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, case, select
from controllers.admin import admin_required
from services.report_service import generate_pdf_report, generate_excel_report
import calendar
import io
import os

# Создание блюпринта для аналитики
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard')
@login_required
@admin_required
def analytics_dashboard():
    """
    Обработчик маршрута панели аналитики
    """
    return render_template('admin/analytics/dashboard.html', title='Аналитика')

@analytics_bp.route('/workout-popularity')
@login_required
@admin_required
def workout_popularity():
    """
    Обработчик маршрута просмотра популярности тренировок (using subquery approach)
    """
    days = request.args.get('days', 30, type=int)
    query_start_date = datetime.now() - timedelta(days=days)
    query_end_date = datetime.now()

    # Subquery to get workouts within the date range
    workouts_in_range_sq = (
        select(Workout.id.label("workout_id"), Workout.workout_type_id)
        .where(Workout.start_time >= query_start_date)
        .where(Workout.start_time < query_end_date)
        .subquery('workouts_in_range') # Naming the subquery for clarity
    )

    workout_type_stats = (
        db.session.query(
            WorkoutType.name,
            func.count(Booking.id).label('booking_count')
        )
        .select_from(WorkoutType) # Explicitly start from WorkoutType
        .outerjoin(workouts_in_range_sq, WorkoutType.id == workouts_in_range_sq.c.workout_type_id)
        .outerjoin(Booking, Booking.workout_id == workouts_in_range_sq.c.workout_id)
        .group_by(WorkoutType.name)
        .order_by(desc('booking_count'))
        .all()
    )

    workout_types_labels = [item[0] for item in workout_type_stats]
    booking_counts_values = [item[1] for item in workout_type_stats]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'labels': workout_types_labels,
            'data': booking_counts_values
        })

    return render_template('admin/analytics/workout_popularity.html',
                         title='Популярность тренировок',
                         workout_type_stats=workout_type_stats,
                         days=days)

@analytics_bp.route('/trainer-workload')
@login_required
@admin_required
def trainer_workload():
    """
    Обработчик маршрута просмотра загруженности тренеров
    """
    # Период анализа (по умолчанию - текущий месяц)
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Определяем начало и конец месяца
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Получаем статистику по загруженности тренеров с корректным расчетом часов
    # используя outerjoin для показа всех тренеров
    trainer_stats = db.session.query(
        Trainer.first_name,
        Trainer.last_name,
        func.sum(
            func.extract('epoch', Workout.end_time) - func.extract('epoch', Workout.start_time)
        ).label('total_seconds')
    ).outerjoin(
        Workout, and_(
            Workout.trainer_id == Trainer.id,
            Workout.start_time >= start_date,
            Workout.start_time < end_date
        )
    ).group_by(Trainer.id, Trainer.first_name, Trainer.last_name) \
     .order_by(desc('total_seconds')) \
     .all()
    
    # Преобразуем секунды в часы и обеспечиваем отсутствие отрицательных значений
    processed_stats = []
    for item in trainer_stats:
        first_name = item[0]
        last_name = item[1]
        total_seconds = item[2] if item[2] is not None else 0
        # Преобразуем секунды в часы и округляем до 2 знаков
        total_hours = max(0, round(total_seconds / 3600, 2))
        processed_stats.append((first_name, last_name, total_hours))
    
    # Преобразуем для удобства использования в шаблоне и JSON
    trainer_names = [f"{item[0]} {item[1]}" for item in processed_stats]
    total_hours = [item[2] for item in processed_stats]
    
    # Получаем список всех месяцев для селектора
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    # Если запрос на получение JSON данных
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'labels': trainer_names,
            'data': total_hours
        })
    
    return render_template('admin/analytics/trainer_workload.html',
                         title='Загруженность тренеров',
                         trainer_stats=processed_stats,
                         months=months,
                         selected_month=month,
                         selected_year=year,
                         current_month_name=calendar.month_name[month])

@analytics_bp.route('/attendance')
@login_required
@admin_required
def attendance():
    """
    Обработчик маршрута просмотра посещаемости
    """
    # Период анализа (по умолчанию - последние 30 дней)
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    
    # Получаем данные о посещаемости с правильной логикой фильтрации по датам
    attendance_data = db.session.query(
        func.date(Workout.start_time).label('date'),
        func.count(Booking.id).label('booking_count'),
        func.sum(case((Booking.attended == True, 1), else_=0)).label('attended_count')
    ).join(
        Workout, and_(
            Booking.workout_id == Workout.id,
            Workout.start_time >= start_date, 
            Workout.start_time < end_date
        )
    ).group_by(func.date(Workout.start_time)) \
     .order_by('date') \
     .all()
    
    # Преобразуем для удобства использования в шаблоне и JSON
    # Проверяем тип данных и обрабатываем как datetime или строку соответственно
    dates = []
    for item in attendance_data:
        if hasattr(item[0], 'strftime'):  # Это объект datetime или date
            dates.append(item[0].strftime('%Y-%m-%d'))
        else:  # Это строка или другой тип
            dates.append(str(item[0]))
            
    booking_counts = [item[1] for item in attendance_data]
    attended_counts = [item[2] if item[2] is not None else 0 for item in attendance_data]
    
    # Рассчитываем процент посещаемости
    attendance_rates = []
    for booked, attended in zip(booking_counts, attended_counts):
        if booked > 0:
            rate = (attended / booked) * 100
        else:
            rate = 0
        attendance_rates.append(round(rate, 2))
    
    # Если запрос на получение JSON данных
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'labels': dates,
            'bookings': booking_counts,
            'attended': attended_counts,
            'rates': attendance_rates
        })
    
    return render_template('admin/analytics/attendance.html',
                         title='Посещаемость',
                         attendance_data=attendance_data,
                         days=days)

@analytics_bp.route('/generate-report', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_report():
    """
    Обработчик маршрута генерации отчёта
    """
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        data_type = request.form.get('data_type')
        format_type = request.form.get('format_type')
        
        # Период отчёта
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include the end day
        
        # Получаем данные в зависимости от типа отчёта и уровня детализации
        if data_type == 'workout_popularity':
            if report_type == 'summary':
                data = get_workout_popularity_summary(start_date, end_date)
                title = "Сводный отчет о популярности тренировок"
            else:
                data = get_workout_popularity_detailed(start_date, end_date)
                title = "Детальный отчет о популярности тренировок"
        elif data_type == 'trainer_workload':
            if report_type == 'summary':
                data = get_trainer_workload_summary(start_date, end_date)
                title = "Сводный отчет о загруженности тренеров"
            else:
                data = get_trainer_workload_detailed(start_date, end_date)
                title = "Детальный отчет о загруженности тренеров"
        elif data_type == 'attendance':
            if report_type == 'summary':
                data = get_attendance_summary(start_date, end_date)
                title = "Сводный отчет о посещаемости"
            else:
                data = get_attendance_detailed(start_date, end_date)
                title = "Детальный отчет о посещаемости"
        else:
            return jsonify({'error': 'Неверный тип данных'}), 400
        
        # Генерируем отчёт в зависимости от выбранного формата
        if format_type == 'pdf':
            report = generate_pdf_report(title, data, start_date, end_date)
            mimetype = 'application/pdf'
            file_ext = 'pdf'
        elif format_type == 'excel':
            report = generate_excel_report(title, data, start_date, end_date)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            file_ext = 'xlsx'
        else:
            return jsonify({'error': 'Неверный формат отчёта'}), 400
        
        # Отправляем файл клиенту
        filename = f"{data_type}_{report_type}_{start_date_str}_to_{end_date_str}.{file_ext}"
        return send_file(
            io.BytesIO(report),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    
    # Для GET запроса просто отображаем форму
    return render_template('admin/analytics/generate_report.html',
                         title='Создание отчёта',
                         now=datetime.now,
                         timedelta=timedelta)

# Вспомогательные функции для получения данных отчётов

def get_workout_popularity_summary(start_date, end_date):
    """
    Получает сводные данные о популярности тренировок за указанный период
    """
    # Subquery to get workouts within the date range
    workouts_in_range_sq = (
        select(Workout.id.label("workout_id"), Workout.workout_type_id)
        .where(Workout.start_time >= start_date)
        .where(Workout.start_time < end_date)
        .subquery('workouts_in_range_report')
    )

    workout_type_stats_rows = (
        db.session.query(
            WorkoutType.name,
            func.count(Booking.id).label('booking_count')
        )
        .select_from(WorkoutType)
        .outerjoin(workouts_in_range_sq, WorkoutType.id == workouts_in_range_sq.c.workout_type_id)
        .outerjoin(Booking, Booking.workout_id == workouts_in_range_sq.c.workout_id)
        .group_by(WorkoutType.name)
        .order_by(desc('booking_count'))
        .all()
    )
    
    # Вычисляем общее количество записей
    total_bookings = sum(row[1] for row in workout_type_stats_rows)
    
    # Добавляем процент от общего количества записей
    processed_rows = []
    for row in workout_type_stats_rows:
        workout_type = row[0]
        booking_count = row[1]
        percentage = round((booking_count / total_bookings * 100 if total_bookings > 0 else 0), 2)
        processed_rows.append((workout_type, booking_count, f"{percentage}%"))

    return {
        'headers': ['Тип тренировки', 'Количество записей', 'Процент от общего'],
        'rows': processed_rows
    }

def get_workout_popularity_detailed(start_date, end_date):
    """
    Получает детальные данные о популярности тренировок за указанный период
    """
    # Получаем данные о записях на тренировки по дням
    detailed_data = db.session.query(
        func.date(Workout.start_time).label('date'),
        WorkoutType.name,
        Trainer.first_name,
        Trainer.last_name,
        func.count(Booking.id).label('booking_count')
    ).join(
        Workout, Booking.workout_id == Workout.id
    ).join(
        WorkoutType, Workout.workout_type_id == WorkoutType.id
    ).join(
        Trainer, Workout.trainer_id == Trainer.id
    ).filter(
        Workout.start_time >= start_date,
        Workout.start_time < end_date
    ).group_by(
        func.date(Workout.start_time),
        WorkoutType.name,
        Trainer.first_name,
        Trainer.last_name
    ).order_by(
        func.date(Workout.start_time),
        WorkoutType.name
    ).all()
    
    processed_rows = []
    for row in detailed_data:
        # Форматируем дату
        if hasattr(row[0], 'strftime'):
            date_str = row[0].strftime('%d.%m.%Y')
        else:
            date_str = str(row[0])
            
        workout_type = row[1]
        trainer_name = f"{row[2]} {row[3]}"
        booking_count = row[4]
        
        processed_rows.append((date_str, workout_type, trainer_name, booking_count))
    
    return {
        'headers': ['Дата', 'Тип тренировки', 'Тренер', 'Количество записей'],
        'rows': processed_rows
    }

def get_trainer_workload_summary(start_date, end_date):
    """
    Получает сводные данные о загруженности тренеров за указанный период
    """
    trainer_stats = db.session.query(
        Trainer.first_name,
        Trainer.last_name,
        func.sum(
            func.extract('epoch', Workout.end_time) - func.extract('epoch', Workout.start_time)
        ).label('total_seconds'),
        func.count(Workout.id).label('workout_count')
    ).outerjoin(
        Workout, and_(
            Workout.trainer_id == Trainer.id, 
            Workout.start_time >= start_date,
            Workout.start_time < end_date
        )
    ).group_by(Trainer.id, Trainer.first_name, Trainer.last_name) \
     .order_by(desc('total_seconds')) \
     .all()
    
    # Преобразуем секунды в часы и добавляем дополнительную информацию
    processed_rows = []
    total_hours_all = 0
    
    for row in trainer_stats:
        first_name = row[0]
        last_name = row[1]
        total_seconds = row[2] if row[2] is not None else 0
        workout_count = row[3] if row[3] is not None else 0
        
        # Преобразуем секунды в часы и округляем до 2 знаков
        total_hours = max(0, round(total_seconds / 3600, 2))
        total_hours_all += total_hours
        
        # Средняя продолжительность тренировки в часах
        avg_hours_per_workout = round(total_hours / workout_count, 2) if workout_count > 0 else 0
        
        processed_rows.append((
            f"{first_name} {last_name}", 
            total_hours, 
            workout_count, 
            avg_hours_per_workout
        ))
    
    # Вычисляем процент от общей нагрузки для каждого тренера
    final_rows = []
    for row in processed_rows:
        trainer_name = row[0]
        hours = row[1]
        workout_count = row[2]
        avg_duration = row[3]
        
        # Процент от общей нагрузки
        workload_percentage = round((hours / total_hours_all * 100) if total_hours_all > 0 else 0, 2)
        
        final_rows.append((
            trainer_name,
            hours,
            f"{workload_percentage}%",
            workout_count,
            avg_duration
        ))
    
    return {
        'headers': ['Тренер', 'Общая нагрузка (ч)', 'Доля от общей нагрузки', 'Количество тренировок', 'Средняя длительность (ч)'],
        'rows': final_rows
    }

def get_trainer_workload_detailed(start_date, end_date):
    """
    Получает детальные данные о загруженности тренеров за указанный период
    """
    trainer_daily_stats = db.session.query(
        func.date(Workout.start_time).label('date'),
        Trainer.first_name,
        Trainer.last_name,
        WorkoutType.name,
        func.count(Workout.id).label('workout_count'),
        func.sum(
            func.extract('epoch', Workout.end_time) - func.extract('epoch', Workout.start_time)
        ).label('total_seconds')
    ).join(
        Trainer, Workout.trainer_id == Trainer.id
    ).join(
        WorkoutType, Workout.workout_type_id == WorkoutType.id
    ).filter(
        Workout.start_time >= start_date,
        Workout.start_time < end_date
    ).group_by(
        func.date(Workout.start_time),
        Trainer.first_name,
        Trainer.last_name,
        WorkoutType.name
    ).order_by(
        func.date(Workout.start_time),
        Trainer.last_name,
        Trainer.first_name
    ).all()
    
    processed_rows = []
    for row in trainer_daily_stats:
        if hasattr(row[0], 'strftime'):
            date_str = row[0].strftime('%d.%m.%Y')
        else:
            date_str = str(row[0])
            
        trainer_name = f"{row[1]} {row[2]}"
        workout_type = row[3]
        workout_count = row[4]
        hours = max(0, round(row[5] / 3600, 2)) if row[5] is not None else 0
        
        processed_rows.append((
            date_str,
            trainer_name,
            workout_type,
            workout_count,
            hours
        ))
    
    return {
        'headers': ['Дата', 'Тренер', 'Тип тренировки', 'Количество', 'Часы'],
        'rows': processed_rows
    }

def get_attendance_summary(start_date, end_date):
    """
    Получает сводные данные о посещаемости за указанный период
    """
    # Получаем агрегированные данные по типам тренировок
    attendance_by_type = db.session.query(
        WorkoutType.name,
        func.count(Booking.id).label('booking_count'),
        func.sum(case((Booking.attended == True, 1), else_=0)).label('attended_count')
    ).join(
        Workout, Booking.workout_id == Workout.id
    ).join(
        WorkoutType, Workout.workout_type_id == WorkoutType.id
    ).filter(
        Workout.start_time >= start_date,
        Workout.start_time < end_date
    ).group_by(
        WorkoutType.name
    ).order_by(
        desc('booking_count')
    ).all()
    
    # Общая статистика
    total_bookings = db.session.query(
        func.count(Booking.id),
        func.sum(case((Booking.attended == True, 1), else_=0))
    ).join(
        Workout, and_(
            Booking.workout_id == Workout.id,
            Workout.start_time >= start_date,
            Workout.start_time < end_date
        )
    ).first()
    
    # Количество уникальных клиентов
    unique_clients = db.session.query(
        func.count(func.distinct(Booking.user_id))
    ).join(
        Workout, and_(
            Booking.workout_id == Workout.id,
            Workout.start_time >= start_date,
            Workout.start_time < end_date
        )
    ).scalar()
    
    # Обработка данных по типам тренировок
    workout_type_rows = []
    for row in attendance_by_type:
        workout_type = row[0]
        booked = row[1]
        attended = row[2] if row[2] is not None else 0
        attendance_rate = round((attended / booked) * 100, 2) if booked > 0 else 0
        
        workout_type_rows.append((
            workout_type,
            booked,
            attended,
            f"{attendance_rate}%"
        ))
    
    # Добавляем строку с итогами
    total_booked = total_bookings[0] if total_bookings[0] is not None else 0
    total_attended = total_bookings[1] if total_bookings[1] is not None else 0
    total_rate = round((total_attended / total_booked) * 100, 2) if total_booked > 0 else 0
    
    workout_type_rows.append((
        "ИТОГО",
        total_booked,
        total_attended,
        f"{total_rate}%"
    ))
    
    # Добавляем информацию о количестве клиентов
    return {
        'headers': ['Тип тренировки', 'Записалось', 'Посетило', 'Процент посещаемости'],
        'rows': workout_type_rows,
        'summary': f"За указанный период услугами воспользовались {unique_clients} уникальных клиентов."
    }

def get_attendance_detailed(start_date, end_date):
    """
    Получает детальные данные о посещаемости за указанный период
    """
    # Получаем подробные данные о посещаемости по датам и типам тренировок
    attendance_data = db.session.query(
        func.date(Workout.start_time).label('date'),
        WorkoutType.name,
        Trainer.first_name,
        Trainer.last_name,
        func.count(Booking.id).label('booking_count'),
        func.sum(case((Booking.attended == True, 1), else_=0)).label('attended_count')
    ).join(
        Workout, Booking.workout_id == Workout.id
    ).join(
        WorkoutType, Workout.workout_type_id == WorkoutType.id
    ).join(
        Trainer, Workout.trainer_id == Trainer.id
    ).filter(
        Workout.start_time >= start_date,
        Workout.start_time < end_date
    ).group_by(
        func.date(Workout.start_time),
        WorkoutType.name,
        Trainer.first_name,
        Trainer.last_name
    ).order_by(
        func.date(Workout.start_time),
        WorkoutType.name
    ).all()
    
    # Обработка данных
    processed_rows = []
    for row in attendance_data:
        if hasattr(row[0], 'strftime'):
            date_str = row[0].strftime('%d.%m.%Y')
        else:
            date_str = str(row[0])
            
        workout_type = row[1]
        trainer_name = f"{row[2]} {row[3]}"
        booked = row[4]
        attended = row[5] if row[5] is not None else 0
        attendance_rate = round((attended / booked) * 100, 2) if booked > 0 else 0
        
        # Добавляем пропуски
        not_attended = booked - attended
        
        processed_rows.append((
            date_str,
            workout_type,
            trainer_name,
            booked,
            attended,
            not_attended,
            f"{attendance_rate}%"
        ))
    
    return {
        'headers': ['Дата', 'Тип тренировки', 'Тренер', 'Записалось', 'Посетило', 'Пропуски', 'Процент посещаемости'],
        'rows': processed_rows
    }

# Старые функции оставляем для обратной совместимости
def get_workout_popularity_data(start_date, end_date):
    """
    Обратная совместимость
    """
    return get_workout_popularity_summary(start_date, end_date)

def get_trainer_workload_data(start_date, end_date):
    """
    Обратная совместимость
    """
    return get_trainer_workload_summary(start_date, end_date)

def get_attendance_data(start_date, end_date):
    """
    Обратная совместимость
    """
    return get_attendance_summary(start_date, end_date) 