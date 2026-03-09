from flask import Blueprint, render_template, jsonify, request
from abonements import AbonementManager


abonements_bp = Blueprint('abonements', __name__)


# Инициализация менеджера абонементов
abonement_manager = AbonementManager()  # TODO replace to database


@abonements_bp.route('/')
def index():
    """Главная страница со всеми абонементами"""
    abonements = abonement_manager.get_all_abonements()
    return render_template('abonements/index.html',
                           abonements=abonements,
                           title="Наши абонементы")


@abonements_bp.route('/abonement/<int:abonement_id>')
def abonement_detail(abonement_id):
    """Детальная страница абонемента"""
    abonement = abonement_manager.get_abonement_by_id(abonement_id)
    if abonement:
        return render_template('abonements/abonement_detail.html',
                               abonement=abonement,
                               title=abonement.name)
    return "Абонемент не найден", 404


@abonements_bp.route('/api/abonements')
def api_abonements():
    """API для получения списка абонементов в JSON"""
    abonements = abonement_manager.get_all_abonements()
    return jsonify([a.to_dict() for a in abonements])


@abonements_bp.route('/api/abonement/<int:abonement_id>')
def api_abonement_detail(abonement_id):
    """API для получения деталей абонемента"""
    abonement = abonement_manager.get_abonement_by_id(abonement_id)
    if abonement:
        return jsonify(abonement.to_dict())
    return jsonify({'error': 'Абонемент не найден'}), 404


@abonements_bp.route('/compare')
def compare_abonements():
    """Страница сравнения абонементов"""
    comparison = abonement_manager.compare_abonements()
    return render_template('abonements/compare.html',
                           comparison=comparison,
                           title="Сравнение абонементов")


@abonements_bp.route('/filter', methods=['POST'])
def filter_abonements():
    """Фильтрация абонементов"""
    filter_type = request.json.get('type', 'all')

    if filter_type == 'all':
        abonements = abonement_manager.get_all_abonements()
    else:
        abonements = abonement_manager.get_abonements_by_type(filter_type)

    return jsonify([a.to_dict() for a in abonements])
