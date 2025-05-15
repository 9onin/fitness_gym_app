from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    """
    Форма для входа в систему
    """
    email = StringField('Email', validators=[DataRequired(), Email()], 
                        render_kw={"placeholder": "Введите ваш email"})
    password = PasswordField('Пароль', validators=[DataRequired()], 
                             render_kw={"placeholder": "Введите ваш пароль"})
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    """
    Форма для регистрации
    """
    email = StringField('Email', validators=[DataRequired(), Email()], 
                        render_kw={"placeholder": "Введите ваш email"})
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)], 
                           render_kw={"placeholder": "Введите ваше имя"})
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)], 
                          render_kw={"placeholder": "Введите вашу фамилию"})
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)], 
                             render_kw={"placeholder": "Введите пароль"})
    confirm_password = PasswordField('Подтвердите пароль', 
                                   validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')], 
                                   render_kw={"placeholder": "Подтвердите пароль"})
    submit = SubmitField('Зарегистрироваться') 