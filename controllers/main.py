from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import current_user

from models.models import Booking, Workout, WorkoutType
from services.intelligence_service import FITNESS_ASSISTANT_GOALS, build_client_intelligence


main_bp = Blueprint('main', __name__)


ENERGY_LEVELS = {
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
    'TRX': 3,
}


WORKOUT_SUMMARIES = {
    'Йога': 'Спокойная практика для гибкости, дыхания и внутреннего баланса.',
    'Пилатес': 'Мягкая нагрузка на корпус, осанку и контроль движений.',
    'Стретчинг': 'Растяжка для подвижности суставов и снятия мышечного напряжения.',
    'Тай-чи': 'Плавные движения для координации, концентрации и баланса.',
    'Плавание': 'Ровная кардионагрузка с бережной работой всего тела.',
    'Бег': 'Тренировка выносливости, дыхания и общей физической формы.',
    'Кардио': 'Активная сессия для укрепления сердца и сжигания калорий.',
    'Аэробика': 'Динамичные связки под музыку для тонуса и выносливости.',
    'Зумба': 'Танцевальная фитнес-тренировка с ярким ритмом и хорошим настроением.',
    'Спиннинг': 'Интенсивная велотренировка для ног, сердца и выносливости.',
    'Функциональный тренинг': 'Упражнения на силу, стабильность и движения из реальной жизни.',
    'Степ-аэробика': 'Кардио с платформой для координации, ног и выносливости.',
    'Каланетика': 'Статичные упражнения на глубокие мышцы и точный контроль тела.',
    'Аквааэробика': 'Тренировка в воде с мягкой нагрузкой на суставы и мышцы.',
    'Силовая тренировка': 'Работа на силу, рельеф и уверенное развитие мышц.',
    'Кроссфит': 'Высокоинтенсивный формат с силой, скоростью и мощной нагрузкой.',
    'Бокс': 'Энергичная тренировка на реакцию, выносливость и силу удара.',
    'HIIT': 'Короткие интервалы высокой нагрузки для быстрого расхода энергии.',
    'Табата': 'Очень интенсивные интервалы в быстром темпе с коротким отдыхом.',
    'TRX': 'Подвесной тренинг на собственном весе для всего тела и баланса.',
}


def get_goal_key_by_text(goal_text):
    for key, goal in FITNESS_ASSISTANT_GOALS.items():
        if goal['goal_text'] == goal_text:
            return key
    return 'wellness'


def has_saved_fitness_plan(user):
    return (
        user.fitness_plan_height_cm is not None
        and user.fitness_plan_weight_kg is not None
        and user.fitness_plan_goal_key
    )


def build_home_plan_context(user):
    if not user.is_authenticated:
        return None

    now = datetime.now()
    week_end = now + timedelta(days=7)
    goal_key = user.fitness_plan_goal_key or get_goal_key_by_text(user.fitness_goal)
    goal = FITNESS_ASSISTANT_GOALS.get(goal_key, FITNESS_ASSISTANT_GOALS['wellness'])
    has_plan = has_saved_fitness_plan(user)
    upcoming_bookings = (
        Booking.query.join(Workout)
        .filter(
            Booking.user_id == user.id,
            Workout.start_time >= now,
            Workout.start_time < week_end,
        )
        .order_by(Workout.start_time)
        .all()
    )
    booking_items = [
        {
            'date_label': booking.workout.start_time.strftime('%d.%m'),
            'time_label': booking.workout.start_time.strftime('%H:%M'),
            'workout_name': booking.workout.workout_type.name,
        }
        for booking in upcoming_bookings[:3]
    ]
    smart_profile = build_client_intelligence(user)
    activity_status_label = _build_activity_status_label(smart_profile['activity_score'])

    if not has_plan:
        return {
            'has_plan': False,
            'goal_label': goal['label'],
            'title': 'Сначала подберите план',
            'status_label': 'Плана еще нет',
            'message': 'Ответьте на пару вопросов по росту, весу и цели, чтобы увидеть недельный план и затем записаться на подходящие тренировки.',
            'booking_items': booking_items,
            'booking_count': len(upcoming_bookings),
            'activity_score': smart_profile['activity_score'],
            'activity_status_label': activity_status_label,
            'load_message': smart_profile['load_message'],
        }

    booking_count = len(upcoming_bookings)
    if booking_count == 0:
        status_label = 'Нужна запись'
        message = 'План сохранен, но на ближайшие 7 дней у вас пока нет записей. Откройте план и выберите удобные слоты.'
    elif booking_count == 1:
        status_label = '1 запись на неделе'
        message = 'План сохранен, первая запись уже есть. Проверьте, закрывает ли она рекомендованный ритм.'
    else:
        status_label = f'{booking_count} записи на неделе'
        message = 'План сохранен, ближайшая неделя уже частично закрыта записями.'

    return {
        'has_plan': True,
        'goal_label': goal['label'],
        'title': 'Текущий план тренировок',
        'status_label': status_label,
        'message': message,
        'booking_items': booking_items,
        'booking_count': booking_count,
        'updated_at': user.fitness_plan_updated_at,
        'activity_score': smart_profile['activity_score'],
        'activity_status_label': activity_status_label,
        'load_message': smart_profile['load_message'],
    }


def _build_activity_status_label(activity_score):
    if activity_score >= 75:
        return 'Ритм стабильный'
    if activity_score >= 45:
        return 'Ритм нужно поддержать'
    return 'Нужен следующий шаг'


@main_bp.route('/')
@main_bp.route('/index')
def index():
    upcoming_workouts = (
        Workout.query.filter(Workout.start_time >= datetime.now())
        .order_by(Workout.start_time)
        .limit(5)
        .all()
    )
    workout_types = WorkoutType.query.all()
    featured_workout_types = workout_types[:8]
    smart_profile = build_client_intelligence(current_user) if current_user.is_authenticated else None
    home_plan = build_home_plan_context(current_user) if current_user.is_authenticated else None
    recommended_workouts = []

    if smart_profile:
        workout_type_map = {workout_type.name: workout_type.id for workout_type in workout_types}
        recommended_workouts = [
            {'name': workout_name, 'id': workout_type_map.get(workout_name)}
            for workout_name in smart_profile['recommended_types']
            if workout_type_map.get(workout_name)
        ]

    return render_template(
        'index.html',
        title='Главная',
        upcoming_workouts=upcoming_workouts,
        workout_types=workout_types,
        featured_workout_types=featured_workout_types,
        energy_levels=ENERGY_LEVELS,
        workout_summaries=WORKOUT_SUMMARIES,
        smart_profile=smart_profile,
        home_plan=home_plan,
        recommended_workouts=recommended_workouts,
    )
