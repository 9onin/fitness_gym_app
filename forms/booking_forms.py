from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField
from wtforms.validators import DataRequired
 
class BookingForm(FlaskForm):
    """
    Форма для записи на тренировку
    """
    submit = SubmitField('Записаться') 