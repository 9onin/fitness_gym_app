from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import Abonement, UserAbonement
from models.database import db
from datetime import datetime, timedelta


abonements_bp = Blueprint('abonements', __name__)


@abonements_bp.route('/')
def index():
    """Главная страница со всеми абонементами"""
    abonements = Abonement.query.filter_by(is_active=True).all()
    return render_template('abonements/index.html',
                       abonements=abonements,
                       title="Наши абонементы")


@abonements_bp.route('/abonement/<int:abonement_id>')
def abonement_detail(abonement_id):
    """Детальная страница абонемента"""
    abonement = Abonement.query.get_or_404(abonement_id)
    return render_template('abonements/abonement_detail.html',
                       abonement=abonement,
                       title=abonement.name)


@abonements_bp.route('/api/abonements')
def api_abonements():
    """API для получения списка абонементов в JSON"""
    abonements = Abonement.query.filter_by(is_active=True).all()
    return jsonify([a.to_dict() for a in abonements])


@abonements_bp.route('/api/abonement/<int:abonement_id>')
def api_abonement_detail(abonement_id):
    """API для получения деталей абонемента"""
    abonement = Abonement.query.get_or_404(abonement_id)
    return jsonify(abonement.to_dict())


@abonements_bp.route('/compare')
def compare_abonements():
    """Страница сравнения абонементов"""
    abonements = Abonement.query.filter_by(is_active=True).all()
    comparison = {}
    for a in abonements:
        comparison[a.name] = {
            'Цена': f"{a.final_price} ₽",
            'Длительность': a.duration_text,
            'Посещения': a.visits_text,
            'Цена за визит': f"{a.price_per_visit} ₽" if a.price_per_visit > 0 else "—",
            'Скидка': f"{a.discount}%" if a.discount > 0 else "—"
        }
    return render_template('abonements/compare.html',
                       comparison=comparison,
                       title="Сравнение абонементов")


@abonements_bp.route('/filter', methods=['POST'])
def filter_abonements():
    """Фильтрация абонементов"""
    filter_type = request.json.get('type', 'all')

    if filter_type == 'all':
        abonements = Abonement.query.filter_by(is_active=True).all()
    else:
        abonements = Abonement.query.filter_by(is_active=True, type=filter_type).all()

    return jsonify([a.to_dict() for a in abonements])


@abonements_bp.route('/buy/<int:abonement_id>', methods=['GET', 'POST'])
@login_required
def buy_abonement(abonement_id):
    """Страница покупки абонемента"""
    abonement = Abonement.query.get_or_404(abonement_id)
    
    if request.method == 'POST':
        user_plan = current_user.email
        
        if user_plan == 'simulate':
            flash('Это симуляция оплаты', 'info')
        
        expiration_date = datetime.utcnow() + timedelta(days=abonement.duration_days)
        
        user_abonement = UserAbonement(
            user_id=current_user.id,
            abonement_id=abonement.id,
            purchase_date=datetime.utcnow(),
            expiration_date=expiration_date,
            visits_remaining=abonement.visits_count if abonement.visits_count > 0 else None,
            is_active=True,
            payment_info=f"Payment: {abonement.final_price} RUB"
        )
        
        db.session.add(user_abonement)
        db.session.commit()
        
        flash(f'Абонемент "{abonement.name}" успешно приобретен!', 'success')
        return redirect(url_for('user.my_abonements'))
    
    return render_template('abonements/buy.html',
                         abonement=abonement,
                         title=f"Купить {abonement.name}")


@abonements_bp.route('/my')
@login_required
def my_abonements():
    """Мои абонементы пользователя"""
    user_abonements = UserAbonement.query.filter_by(user_id=current_user.id).order_by(
        UserAbonement.purchase_date.desc()
    ).all()
    return render_template('abonements/my_abonements.html',
                       user_abonements=user_abonements,
                       title="Мои абонементы")