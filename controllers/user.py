from datetime import datetime, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from forms.booking_forms import BookingForm
from models.database import db
from models.models import Booking, Trainer, UserAbonement, Workout, WorkoutType
from services.intelligence_service import (
    FITNESS_ASSISTANT_GOALS,
    build_client_intelligence,
    build_fitness_assistant_plan,
)
from services.notification_service import send_booking_confirmation
from services.notification_service import build_user_marketing_notifications
from services.trainer_balance_service import ensure_trainers_and_balance_workouts


user_bp = Blueprint('user', __name__)


PLAN_WEEKDAY_NUMBERS = {
    'Понедельник': 0,
    'Вторник': 1,
    'Среда': 2,
    'Четверг': 3,
    'Пятница': 4,
    'Суббота': 5,
    'Воскресенье': 6,
}


def get_goal_key_by_text(goal_text):
    for key, goal in FITNESS_ASSISTANT_GOALS.items():
        if goal['goal_text'] == goal_text:
            return key
    return 'wellness'


def get_goal_label(goal_key):
    return FITNESS_ASSISTANT_GOALS.get(goal_key, FITNESS_ASSISTANT_GOALS['wellness'])['label']


def has_saved_fitness_plan(user):
    return (
        user.fitness_plan_height_cm is not None
        and user.fitness_plan_weight_kg is not None
        and user.fitness_plan_goal_key
    )


def get_next_plan_date(day_name, today=None):
    today = today or datetime.now().date()
    weekday_number = PLAN_WEEKDAY_NUMBERS.get(day_name)
    if weekday_number is None:
        return None

    days_until = (weekday_number - today.weekday()) % 7
    return today + timedelta(days=days_until)


def build_fitness_recommendation(height_cm, weight_kg, goal_key, user_id=None):
    recommendation = build_fitness_assistant_plan(height_cm, weight_kg, goal_key)
    recommendation['upcoming_bookings'] = []
    workout_type_map = {workout_type.name: workout_type.id for workout_type in WorkoutType.query.all()}
    recommendation['recommended_workouts'] = [
        {'name': workout_name, 'id': workout_type_map.get(workout_name)}
        for workout_name in recommendation['recommended_types']
        if workout_type_map.get(workout_name)
    ]
    recommendation['weekly_plan'] = [
        {
            **item,
            'workout_id': workout_type_map.get(item['workout_name']),
        }
        for item in recommendation['weekly_plan']
    ]
    if user_id:
        attach_weekly_booking_status(recommendation, user_id)
    return recommendation


def attach_weekly_booking_status(recommendation, user_id):
    now = datetime.now()
    period_end = now + timedelta(days=7)
    bookings = (
        Booking.query.join(Workout)
        .filter(
            Booking.user_id == user_id,
            Workout.start_time >= now,
            Workout.start_time < period_end,
        )
        .order_by(Workout.start_time)
        .all()
    )
    bookings_by_date = {}
    for booking in bookings:
        bookings_by_date.setdefault(booking.workout.start_time.date(), []).append(booking)

    planned_types_by_date = {}
    for item in recommendation.get('weekly_plan', []):
        plan_date = get_next_plan_date(item['day'])
        item['date'] = plan_date
        item['date_label'] = plan_date.strftime('%d.%m') if plan_date else ''
        if plan_date:
            planned_types_by_date.setdefault(plan_date, set()).add(item['workout_name'])

        day_bookings = bookings_by_date.get(plan_date, []) if plan_date else []
        matching_booking = next(
            (
                booking for booking in day_bookings
                if booking.workout.workout_type.name == item['workout_name']
            ),
            None,
        )

        if matching_booking:
            item['booking_status'] = 'matched'
            item['booking_label'] = 'Записан'
            item['booking_text'] = (
                f"{matching_booking.workout.start_time.strftime('%H:%M')} - "
                f"{matching_booking.workout.workout_type.name}"
            )
        elif day_bookings:
            booking_names = ', '.join(
                f"{booking.workout.start_time.strftime('%H:%M')} - {booking.workout.workout_type.name}"
                for booking in day_bookings
            )
            item['booking_status'] = 'same_day'
            item['booking_label'] = 'Другая запись'
            item['booking_text'] = booking_names
        else:
            item['booking_status'] = 'missing'
            item['booking_label'] = 'Не записан'
            item['booking_text'] = 'Выберите подходящее время для этого дня.'

    recommendation['upcoming_bookings'] = [
        _build_upcoming_booking_item(booking, planned_types_by_date)
        for booking in bookings
    ]


