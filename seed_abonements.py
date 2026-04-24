from app import create_app
from models.database import db
from models.models import Abonement

app = create_app()

with app.app_context():
    db.create_all()
    
    if Abonement.query.count() == 0:
        abonements = [
            Abonement(
                name="Пробный",
                type="trial",
                price=990,
                duration_days=7,
                visits_count=3,
                description="Идеально для знакомства с клубом",
                features="3 персональные тренировки\nКонсультация тренера\nСоставление программы питания\nФитнес-тестирование\nДоступ в раздевалку\nБутилированная вода",
                color="#4CAF50",
                is_popular=False,
                discount=0,
                is_active=True
            ),
            Abonement(
                name="Базовый",
                type="basic",
                price=3990,
                duration_days=30,
                visits_count=0,
                description="Оптимальный выбор для регулярных тренировок",
                features="Безлимитное посещение\nВсе тренажерные зоны\nГрупповые занятия\nКардиозона\nСолярий (5 мин/день)\nSPA-зона\nПолотенца в подарок\nФитнес-браслет",
                color="#2196F3",
                is_popular=True,
                discount=15,
                is_active=True
            ),
            Abonement(
                name="VIP",
                type="vip",
                price=8990,
                duration_days=30,
                visits_count=0,
                description="Максимальный комфорт и премиум-услуги",
                features="Безлимитное посещение\nПерсональный тренер\nVIP-раздевалка\nМассаж (4 сеанса)\nSPA-комплекс\nБассейн\nХамам и сауна\nФитнес-бар (напитки включены)\nПарковка\nГостевые визиты (2 в месяц)",
                color="#9C27B0",
                is_popular=False,
                discount=20,
                is_active=True
            ),
            Abonement(
                name="Пакет 10",
                type="package",
                price=4990,
                duration_days=60,
                visits_count=10,
                description="10 тренировок с гибким графиком",
                features="10 тренировок\nДоступ ко всем зонам\nГрупповые занятия\nЛокер\nПолотенце",
                color="#FF9800",
                is_popular=False,
                discount=0,
                is_active=True
            ),
            Abonement(
                name="Пакет 20",
                type="package",
                price=8990,
                duration_days=90,
                visits_count=20,
                description="20 тренировок - выгодное предложение",
                features="20 тренировок\nДоступ ко всем зонам\nГрупповые занятия\nVIP-локер\nПолотенце\nФитнес-ко��сультация",
                color="#E91E63",
                is_popular=False,
                discount=10,
                is_active=True
            ),
        ]
        
        for a in abonements:
            db.session.add(a)
        
        db.session.commit()
        print(f"Добавлено {len(abonements)} абонементов")
    else:
        print(f"Уже есть {Abonement.query.count()} абонементов")