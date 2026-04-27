from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from forms.booking_forms import BookingForm
from models.database import db
from models.models import Booking, UserAbonement, Workout, WorkoutType
from services.notification_service import send_booking_confirmation


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
    today = datetime.now().date()

    future_bookings = (
        Booking.query.join(Workout)
        .filter(Booking.user_id == current_user.id, Workout.start_time >= today)
        .order_by(Workout.start_time)
        .all()
    )
    past_bookings = (
        Booking.query.join(Workout)
        .filter(Booking.user_id == current_user.id, Workout.start_time < today)
        .order_by(Workout.start_time.desc())
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
        workout_notifications=workout_notifications,
    )


@user_bp.route('/workouts')
@login_required
def workouts():
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


@user_bp.route('/book/<int:workout_id>', methods=['GET', 'POST'])
@login_required
def book_workout(workout_id):
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