def _build_upcoming_booking_item(booking, planned_types_by_date):
    workout = booking.workout
    workout_date = workout.start_time.date()
    planned_types = planned_types_by_date.get(workout_date, set())
    workout_name = workout.workout_type.name

    if workout_name in planned_types:
        plan_status = 'in_plan'
        plan_label = 'В плане'
    elif planned_types:
        plan_status = 'same_day'
        plan_label = 'В день плана'
    else:
        plan_status = 'extra'
        plan_label = 'Дополнительно'

    return {
        'id': booking.id,
        'date_label': workout.start_time.strftime('%d.%m'),
        'time_label': f"{workout.start_time.strftime('%H:%M')} - {workout.end_time.strftime('%H:%M')}",
        'workout_name': workout_name,
        'trainer_name': f'{workout.trainer.first_name} {workout.trainer.last_name}' if workout.trainer else 'Тренер назначается',
        'plan_status': plan_status,
        'plan_label': plan_label,
    }


def get_refundable_abonement(user_id):
    return (
        UserAbonement.query.filter(
            UserAbonement.user_id == user_id,
            UserAbonement.is_active == True,
            UserAbonement.expiration_date > datetime.utcnow(),
            UserAbonement.visits_remaining != None,
        )
        .order_by(UserAbonement.purchase_date.desc())
        .first()
    )


def get_valid_abonement(user_id):
    return (
        UserAbonement.query.filter(
            UserAbonement.user_id == user_id,
            UserAbonement.is_active == True,
            UserAbonement.expiration_date > datetime.utcnow(),
        )
        .filter((UserAbonement.visits_remaining == None) | (UserAbonement.visits_remaining > 0))
        .filter((UserAbonement.frozen_until == None) | (UserAbonement.frozen_until <= datetime.utcnow()))
        .first()
    )


