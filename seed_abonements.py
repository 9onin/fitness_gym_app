from app import create_app
from models.database import db
from models.models import Abonement


app = create_app()


CATALOG = [
    {
        'name': 'Пробный старт',
        'type': 'trial',
        'price': 990,
        'duration_days': 7,
        'visits_count': 3,
        'description': 'Неделя, чтобы познакомиться с клубом, тренерами и вашим будущим ритмом занятий.',
        'features': '3 посещения в любые будние дни\nВводная консультация тренера\nПервичная диагностика состава тела\nДоступ в тренажерный зал и кардиозону\nГрупповые занятия начального уровня',
        'color': '#22c55e',
        'is_popular': False,
        'discount': 0,
        'is_active': True,
    },
    {
        'name': 'Базовый безлимит',
        'type': 'basic',
        'price': 3990,
        'duration_days': 30,
        'visits_count': 0,
        'description': 'Комфортный месячный тариф для тех, кто хочет тренироваться регулярно и без ограничений.',
        'features': 'Безлимитное посещение клуба\nВсе тренажерные зоны и кардиопространство\nГрупповые занятия по расписанию\nДоступ в раздевалки и душевые\nОдна персональная консультация в месяц',
        'color': '#4f46e5',
        'is_popular': True,
        'discount': 10,
        'is_active': True,
    },
    {
        'name': 'VIP Премиум',
        'type': 'vip',
        'price': 8990,
        'duration_days': 30,
        'visits_count': 0,
        'description': 'Премиальный формат с персональным сопровождением и расширенным набором восстановительных услуг.',
        'features': 'Безлимит на все зоны клуба\n2 персональные тренировки в подарок\nVIP-раздевалка и полотенца\nДоступ в SPA, хаммам и сауну\nПриоритетная запись на популярные тренировки',
        'color': '#7c3aed',
        'is_popular': False,
        'discount': 15,
        'is_active': True,
    },
    {
        'name': 'Пакет 10 тренировок',
        'type': 'package',
        'price': 4990,
        'duration_days': 60,
        'visits_count': 10,
        'description': 'Гибкий пакет для тех, кто тренируется в удобном темпе и не хочет переплачивать за безлимит.',
        'features': '10 посещений в течение 60 дней\nДоступ ко всем зонам клуба\nГрупповые занятия включены\nЗаморозка до 7 дней\nЭлектронный трекер остатка посещений',
        'color': '#f59e0b',
        'is_popular': False,
        'discount': 0,
        'is_active': True,
    },
    {
        'name': 'Пакет 20 тренировок',
        'type': 'package',
        'price': 8990,
        'duration_days': 90,
        'visits_count': 20,
        'description': 'Выгодный пакет для стабильных тренировок несколько раз в неделю с хорошей ценой за визит.',
        'features': '20 посещений в течение 90 дней\nВсе тренировочные зоны и групповые классы\nПриоритет на вечерние слоты\nРасширенная заморозка до 14 дней\nБонусная консультация по тренировочному плану',
        'color': '#ec4899',
        'is_popular': False,
        'discount': 10,
        'is_active': True,
    },
]


with app.app_context():
    db.create_all()

    if Abonement.query.count() == 0:
        for item in CATALOG:
            db.session.add(Abonement(**item))

        db.session.commit()
        print(f'Добавлено {len(CATALOG)} абонементов')
    else:
        print(f'Уже есть {Abonement.query.count()} абонементов')
