from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, current_user, logout_user, login_required
from models.models import User
from models.database import db
from forms.auth_forms import LoginForm, RegisterForm

# Создание блюпринта для аутентификации
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обработчик маршрута входа в систему
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Неверный email или пароль', 'danger')
    
    return render_template('auth/login.html', form=form, title='Вход')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Обработчик маршрута регистрации
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Проверяем, существует ли пользователь с таким email
        existing_user = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
        else:
            # Создаем нового пользователя
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Вы успешно зарегистрировались! Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form, title='Регистрация')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Обработчик маршрута выхода из системы
    """
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index')) 