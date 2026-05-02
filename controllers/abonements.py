from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from forms.payment_forms import AbonementPaymentForm
from models.database import db
from models.models import Abonement, Booking, UserAbonement, Workout
from payment import PaymentValidationError, TestPaymentProcessor, parse_payment_info


abonements_bp = Blueprint('abonements', __name__)


ABONEMENT_CATALOG = [
    {
        'slug': 'trial',
        'name': 'Пробный старт',
        'type': 'trial',
        'price': 990,
        'duration_days': 7,
        'visits_count': 3,
        'description': 'Неделя, чтобы познакомиться с клубом, тренерами и вашим будущим ритмом занятий.',
        'summary': 'Лучший вариант, чтобы попробовать клуб без долгих обязательств.',
        'features': [
            '3 посещения в любые будние дни',
            'Вводная консультация тренера',
            'Первичная диагностика состава тела',
            'Доступ в тренажерный зал и кардиозону',
            'Групповые занятия начального уровня',
        ],
        'color': '#22c55e',
        'is_popular': False,
        'discount': 0,
        'is_active': True,
        'type_label': 'Пробный',
        'accent': 'Попробовать клуб',
    },
    {
        'slug': 'basic',
        'name': 'Базовый безлимит',
        'type': 'basic',
        'price': 3990,
        'duration_days': 30,
        'visits_count': 0,
        'description': 'Комфортный месячный тариф для тех, кто хочет тренироваться регулярно и без ограничений.',
        'summary': 'Универсальный абонемент на каждый день и любой тип тренировки.',
        'features': [
            'Безлимитное посещение клуба',
            'Все тренажерные зоны и кардиопространство',
            'Групповые занятия по расписанию',
            'Доступ в раздевалки и душевые',
            'Одна персональная консультация в месяц',
        ],
        'color': '#4f46e5',
        'is_popular': True,
        'discount': 10,
        'is_active': True,
        'type_label': 'Базовый',
        'accent': 'Самый популярный выбор',
    },
    {
        'slug': 'vip',
        'name': 'VIP Премиум',
        'type': 'vip',
        'price': 8990,
        'duration_days': 30,
        'visits_count': 0,
        'description': 'Премиальный формат с персональным сопровождением и расширенным набором восстановительных услуг.',
        'summary': 'Максимум комфорта, приватности и персонального внимания.',
        'features': [
            'Безлимит на все зоны клуба',
            '2 персональные тренировки в подарок',
            'VIP-раздевалка и полотенца',
            'Доступ в SPA, хаммам и сауну',
            'Приоритетная запись на популярные тренировки',
        ],
        'color': '#7c3aed',
        'is_popular': False,
        'discount': 15,
        'is_active': True,
        'type_label': 'Премиум',
        'accent': 'Для максимального комфорта',
    },
    {
        'slug': 'package-10',
        'name': 'Пакет 10 тренировок',
        'type': 'package',
        'price': 4990,
        'duration_days': 60,
        'visits_count': 10,
        'description': 'Гибкий пакет для тех, кто тренируется в удобном темпе и не хочет переплачивать за безлимит.',
        'summary': 'Подходит для спокойного режима занятий 1-2 раза в неделю.',
        'features': [
            '10 посещений в течение 60 дней',
            'Доступ ко всем зонам клуба',
            'Групповые занятия включены',
            'Заморозка до 7 дней',
            'Электронный трекер остатка посещений',
        ],
        'color': '#f59e0b',
        'is_popular': False,
        'discount': 0,
        'is_active': True,
        'type_label': 'Пакет',
        'accent': 'Гибкий график',
    },
    {
        'slug': 'package-20',
        'name': 'Пакет 20 тренировок',
        'type': 'package',
        'price': 8990,
        'duration_days': 90,
        'visits_count': 20,
        'description': 'Выгодный пакет для стабильных тренировок несколько раз в неделю с хорошей ценой за визит.',
        'summary': 'Рациональный выбор для тех, кто уже вошел в тренировочный ритм.',
        'features': [
            '20 посещений в течение 90 дней',
            'Все тренировочные зоны и групповые классы',
            'Приоритет на вечерние слоты',
            'Расширенная заморозка до 14 дней',
            'Бонусная консультация по тренировочному плану',
        ],
        'color': '#ec4899',
        'is_popular': False,
        'discount': 10,
        'is_active': True,
        'type_label': 'Пакет',
        'accent': 'Самая выгодная цена за визит',
    },
]


