from flask import Blueprint, render_template
from flask_login import current_user
from models.models import Workout, WorkoutType

# Создание блюпринта для основных маршрутов
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """
    Обработчик маршрута главной страницы
    """
    # Получаем предстоящие тренировки (ограничиваем до 5)
    upcoming_workouts = Workout.query.order_by(Workout.start_time).limit(5).all()
    
    # Получаем все типы тренировок для отображения в меню
    workout_types = WorkoutType.query.all()
    
    return render_template('index.html', 
                         title='Главная', 
                         upcoming_workouts=upcoming_workouts,
                         workout_types=workout_types)