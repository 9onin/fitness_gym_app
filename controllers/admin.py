from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from models.models import User, Trainer, Workout, WorkoutType, Booking
from models.database import db
from forms.admin_forms import TrainerForm, WorkoutForm, WorkoutTypeForm
from services.notification_service import send_schedule_update_notification
from datetime import datetime, timedelta
from functools import wraps

# Создание блюпринта для административных маршрутов
admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """
    Декоратор для проверки прав администратора
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Обработчик маршрута панели администратора
    """
    # Статистика для панели инструментов
    total_users = User.query.filter_by(is_admin=False).count()
    total_trainers = Trainer.query.count()
    total_workouts = Workout.query.count()
    upcoming_workouts = Workout.query.filter(Workout.start_time >= datetime.now()).count()
    
    # Последние регистрации
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         title='Панель администратора',
                         total_users=total_users,
                         total_trainers=total_trainers,
                         total_workouts=total_workouts,
                         upcoming_workouts=upcoming_workouts,
                         recent_users=recent_users)

# Маршруты для управления тренерами
@admin_bp.route('/trainers')
@login_required
@admin_required
def trainers():
    """
    Обработчик маршрута списка тренеров
    """
    trainers_list = Trainer.query.all()
    return render_template('admin/trainers/index.html',
                         title='Управление тренерами',
                         trainers=trainers_list)

