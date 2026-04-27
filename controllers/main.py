from flask import Blueprint, render_template
from models.models import Workout, WorkoutType

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
    'ТРХ': 3,
}


@main_bp.route('/')
@main_bp.route('/index')
def index():
    upcoming_workouts = Workout.query.order_by(Workout.start_time).limit(5).all()
    workout_types = WorkoutType.query.all()

    return render_template(
        'index.html',
        title='Главная',
        upcoming_workouts=upcoming_workouts,
        workout_types=workout_types,
        energy_levels=ENERGY_LEVELS
    )
