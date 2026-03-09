from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict
import json

@dataclass
class Abonement:
    """Класс для описания абонемента"""
    id: int
    name: str
    type: str  # 'trial', 'basic', 'vip'
    price: int
    duration_days: int
    visits_count: int  # 0 = безлимит
    description: str
    features: List[str]
    color: str  # для оформления
    is_popular: bool = False
    discount: int = 0  # скидка в процентах
    
    @property
    def final_price(self) -> int:
        """Цена со скидкой"""
        if self.discount > 0:
            return int(self.price * (100 - self.discount) / 100)
        return self.price
    
    @property
    def price_per_visit(self) -> int:
        """Цена за одно посещение"""
        if self.visits_count > 0:
            return int(self.final_price / self.visits_count)
        return 0
    
    @property
    def duration_text(self) -> str:
        """Текст длительности"""
        if self.duration_days == 1:
            return "1 день"
        elif self.duration_days < 30:
            return f"{self.duration_days} дней"
        elif self.duration_days == 30:
            return "1 месяц"
        elif self.duration_days == 90:
            return "3 месяца"
        elif self.duration_days == 180:
            return "6 месяцев"
        elif self.duration_days == 365:
            return "1 год"
        else:
            return f"{self.duration_days} дней"
    
    @property
    def visits_text(self) -> str:
        """Текст количества посещений"""
        if self.visits_count == 0:
            return "Безлимит"
        elif self.visits_count == 1:
            return "1 тренировка"
        elif self.visits_count < 5:
            return f"{self.visits_count} тренировки"
        else:
            return f"{self.visits_count} тренировок"
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'price': self.price,
            'final_price': self.final_price,
            'duration_days': self.duration_days,
            'duration_text': self.duration_text,
            'visits_count': self.visits_count,
            'visits_text': self.visits_text,
            'description': self.description,
            'features': self.features,
            'color': self.color,
            'is_popular': self.is_popular,
            'discount': self.discount,
            'price_per_visit': self.price_per_visit
        }


class AbonementManager:
    """Менеджер для работы с абонементами"""
    
    def __init__(self):
        self.abonements = self._create_abonements()
    
    def _create_abonements(self) -> List[Abonement]:
        """Создание трёх видов абонементов"""
        return [
            # Пробный абонемент
            Abonement(
                id=1,
                name="Пробный",
                type="trial",
                price=990,
                duration_days=7,
                visits_count=3,
                description="Идеально для знакомства с клубом",
                features=[
                    "3 персональные тренировки",
                    "Консультация тренера",
                    "Составление программы питания",
                    "Фитнес-тестирование",
                    "Доступ в раздевалку",
                    "Бутилированная вода"
                ],
                color="#4CAF50",
                is_popular=False,
                discount=0
            ),
            
            # Базовый абонемент (самый популярный)
            Abonement(
                id=2,
                name="Базовый",
                type="basic",
                price=3990,
                duration_days=30,
                visits_count=0,  # безлимит
                description="Оптимальный выбор для регулярных тренировок",
                features=[
                    "Безлимитное посещение",
                    "Все тренажерные зоны",
                    "Групповые занятия",
                    "Кардиозона",
                    "Солярий (5 мин/день)",
                    "SPA-зона",
                    "Полотенца в подарок",
                    "Фитнес-браслет"
                ],
                color="#2196F3",
                is_popular=True,
                discount=15  # скидка 15%
            ),
            
            # VIP абонемент
            Abonement(
                id=3,
                name="VIP",
                type="vip",
                price=8990,
                duration_days=30,
                visits_count=0,  # безлимит
                description="Максимальный комфорт и премиум-условия",
                features=[
                    "Безлимитное посещение",
                    "Персональный тренер",
                    "VIP-раздевалка",
                    "Массаж (4 сеанса)",
                    "SPA-комплекс",
                    "Бассейн",
                    "Хамам и сауна",
                    "Фитнес-бар (напитки включены)",
                    "Парковка",
                    "Гостевые визиты (2 в месяц)"
                ],
                color="#9C27B0",
                is_popular=False,
                discount=20  # скидка 20%
            )
        ]
    
    def get_all_abonements(self) -> List[Abonement]:
        """Получить все абонементы"""
        return self.abonements
    
    def get_abonement_by_id(self, abonement_id: int) -> Abonement:
        """Получить абонемент по ID"""
        for abonement in self.abonements:
            if abonement.id == abonement_id:
                return abonement
        return None
    
    def get_abonements_by_type(self, abonement_type: str) -> List[Abonement]:
        """Получить абонементы по типу"""
        return [a for a in self.abonements if a.type == abonement_type]
    
    def compare_abonements(self) -> Dict:
        """Сравнение всех абонементов"""
        comparison = {}
        for abonement in self.abonements:
            comparison[abonement.name] = {
                'Цена': f"{abonement.final_price} ₽",
                'Длительность': abonement.duration_text,
                'Посещения': abonement.visits_text,
                'Цена за визит': f"{abonement.price_per_visit} ₽" if abonement.price_per_visit > 0 else "—",
                'Скидка': f"{abonement.discount}%" if abonement.discount > 0 else "—"
            }
        return comparison