def sync_abonement_catalog():
    existing = Abonement.query.all()
    changed = False

    def find_match(spec):
        for abonement in existing:
            if spec['slug'] == 'package-10' and abonement.type == 'package' and abonement.visits_count == 10:
                return abonement
            if spec['slug'] == 'package-20' and abonement.type == 'package' and abonement.visits_count == 20:
                return abonement
            if spec['slug'] not in ('package-10', 'package-20') and abonement.type == spec['type']:
                return abonement
        return None

    for spec in ABONEMENT_CATALOG:
        abonement = find_match(spec)
        if abonement is None:
            abonement = Abonement()
            db.session.add(abonement)
            existing.append(abonement)
            changed = True

        features_text = '\n'.join(spec['features'])
        for field in ('name', 'type', 'price', 'duration_days', 'visits_count', 'description', 'color', 'is_popular', 'discount', 'is_active'):
            if getattr(abonement, field) != spec[field]:
                setattr(abonement, field, spec[field])
                changed = True

        if abonement.features != features_text:
            abonement.features = features_text
            changed = True

    if changed:
        db.session.commit()


def build_abonement_view(abonement):
    spec = next((item for item in ABONEMENT_CATALOG if item['name'] == abonement.name), None)
    features = spec['features'] if spec else abonement.features_list

    return {
        'id': abonement.id,
        'name': abonement.name,
        'type': abonement.type,
        'type_label': spec['type_label'] if spec else 'Абонемент',
        'accent': spec['accent'] if spec else 'Удобный формат для тренировок',
        'summary': spec['summary'] if spec else abonement.description,
        'description': abonement.description,
        'price': abonement.price,
        'final_price': abonement.final_price,
        'duration_days': abonement.duration_days,
        'duration_text': abonement.duration_text,
        'visits_count': abonement.visits_count,
        'visits_text': abonement.visits_text,
        'price_per_visit': abonement.price_per_visit,
        'features': features,
        'color': abonement.color,
        'is_popular': abonement.is_popular,
        'discount': abonement.discount,
    }


def build_payment_history(user_abonements):
    payment_history = []

    for user_abonement in user_abonements:
        payment_details = parse_payment_info(user_abonement.payment_info)
        if not payment_details:
            continue

        payment_history.append({
            'abonement_name': user_abonement.abonement.name,
            'purchase_date': user_abonement.purchase_date,
            'details': payment_details,
        })

    return payment_history


def build_abonement_notifications(user_abonements):
    notifications = []

    for user_abonement in user_abonements:
        if user_abonement.is_frozen:
            notifications.append({
                'level': 'info',
                'title': 'Абонемент на заморозке',
                'text': f'{user_abonement.abonement.name} заморожен до {user_abonement.frozen_until.strftime("%d.%m.%Y")}.',
            })
        elif user_abonement.nearing_expiration:
            notifications.append({
                'level': 'warning',
                'title': 'Скоро закончится абонемент',
                'text': f'{user_abonement.abonement.name} действует еще {user_abonement.days_remaining} дн.',
            })

    return notifications


def get_safe_next_url():
    next_url = request.args.get('next') or request.form.get('next')
    if not next_url:
        return None

    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc or not next_url.startswith('/'):
        return None

    return next_url


