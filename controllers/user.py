from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
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
from services.trainer_balance_service import ensure_trainers_and_balance_workouts


user_bp = Blueprint('user', __name__)


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
    base_query = Workout.query.filter(Workout.start_time >= datetime.now())

    if workout_type_id:
        base_query = base_query.filter(Workout.workout_type_id == workout_type_id)

    workouts_list = base_query.order_by(Workout.start_time).all()
    workout_types = WorkoutType.query.all()

    return render_template(
        'user/workouts.html',
        title='Доступные тренировки',
        workouts=workouts_list,
        workout_types=workout_types,
        selected_type=workout_type_id,
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
    form_data = {
        'height_cm': '',
        'weight_kg': '',
        'goal_key': 'wellness',
    }
    recommendation = None

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
            )

        if height_cm < 120 or height_cm > 230 or weight_kg < 30 or weight_kg > 250:
            flash('Укажите реалистичные параметры роста и веса.', 'warning')
        else:
            recommendation = build_fitness_assistant_plan(height_cm, weight_kg, form_data['goal_key'])
            workout_type_map = {workout_type.name: workout_type.id for workout_type in WorkoutType.query.all()}
            recommendation['recommended_workouts'] = [
                {'name': workout_name, 'id': workout_type_map.get(workout_name)}
                for workout_name in recommendation['recommended_types']
                if workout_type_map.get(workout_name)
            ]
            current_user.fitness_goal = FITNESS_ASSISTANT_GOALS.get(
                form_data['goal_key'],
                FITNESS_ASSISTANT_GOALS['wellness'],
            )['goal_text']
            db.session.commit()

    return render_template(
        'user/fitness_assistant.html',
        title='Подбор тренировок',
        goal_choices=goal_choices,
        form_data=form_data,
        recommendation=recommendation,
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
        return redirect(url_for('abonements.index'))

    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(user_id=current_user.id, workout_id=workout.id)
        db.session.add(booking)
        db.session.commit()

        if valid_abonement.visits_remaining is not None:
            valid_abonement.visits_remaining -= 1

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
