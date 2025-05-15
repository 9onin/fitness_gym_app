from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from datetime import datetime, timedelta

class TrainerForm(FlaskForm):
    """
    Форма для добавления и редактирования тренеров
    """
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)], 
                           render_kw={"placeholder": "Введите имя тренера"})
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)], 
                          render_kw={"placeholder": "Введите фамилию тренера"})
    experience_years = IntegerField('Опыт работы (лет)', validators=[NumberRange(min=0, max=50)], 
                                  render_kw={"placeholder": "Введите опыт работы в годах"})
    specialization = StringField('Специализация', validators=[DataRequired(), Length(max=100)], 
                               render_kw={"placeholder": "Например: йога, кроссфит, силовые тренировки"})
    profile = TextAreaField('Профиль', render_kw={"placeholder": "Информация о тренере, достижениях, образовании"})
    submit = SubmitField('Сохранить')

class WorkoutTypeForm(FlaskForm):
    """
    Форма для добавления и редактирования типов тренировок
    """
    name = StringField('Название', validators=[DataRequired(), Length(max=100)], 
                     render_kw={"placeholder": "Введите название типа тренировки"})
    description = TextAreaField('Описание', render_kw={"placeholder": "Описание типа тренировки"})
    submit = SubmitField('Сохранить')

class WorkoutForm(FlaskForm):
    """
    Форма для добавления и редактирования тренировок
    """
    trainer_id = SelectField('Тренер', validators=[DataRequired()], coerce=int)
    workout_type_id = SelectField('Тип тренировки', validators=[DataRequired()], coerce=int)
    start_time = DateTimeField('Время начала', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('Время окончания', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    max_participants = IntegerField('Максимальное количество участников', 
                                  validators=[NumberRange(min=1, max=50)], default=10)
    description = TextAreaField('Описание', render_kw={"placeholder": "Описание тренировки"})
    submit = SubmitField('Сохранить')
    
    def validate_end_time(self, field):
        """
        Проверка, что время окончания позже времени начала
        """
        if field.data <= self.start_time.data:
            raise ValidationError('Время окончания должно быть позже времени начала')
        
        # Проверка, что продолжительность тренировки не превышает 4 часа
        duration = (field.data - self.start_time.data).total_seconds() / 3600  # в часах
        if duration > 4:
            raise ValidationError('Продолжительность тренировки не может превышать 4 часа')

    def validate_start_time(self, field):
        """
        Проверка, что время начала не в прошлом
        """
        if field.data < datetime.now():
            raise ValidationError('Время начала не может быть в прошлом') 