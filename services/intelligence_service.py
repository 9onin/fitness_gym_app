from datetime import datetime, timedelta

from models.models import Booking, UserAbonement, WorkoutType


INTENSITY_LEVELS = {
    'Йога': 1,
    'Пилатес': 1,
    'Стретчинг': 1,
    'Тай-чи': 1,
    'Плавание': 2,
    'Бег': 2,
    'Кардио': 2,
    'Аэробика': 2,
    'Зумба': 2,
    'Спиннинг': 2,
    'Функциональный тренинг': 2,
    'Степ-аэробика': 2,
    'Каланетика': 2,
    'Аквааэробика': 2,
    'Силовая тренировка': 3,
    'Кроссфит': 3,
    'Бокс': 3,
    'HIIT': 3,
    'Табата': 3,
    'ТРХ': 3,
}


GOAL_RULES = {
    'похуд': ['Кардио', 'Функциональный тренинг', 'Зумба', 'Спиннинг'],
    'снижен': ['Кардио', 'Функциональный тренинг', 'Зумба'],
    'мас': ['Силовая тренировка', 'Кроссфит', 'ТРХ'],
    'сил': ['Силовая тренировка', 'Кроссфит', 'Бокс'],
    'восстан': ['Йога', 'Пилатес', 'Стретчинг'],
    'гибк': ['Йога', 'Пилатес', 'Стретчинг'],
    'вынослив': ['Кардио', 'Спиннинг', 'Бег', 'Функциональный тренинг'],
}


def build_client_intelligence(user):
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    week_ahead = now + timedelta(days=7)

    all_bookings = Booking.query.filter_by(user_id=user.id).all()
    upcoming_bookings = [booking for booking in all_bookings if booking.workout and booking.workout.start_time >= now]
    upcoming_week = [booking for booking in upcoming_bookings if booking.workout.start_time <= week_ahead]

    active_abonements = [
        abonement for abonement in getattr(user, 'abonements', [])
        if abonement.is_active and abonement.expiration_date >= now
    ]

    last_booking_date = None
    if all_bookings:
        workout_dates = [booking.workout.start_time for booking in all_bookings if booking.workout]
        if workout_dates:
            last_booking_date = max(workout_dates)

    activity_score = 100
    risk_reasons = []

    recent_visits = len([booking for booking in all_bookings if booking.workout and booking.workout.start_time >= month_ago])
    if recent_visits == 0:
        activity_score -= 40
        risk_reasons.append('нет посещений за последние 30 дней')
    elif recent_visits <= 2:
        activity_score -= 20
        risk_reasons.append('низкая активность за последний месяц')

    if not upcoming_bookings:
        activity_score -= 20
        risk_reasons.append('нет будущих записей')

    if not active_abonements:
        activity_score -= 20
        risk_reasons.append('нет активного абонемента')
    else:
        nearest_expiration = min(abonement.expiration_date for abonement in active_abonements)
        days_to_expire = (nearest_expiration - now).days
        if days_to_expire <= 7:
            activity_score -= 15
            risk_reasons.append('абонемент скоро закончится')

    if last_booking_date and last_booking_date < now - timedelta(days=21):
        activity_score -= 20
        risk_reasons.append('клиент давно не посещал тренировки')

    activity_score = max(0, min(100, activity_score))

    if activity_score >= 75:
        risk_level = 'low'
        risk_label = 'Низкий риск'
        admin_action = 'Можно предложить апгрейд абонемента или более амбициозный план тренировок.'
    elif activity_score >= 45:
        risk_level = 'medium'
        risk_label = 'Средний риск'
        admin_action = 'Стоит предложить подходящие тренировки и заранее напомнить о продлении.'
    else:
        risk_level = 'high'
        risk_label = 'Высокий риск'
        admin_action = 'Нужен персональный контакт: продление, заморозка или возврат клиента в расписание.'

    recommended_types = _recommend_workouts(user.fitness_goal)
    recommended_frequency = _recommend_frequency(user.fitness_goal, recent_visits)
    load_message = _build_load_message(upcoming_week)
    user_action = _build_user_action(risk_level, recommended_frequency, recommended_types)

    return {
        'activity_score': activity_score,
        'risk_level': risk_level,
        'risk_label': risk_label,
        'risk_reasons': risk_reasons or ['активность стабильна'],
        'recommended_types': recommended_types,
        'recommended_frequency': recommended_frequency,
        'load_message': load_message,
        'user_action': user_action,
        'admin_action': admin_action,
    }


def build_user_directory_intelligence(users):
    return {user.id: build_client_intelligence(user) for user in users if not user.is_admin}


def _recommend_workouts(goal_text):
    available_names = {workout_type.name for workout_type in WorkoutType.query.all()}
    normalized_goal = (goal_text or '').lower()

    for keyword, suggestions in GOAL_RULES.items():
        if keyword in normalized_goal:
            return [name for name in suggestions if name in available_names][:3]

    default_options = ['Функциональный тренинг', 'Кардио', 'Йога']
    return [name for name in default_options if name in available_names][:3]


def _recommend_frequency(goal_text, recent_visits):
    normalized_goal = (goal_text or '').lower()
    if 'мас' in normalized_goal or 'сил' in normalized_goal:
        return '3-4 тренировки в неделю'
    if 'восстан' in normalized_goal or 'гибк' in normalized_goal:
        return '2-3 мягкие тренировки в неделю'
    if recent_visits <= 1:
        return '2 тренировки в неделю для плавного старта'
    return '3 тренировки в неделю'


def _build_load_message(upcoming_week):
    if not upcoming_week:
        return 'На ближайшую неделю пока нет записей. Система советует выбрать минимум 2 тренировки.'

    intense_sessions = 0
    total_intensity = 0

    for booking in upcoming_week:
        intensity = INTENSITY_LEVELS.get(booking.workout.workout_type.name, 2)
        total_intensity += intensity
        if intensity == 3:
            intense_sessions += 1

    if intense_sessions >= 3:
        return 'В расписании много тяжелых тренировок подряд. Лучше добавить восстановительный день.'
    if total_intensity <= len(upcoming_week) * 2:
        return 'Нагрузка выглядит сбалансированной, можно сохранять текущий темп.'
    return 'Нагрузка выше средней. Следите за восстановлением и качеством сна.'


def _build_user_action(risk_level, recommended_frequency, recommended_types):
    workout_line = ', '.join(recommended_types) if recommended_types else 'смешанный тренировочный план'
    if risk_level == 'high':
        return f'Лучший следующий шаг: вернуть регулярность и записаться на {recommended_frequency}. Начните с {workout_line}.'
    if risk_level == 'medium':
        return f'Для стабильного прогресса держите темп {recommended_frequency} и добавьте в план {workout_line}.'
    return f'У вас хороший ритм. Чтобы развиваться дальше, сохраняйте {recommended_frequency} и чередуйте {workout_line}.'
