import random

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms.auth_forms import LoginForm, RegisterForm
from models.database import db
from models.models import User

auth_bp = Blueprint('auth', __name__)


def generate_captcha():
    left = random.randint(1, 9)
    right = random.randint(1, 9)
    session['captcha_question'] = f'{left} + {right}'
    session['captcha_answer'] = str(left + right)


def ensure_captcha():
    if request.method == 'GET' or 'captcha_question' not in session:
        generate_captcha()


def validate_captcha(answer):
    expected = session.get('captcha_answer')
    return expected is not None and answer.strip() == expected


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    ensure_captcha()
    form = LoginForm()

    if form.validate_on_submit():
        if not validate_captcha(form.captcha_answer.data):
            form.captcha_answer.errors.append('Неверный ответ на капчу')
            generate_captcha()
            return render_template(
                'auth/login.html',
                form=form,
                title='Вход',
                captcha_question=session.get('captcha_question')
            )

        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            generate_captcha()
            return redirect(next_page or url_for('main.index'))

        flash('Неверный email или пароль', 'danger')
        generate_captcha()

    return render_template(
        'auth/login.html',
        form=form,
        title='Вход',
        captcha_question=session.get('captcha_question')
    )


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    ensure_captcha()
    form = RegisterForm()

    if form.validate_on_submit():
        if not validate_captcha(form.captcha_answer.data):
            form.captcha_answer.errors.append('Неверный ответ на капчу')
            generate_captcha()
            return render_template(
                'auth/register.html',
                form=form,
                title='Регистрация',
                captcha_question=session.get('captcha_question')
            )

        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            generate_captcha()
        else:
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Вы успешно зарегистрировались! Теперь вы можете войти в систему.', 'success')
            generate_captcha()
            return redirect(url_for('auth.login'))

    return render_template(
        'auth/register.html',
        form=form,
        title='Регистрация',
        captcha_question=session.get('captcha_question')
    )


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))