@admin_bp.route('/trainers/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_trainer():
    """
    Обработчик маршрута создания нового тренера
    """
    form = TrainerForm()
    
    if form.validate_on_submit():
        trainer = Trainer(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            experience_years=form.experience_years.data,
            specialization=form.specialization.data,
            profile=form.profile.data
        )
        
        db.session.add(trainer)
        db.session.commit()
        
        flash('Тренер успешно добавлен', 'success')
        return redirect(url_for('admin.trainers'))
        
    return render_template('admin/trainers/form.html',
                         title='Добавить тренера',
                         form=form)

@admin_bp.route('/trainers/edit/<int:trainer_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trainer(trainer_id):
    """
    Обработчик маршрута редактирования тренера
    """
    trainer = Trainer.query.get_or_404(trainer_id)
    form = TrainerForm(obj=trainer)
    
    if form.validate_on_submit():
        trainer.first_name = form.first_name.data
        trainer.last_name = form.last_name.data
        trainer.experience_years = form.experience_years.data
        trainer.specialization = form.specialization.data
        trainer.profile = form.profile.data
        
        db.session.commit()
        
        flash('Информация о тренере обновлена', 'success')
        return redirect(url_for('admin.trainers'))
        
    return render_template('admin/trainers/form.html',
                         title='Редактировать тренера',
                         form=form,
                         trainer=trainer)

@admin_bp.route('/trainers/delete/<int:trainer_id>', methods=['POST'])
@login_required
@admin_required
def delete_trainer(trainer_id):
    """
    Обработчик маршрута удаления тренера
    """
    trainer = Trainer.query.get_or_404(trainer_id)
    
    # Проверяем, есть ли у тренера запланированные тренировки
    upcoming_workouts = Workout.query.filter(
        Workout.trainer_id == trainer.id,
        Workout.start_time >= datetime.now()
    ).first()
    
    if upcoming_workouts:
        flash('Невозможно удалить тренера с запланированными тренировками', 'danger')
        return redirect(url_for('admin.trainers'))
    
    db.session.delete(trainer)
    db.session.commit()
    
    flash('Тренер успешно удален', 'success')
    return redirect(url_for('admin.trainers'))

# Маршруты для управления типами тренировок
@admin_bp.route('/workout-types')
@login_required
@admin_required
def workout_types():
    """
    Обработчик маршрута списка типов тренировок
    """
    types = WorkoutType.query.all()
    return render_template('admin/workout_types/index.html',
                         title='Типы тренировок',
                         workout_types=types)

@admin_bp.route('/workout-types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_workout_type():
    """
    Обработчик маршрута создания нового типа тренировки
    """
    form = WorkoutTypeForm()
    
    if form.validate_on_submit():
        workout_type = WorkoutType(
            name=form.name.data,
            description=form.description.data
        )
        
        db.session.add(workout_type)
        db.session.commit()
        
        flash('Тип тренировки успешно добавлен', 'success')
        return redirect(url_for('admin.workout_types'))
        
    return render_template('admin/workout_types/form.html',
                         title='Добавить тип тренировки',
                         form=form)

@admin_bp.route('/workout-types/edit/<int:type_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_workout_type(type_id):
    """
    Обработчик маршрута редактирования типа тренировки
    """
    workout_type = WorkoutType.query.get_or_404(type_id)
    form = WorkoutTypeForm(obj=workout_type)
    
    if form.validate_on_submit():
        workout_type.name = form.name.data
        workout_type.description = form.description.data
        
        db.session.commit()
        
        flash('Тип тренировки обновлен', 'success')
        return redirect(url_for('admin.workout_types'))
        
    return render_template('admin/workout_types/form.html',
                         title='Редактировать тип тренировки',
                         form=form,
                         workout_type=workout_type)

@admin_bp.route('/workout-types/delete/<int:type_id>', methods=['POST'])
@login_required
@admin_required
def delete_workout_type(type_id):
    """
    Обработчик маршрута удаления типа тренировки
    """
    workout_type = WorkoutType.query.get_or_404(type_id)
    
    # Проверяем, используется ли тип тренировки
    if workout_type.workouts:
        flash('Невозможно удалить тип тренировки, который используется', 'danger')
        return redirect(url_for('admin.workout_types'))
    
    db.session.delete(workout_type)
    db.session.commit()
    
    flash('Тип тренировки успешно удален', 'success')
    return redirect(url_for('admin.workout_types'))

# Маршруты для управления тренировками
@admin_bp.route('/workouts')
@login_required
@admin_required
def admin_workouts():
    """
    Обработчик маршрута списка тренировок для администратора
    """
    # Фильтрация по дате (предстоящие или прошедшие)
    filter_type = request.args.get('filter', 'upcoming')
    
    if filter_type == 'past':
        workouts = Workout.query.filter(
            Workout.start_time < datetime.now()
        ).order_by(Workout.start_time.desc()).all()
    else:  # upcoming
        workouts = Workout.query.filter(
            Workout.start_time >= datetime.now()
        ).order_by(Workout.start_time).all()
    
    return render_template('admin/workouts/index.html',
                         title='Управление тренировками',
                         workouts=workouts,
                         filter_type=filter_type)

@admin_bp.route('/workouts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_workout():
    """
    Обработчик маршрута создания новой тренировки
    """
    form = WorkoutForm()
    
    # Заполняем выпадающие списки
    form.trainer_id.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Trainer.query.all()]
    form.workout_type_id.choices = [(t.id, t.name) for t in WorkoutType.query.all()]
    
    if form.validate_on_submit():
        # Проверяем, не занят ли тренер в выбранное время
        trainer_conflict = Workout.query.filter(
            Workout.trainer_id == form.trainer_id.data,
            Workout.end_time > form.start_time.data,
            Workout.start_time < form.end_time.data
        ).first()
        
        if trainer_conflict:
            flash('Тренер уже занят в выбранное время', 'danger')
        else:
            # Проверяем максимальную нагрузку тренера (8 часов в день)
            day_start = form.start_time.data.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            trainer_workouts = Workout.query.filter(
                Workout.trainer_id == form.trainer_id.data,
                Workout.start_time >= day_start,
                Workout.start_time < day_end
            ).all()
            
            total_hours = sum((w.end_time - w.start_time).total_seconds() / 3600 for w in trainer_workouts)
            new_workout_hours = (form.end_time.data - form.start_time.data).total_seconds() / 3600
            
            if total_hours + new_workout_hours > 8:
                flash('Превышена максимальная нагрузка тренера (8 часов в день)', 'danger')
            else:
                workout = Workout(
                    trainer_id=form.trainer_id.data,
                    workout_type_id=form.workout_type_id.data,
                    start_time=form.start_time.data,
                    end_time=form.end_time.data,
                    max_participants=form.max_participants.data,
                    description=form.description.data
                )
                
                db.session.add(workout)
                db.session.commit()
                
                flash('Тренировка успешно добавлена', 'success')
                return redirect(url_for('admin.admin_workouts'))
    
    return render_template('admin/workouts/form.html',
                         title='Добавить тренировку',
                         form=form)

@admin_bp.route('/workouts/edit/<int:workout_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_workout(workout_id):
    """
    Обработчик маршрута редактирования тренировки
    """
    workout = Workout.query.get_or_404(workout_id)
    form = WorkoutForm(obj=workout)
    
    # Заполняем выпадающие списки
    form.trainer_id.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Trainer.query.all()]
    form.workout_type_id.choices = [(t.id, t.name) for t in WorkoutType.query.all()]
    
    if form.validate_on_submit():
        # Проверяем, не занят ли тренер в выбранное время (исключая текущую тренировку)
        trainer_conflict = Workout.query.filter(
            Workout.trainer_id == form.trainer_id.data,
            Workout.end_time > form.start_time.data,
            Workout.start_time < form.end_time.data,
            Workout.id != workout_id
        ).first()
        
        if trainer_conflict:
            flash('Тренер уже занят в выбранное время', 'danger')
        else:
            # Проверяем максимальную нагрузку тренера (8 часов в день)
            day_start = form.start_time.data.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            trainer_workouts = Workout.query.filter(
                Workout.trainer_id == form.trainer_id.data,
                Workout.start_time >= day_start,
                Workout.start_time < day_end,
                Workout.id != workout_id
            ).all()
            
            total_hours = sum((w.end_time - w.start_time).total_seconds() / 3600 for w in trainer_workouts)
            new_workout_hours = (form.end_time.data - form.start_time.data).total_seconds() / 3600
            
            if total_hours + new_workout_hours > 8:
                flash('Превышена максимальная нагрузка тренера (8 часов в день)', 'danger')
            else:
                # Получаем всех пользователей, записанных на эту тренировку
                affected_users = [booking.user for booking in workout.bookings]
                
                # Изменяем тренировку
                workout.trainer_id = form.trainer_id.data
                workout.workout_type_id = form.workout_type_id.data
                workout.start_time = form.start_time.data
                workout.end_time = form.end_time.data
                workout.max_participants = form.max_participants.data
                workout.description = form.description.data
                
                db.session.commit()
                
                # Отправляем уведомления всем записанным пользователям
                for user in affected_users:
                    send_schedule_update_notification(user, workout)
                
                flash('Тренировка успешно обновлена', 'success')
                return redirect(url_for('admin.admin_workouts'))
    
    return render_template('admin/workouts/form.html',
                         title='Редактировать тренировку',
                         form=form,
                         workout=workout)

@admin_bp.route('/workouts/delete/<int:workout_id>', methods=['POST'])
@login_required
@admin_required
def delete_workout(workout_id):
    """
    Обработчик маршрута удаления тренировки
    """
    workout = Workout.query.get_or_404(workout_id)
    
    # Получаем всех пользователей, записанных на эту тренировку
    affected_users = [booking.user for booking in workout.bookings]
    
    # Удаляем тренировку
    db.session.delete(workout)
    db.session.commit()
    
    # Отправляем уведомления пользователям об отмене тренировки
    for user in affected_users:
        send_schedule_update_notification(user, workout, is_cancelled=True)
    
    flash('Тренировка успешно удалена', 'success')
    return redirect(url_for('admin.admin_workouts'))

# Маршрут для просмотра всех пользователей (только для администраторов)
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    Обработчик маршрута списка пользователей
    """
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users/index.html',
                         title='Пользователи',
                         users=all_users)

@admin_bp.route('/users/make-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """
    Обработчик маршрута для назначения пользователя администратором
    """
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash(f'Пользователь {user.email} уже является администратором', 'info')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'Пользователь {user.email} теперь администратор', 'success')
    
    return redirect(url_for('admin.users')) 