def build_workout_notifications(user_id):
    now = datetime.utcnow()
    next_day = now + timedelta(hours=24)
    reminders = (
        Booking.query.join(Workout)
        .filter(Booking.user_id == user_id, Workout.start_time >= now, Workout.start_time <= next_day)
        .order_by(Workout.start_time)
        .all()
    )
    notifications = []

    for booking in reminders:
        workout = booking.workout
        notifications.append({
            'title': 'Напоминание о тренировке',
            'text': f'{workout.workout_type.name} сегодня/завтра в {workout.start_time.strftime("%H:%M")} с тренером {workout.trainer.first_name} {workout.trainer.last_name}.',
        })

    return notifications


@abonements_bp.route('/')
def index():
    sync_abonement_catalog()
    sort_order = {'trial': 0, 'basic': 1, 'package': 2, 'vip': 3}
    abonement_models = sorted(
        Abonement.query.filter_by(is_active=True).all(),
        key=lambda item: (sort_order.get(item.type, 99), item.price),
    )
    abonements = [build_abonement_view(item) for item in abonement_models]
    return render_template(
        'abonements/index.html',
        abonements=abonements,
        next_url=get_safe_next_url(),
        title='Наши абонементы',
    )


@abonements_bp.route('/abonement/<int:abonement_id>')
def abonement_detail(abonement_id):
    sync_abonement_catalog()
    abonement = Abonement.query.get_or_404(abonement_id)
    return render_template(
        'abonements/abonement_detail.html',
        abonement=build_abonement_view(abonement),
        next_url=get_safe_next_url(),
        title=abonement.name,
    )


@abonements_bp.route('/api/abonements')
def api_abonements():
    sync_abonement_catalog()
    abonements = Abonement.query.filter_by(is_active=True).all()
    return jsonify([build_abonement_view(item) for item in abonements])


@abonements_bp.route('/api/abonement/<int:abonement_id>')
def api_abonement_detail(abonement_id):
    sync_abonement_catalog()
    abonement = Abonement.query.get_or_404(abonement_id)
    return jsonify(build_abonement_view(abonement))


@abonements_bp.route('/compare')
def compare_abonements():
    sync_abonement_catalog()
    views = [build_abonement_view(item) for item in Abonement.query.filter_by(is_active=True).all()]
    comparison = {}
    for item in views:
        comparison[item['name']] = {
            'Цена': f"{item['final_price']} ₽",
            'Длительность': item['duration_text'],
            'Посещения': item['visits_text'],
            'Цена за визит': f"{item['price_per_visit']} ₽" if item['price_per_visit'] > 0 else '—',
            'Скидка': f"{item['discount']}%" if item['discount'] > 0 else '—',
        }
    return render_template('abonements/compare.html', comparison=comparison, title='Сравнение абонементов')


@abonements_bp.route('/filter', methods=['POST'])
def filter_abonements():
    sync_abonement_catalog()
    filter_type = request.json.get('type', 'all')

    if filter_type == 'all':
        abonements = Abonement.query.filter_by(is_active=True).all()
    else:
        abonements = Abonement.query.filter_by(is_active=True, type=filter_type).all()

    sort_order = {'trial': 0, 'basic': 1, 'package': 2, 'vip': 3}
    abonements = sorted(abonements, key=lambda item: (sort_order.get(item.type, 99), item.price))
    return jsonify([build_abonement_view(item) for item in abonements])


