from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError


class AbonementPaymentForm(FlaskForm):
    cardholder_name = StringField(
        'Имя владельца карты',
        validators=[DataRequired(), Length(min=2, max=80)],
        render_kw={"placeholder": "IVAN IVANOV"}
    )
    card_number = StringField(
        'Номер карты',
        validators=[DataRequired(), Regexp(r'^[0-9 ]{13,23}$', message='Введите номер карты цифрами')],
        render_kw={"placeholder": "4111 1111 1111 1111", "inputmode": "numeric"}
    )
    expiry_month = SelectField(
        'Месяц',
        validators=[DataRequired()],
        choices=[(str(month), f'{month:02d}') for month in range(1, 13)]
    )
    expiry_year = SelectField(
        'Год',
        validators=[DataRequired()],
        choices=[(str(year), str(year)) for year in range(datetime.utcnow().year, datetime.utcnow().year + 11)]
    )
    cvv = StringField(
        'CVV/CVC',
        validators=[DataRequired(), Regexp(r'^[0-9]{3,4}$', message='Введите 3 или 4 цифры')],
        render_kw={"placeholder": "123", "inputmode": "numeric"}
    )
    accept_terms = BooleanField(
        'Я подтверждаю оплату и согласен с условиями использования',
        validators=[DataRequired(message='Подтвердите согласие с условиями')]
    )
    submit = SubmitField('Оплатить онлайн')

    def validate_cardholder_name(self, field):
        if not any(ch.isalpha() for ch in field.data):
            raise ValidationError('Укажите имя владельца карты')