@user_bp.route('/schedule')
@login_required
def schedule():
    ensure_trainers_and_balance_workouts()
    today = datetime.now().date()
    history_days = request.args.get('history_days', 90, type=int)
    history_page = max(request.args.get('history_page', 1, type=int), 1)
    per_page = 20

    allowed_history_days = {30, 90, 180, 365}
    if history_days not in allowed_history_days:
        history_days = 90

    future_bookings = (
        Booking.query.join(Workout)
        .filter(Booking.user_id == current_user.id, Workout.start_time >= today)
        .order_by(Workout.start_time)
        .all()
    )
    past_query = (
        Booking.query.join(Workout)
        .filter(Booking.user_id == current_user.id, Workout.start_time < today)
    )

    history_start = datetime.now() - timedelta(days=history_days)
    past_query = past_query.filter(Workout.start_time >= history_start)
    past_total = past_query.count()
    past_pages = max((past_total + per_page - 1) // per_page, 1)
    history_page = min(history_page, past_pages)
    past_bookings = (
        past_query.order_by(Workout.start_time.desc())
        .offset((history_page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    workout_notifications = []
    next_day = datetime.utcnow() + timedelta(hours=24)
    for booking in future_bookings:
        if booking.workout.start_time <= next_day:
            workout_notifications.append(
                f"{booking.workout.workout_type.name} в {booking.workout.start_time.strftime('%d.%m %H:%M')}"
            )

    return render_template(
        'user/schedule.html',
        title='Моё расписание',
        future_bookings=future_bookings,
        past_bookings=past_bookings,
        history_days=history_days,
        history_page=history_page,
        history_pages=past_pages,
        past_total=past_total,
        workout_notifications=workout_notifications,
        smart_profile=build_client_intelligence(current_user),
    )


@user_bp.route('/workouts')
@login_required
def workouts():
    ensure_trainers_and_balance_workouts()
    workout_type_id = request.args.get('type', type=int)
    selected_date = (request.args.get('date') or '').strip()
    base_query = Workout.query.filter(Workout.start_time >= datetime.now())

    if workout_type_id:
        base_query = base_query.filter(Workout.workout_type_id == workout_type_id)

    if selected_date:
        try:
            selected_day = datetime.strptime(selected_date, '%Y-%m-%d')
            next_day = selected_day + timedelta(days=1)
            base_query = base_query.filter(
                Workout.start_time >= selected_day,
                Workout.start_time < next_day,
            )
        except ValueError:
            flash('Выберите корректную дату для фильтрации тренировок.', 'warning')
            selected_date = ''

    workouts_list = base_query.order_by(Workout.start_time).all()
    workout_types = WorkoutType.query.all()

    return render_template(
        'user/workouts.html',
        title='Доступные тренировки',
        workouts=workouts_list,
        workout_types=workout_types,
        selected_type=workout_type_id,
        selected_date=selected_date,
    )


@user_bp.route('/trainers')
@login_required
def trainers():
    ensure_trainers_and_balance_workouts()
    trainers_list = Trainer.query.order_by(Trainer.first_name, Trainer.last_name).all()
    return render_template(
        'user/trainers.html',
        title='Тренеры клуба',
        trainers=trainers_list,
    )


@user_bp.route('/trainers/<int:trainer_id>')
@login_required
def trainer_detail(trainer_id):
    ensure_trainers_and_balance_workouts()
    trainer = Trainer.query.get_or_404(trainer_id)
    upcoming_workouts = (
        Workout.query.filter(
            Workout.trainer_id == trainer.id,
            Workout.start_time >= datetime.now(),
        )
        .order_by(Workout.start_time)
        .all()
    )

    return render_template(
        'user/trainer_detail.html',
        title=f'{trainer.first_name} {trainer.last_name}',
        trainer=trainer,
        upcoming_workouts=upcoming_workouts,
    )


@user_bp.route('/fitness-assistant', methods=['GET', 'POST'])
@login_required
def fitness_assistant():
    ensure_trainers_and_balance_workouts()
    goal_choices = [
        {'value': key, 'label': item['label']}
        for key, item in FITNESS_ASSISTANT_GOALS.items()
    ]
    saved_goal_key = get_goal_key_by_text(current_user.fitness_goal)
    has_active_abonement = get_valid_abonement(current_user.id) is not None
    has_saved_plan = has_saved_fitness_plan(current_user)
    plan_goal_key = current_user.fitness_plan_goal_key or saved_goal_key
    form_data = {
        'height_cm': f'{current_user.fitness_plan_height_cm:g}' if current_user.fitness_plan_height_cm is not None else '',
        'weight_kg': f'{current_user.fitness_plan_weight_kg:g}' if current_user.fitness_plan_weight_kg is not None else '',
        'goal_key': plan_goal_key,
    }
    recommendation = build_fitness_recommendation(
        current_user.fitness_plan_height_cm,
        current_user.fitness_plan_weight_kg,
        plan_goal_key,
        current_user.id,
    ) if has_saved_plan else None

    if request.method == 'POST':
        form_data['height_cm'] = (request.form.get('height_cm') or '').strip()
        form_data['weight_kg'] = (request.form.get('weight_kg') or '').strip()
        form_data['goal_key'] = (request.form.get('goal_key') or 'wellness').strip()

        try:
            height_cm = float(form_data['height_cm'].replace(',', '.'))
            weight_kg = float(form_data['weight_kg'].replace(',', '.'))
        except ValueError:
            flash('Введите корректные значения роста и веса.', 'warning')
            return render_template(
                'user/fitness_assistant.html',
                title='Подбор тренировок',
                goal_choices=goal_choices,
                form_data=form_data,
                recommendation=recommendation,
                has_active_abonement=has_active_abonement,
                has_saved_plan=has_saved_plan,
                plan_updated_at=current_user.fitness_plan_updated_at,
                saved_goal_label=get_goal_label(form_data['goal_key']),
                smart_profile=build_client_intelligence(current_user),
            )

        if height_cm < 120 or height_cm > 230 or weight_kg < 30 or weight_kg > 250:
            flash('Укажите реалистичные параметры роста и веса.', 'warning')
        else:
            recommendation = build_fitness_recommendation(height_cm, weight_kg, form_data['goal_key'], current_user.id)
            current_user.fitness_goal = FITNESS_ASSISTANT_GOALS.get(
                form_data['goal_key'],
                FITNESS_ASSISTANT_GOALS['wellness'],
            )['goal_text']
            current_user.fitness_plan_height_cm = height_cm
            current_user.fitness_plan_weight_kg = weight_kg
            current_user.fitness_plan_goal_key = form_data['goal_key']
            current_user.fitness_plan_updated_at = datetime.utcnow()
            db.session.commit()
            has_saved_plan = True

    return render_template(
        'user/fitness_assistant.html',
        title='Подбор тренировок',
        goal_choices=goal_choices,
        form_data=form_data,
        recommendation=recommendation,
        has_active_abonement=has_active_abonement,
        has_saved_plan=has_saved_plan,
        plan_updated_at=current_user.fitness_plan_updated_at,
        saved_goal_label=get_goal_label(form_data['goal_key']),
        smart_profile=build_client_intelligence(current_user),
    )


@user_bp.route('/book/<int:workout_id>', methods=['GET', 'POST'])
@login_required
def book_workout(workout_id):
    ensure_trainers_and_balance_workouts()
    workout = Workout.query.get_or_404(workout_id)

    existing_booking = Booking.query.filter_by(user_id=current_user.id, workout_id=workout.id).first()
    if existing_booking:
        flash('Вы уже записаны на эту тренировку', 'warning')
        return redirect(url_for('user.workouts'))

    if workout.is_full:
        flash('На данную тренировку не осталось свободных мест', 'danger')
        return redirect(url_for('user.workouts'))

    valid_abonement = get_valid_abonement(current_user.id)
    if not valid_abonement:
        flash('У вас нет действующего активного абонемента. Если абонемент заморожен, дождитесь окончания заморозки или купите новый.', 'warning')
        next_url = url_for('user.book_workout', workout_id=workout.id)
        return redirect(url_for('abonements.index', next=next_url))

    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(user_id=current_user.id, workout_id=workout.id)
        if valid_abonement.visits_remaining is not None:
            valid_abonement.visits_remaining -= 1
            booking.visit_charged = True

        db.session.add(booking)
        db.session.commit()
        send_booking_confirmation(current_user, workout)

        flash('Вы успешно записались на тренировку', 'success')
        return redirect(url_for('user.schedule'))

    return render_template(
        'user/book_workout.html',
        title='Запись на тренировку',
        form=form,
        workout=workout,
        valid_abonement=valid_abonement,
    )


@user_bp.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash('У вас нет прав для отмены этой записи', 'danger')
        return redirect(url_for('user.schedule'))

    if booking.workout.start_time < datetime.now():
        flash('Невозможно отменить запись на прошедшую тренировку', 'danger')
        return redirect(url_for('user.schedule'))

    if booking.visit_charged:
        refundable_abonement = get_refundable_abonement(current_user.id)
        if refundable_abonement:
            refundable_abonement.visits_remaining += 1

    db.session.delete(booking)
    db.session.commit()

    flash('Запись на тренировку успешно отменена', 'success')
    return redirect(url_for('user.schedule'))


@user_bp.route('/check_in/<int:booking_id>', methods=['POST'])
@login_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash('У вас нет прав для этой операции', 'danger')
        return redirect(url_for('user.schedule'))

    if booking.attended:
        flash('Вы уже отмечены как посетивший', 'info')
        return redirect(url_for('user.schedule'))

    booking.attended = True
    db.session.commit()

    flash('Посещение засчитано!', 'success')
    return redirect(url_for('user.schedule'))


@user_bp.route('/my_abonements')
@login_required
def my_abonements():
    return redirect(url_for('abonements.my_abonements'))


@user_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    notification_ids = [
        item.get('id')
        for item in build_user_marketing_notifications(current_user)
        if item.get('id')
    ]
    session['read_notification_ids'] = notification_ids
    session.modified = True
    return jsonify({'status': 'ok', 'read_count': len(notification_ids), 'unread_count': 0})