@abonements_bp.route('/buy/<int:abonement_id>', methods=['GET', 'POST'])
@login_required
def buy_abonement(abonement_id):
    sync_abonement_catalog()
    abonement_model = Abonement.query.get_or_404(abonement_id)
    abonement = build_abonement_view(abonement_model)
    form = AbonementPaymentForm()
    next_url = get_safe_next_url()

    if form.validate_on_submit():
        processor = TestPaymentProcessor()

        try:
            payment_result = processor.process_test_payment(
                amount=abonement['final_price'],
                user_id=current_user.id,
                card_number=form.card_number.data,
                cardholder_name=form.cardholder_name.data,
                expiry_month=form.expiry_month.data,
                expiry_year=form.expiry_year.data,
                cvv=form.cvv.data,
            )
        except PaymentValidationError as error:
            form.card_number.errors.append(str(error))
            return render_template('abonements/buy.html', abonement=abonement, form=form, next_url=next_url, title=f"Купить {abonement['name']}")

        expiration_date = datetime.utcnow() + timedelta(days=abonement['duration_days'])
        user_abonement = UserAbonement(
            user_id=current_user.id,
            abonement_id=abonement_model.id,
            purchase_date=datetime.utcnow(),
            expiration_date=expiration_date,
            visits_remaining=abonement['visits_count'] if abonement['visits_count'] > 0 else None,
            is_active=True,
            payment_info=(
                f"online-test:{payment_result['transaction_id']};"
                f"amount={payment_result['amount']};"
                f"card=****{payment_result['card_last4']};"
                f"processed_at={payment_result['processed_at']}"
            ),
        )

        db.session.add(user_abonement)
        db.session.commit()

        flash(f'Онлайн-оплата прошла успешно. Абонемент "{abonement["name"]}" уже активирован!', 'success')
        return redirect(next_url or url_for('abonements.my_abonements'))

    return render_template('abonements/buy.html', abonement=abonement, form=form, next_url=next_url, title=f"Купить {abonement['name']}")


@abonements_bp.route('/extend/<int:user_abonement_id>', methods=['POST'])
@login_required
def extend_abonement(user_abonement_id):
    user_abonement = UserAbonement.query.get_or_404(user_abonement_id)
    if user_abonement.user_id != current_user.id:
        flash('Нельзя управлять чужим абонементом.', 'danger')
        return redirect(url_for('abonements.my_abonements'))

    extension_days = user_abonement.abonement.duration_days
    start_point = max(datetime.utcnow(), user_abonement.expiration_date)
    user_abonement.expiration_date = start_point + timedelta(days=extension_days)
    user_abonement.extension_count = (user_abonement.extension_count or 0) + 1
    db.session.commit()

    flash(f'Абонемент продлен еще на {extension_days} дн.', 'success')
    return redirect(url_for('abonements.my_abonements'))


@abonements_bp.route('/freeze/<int:user_abonement_id>', methods=['POST'])
@login_required
def freeze_abonement(user_abonement_id):
    user_abonement = UserAbonement.query.get_or_404(user_abonement_id)
    if user_abonement.user_id != current_user.id:
        flash('Нельзя управлять чужим абонементом.', 'danger')
        return redirect(url_for('abonements.my_abonements'))

    if not user_abonement.can_freeze:
        flash('Этот абонемент сейчас нельзя заморозить.', 'warning')
        return redirect(url_for('abonements.my_abonements'))

    freeze_days = min(7, user_abonement.freeze_days_available)
    now = datetime.utcnow()
    user_abonement.frozen_from = now
    user_abonement.frozen_until = now + timedelta(days=freeze_days)
    user_abonement.expiration_date = user_abonement.expiration_date + timedelta(days=freeze_days)
    user_abonement.freeze_days_used = (user_abonement.freeze_days_used or 0) + freeze_days
    db.session.commit()

    flash(f'Абонемент заморожен на {freeze_days} дн.', 'info')
    return redirect(url_for('abonements.my_abonements'))


@abonements_bp.route('/my')
@login_required
def my_abonements():
    sync_abonement_catalog()
    user_abonements = UserAbonement.query.filter_by(user_id=current_user.id).order_by(
        UserAbonement.purchase_date.desc()
    ).all()
    payment_history = build_payment_history(user_abonements)
    abonement_notifications = build_abonement_notifications(user_abonements)
    workout_notifications = build_workout_notifications(current_user.id)

    return render_template(
        'abonements/my_abonements.html',
        user_abonements=user_abonements,
        payment_history=payment_history,
        abonement_notifications=abonement_notifications,
        workout_notifications=workout_notifications,
        title='Мои абонементы'
    )
