from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """
    Модель пользователя
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    client_status = db.Column(db.String(20), nullable=False, default='new')
    fitness_goal = db.Column(db.String(255), nullable=True)
    manager_notes = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с другими таблицами
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """
        Установка хеша пароля
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Проверка пароля
        """
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def status_label(self):
        labels = {
            'new': 'Новый',
            'active': 'Активный',
            'frozen': 'Заморожен',
            'inactive': 'Неактивный',
            'vip': 'VIP',
        }
        return labels.get(self.client_status or 'new', 'Новый')

    def __repr__(self):
        return f'<User {self.email}>'

class Trainer(db.Model):
    """
    Модель тренера
    """
    __tablename__ = 'trainers'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    specialization = db.Column(db.String(100), nullable=False)
    profile = db.Column(db.Text)
    
    # Отношения с другими таблицами
    workouts = db.relationship('Workout', backref='trainer', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Trainer {self.first_name} {self.last_name}>'

class WorkoutType(db.Model):
    """
    Модель типа тренировки
    """
    __tablename__ = 'workout_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Отношения с другими таблицами
    workouts = db.relationship('Workout', backref='workout_type', lazy=True)
    
    def __repr__(self):
        return f'<WorkoutType {self.name}>'

class Workout(db.Model):
    """
    Модель тренировки
    """
    __tablename__ = 'workouts'
    
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    workout_type_id = db.Column(db.Integer, db.ForeignKey('workout_types.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    max_participants = db.Column(db.Integer, default=10)
    description = db.Column(db.Text)
    
    # Отношения с другими таблицами
    bookings = db.relationship('Booking', backref='workout', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Workout {self.id} {self.start_time}>'
    
    @property
    def available_spots(self):
        """
        Расчет доступных мест
        """
        return self.max_participants - len(self.bookings)
    
    @property
    def is_full(self):
        """
        Проверка, заполнена ли тренировка
        """
        return self.available_spots <= 0

class Booking(db.Model):
    """
    Модель записи на тренировку
    """
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    visit_charged = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Booking {self.id} User:{self.user_id} Workout:{self.workout_id}>'


class Abonement(db.Model):
    """
    Модель абонемента
    """
    __tablename__ = 'abonements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    visits_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    color = db.Column(db.String(20), default='#4CAF50')
    is_popular = db.Column(db.Boolean, default=False)
    discount = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def final_price(self):
        """Цена со скидкой"""
        if self.discount > 0:
            return int(self.price * (100 - self.discount) / 100)
        return self.price
    
    @property
    def price_per_visit(self):
        """Цена за одно посещение"""
        if self.visits_count > 0:
            return int(self.final_price / self.visits_count)
        return 0
    
    @property
    def duration_text(self):
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
    def visits_text(self):
        """Текст количества посещений"""
        if self.visits_count == 0:
            return "Безлимит"
        elif self.visits_count == 1:
            return "1 тренировка"
        elif self.visits_count < 5:
            return f"{self.visits_count} тренировки"
        else:
            return f"{self.visits_count} тренировок"
    
    def to_dict(self):
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
            'features': self.features_list,
            'color': self.color,
            'is_popular': self.is_popular,
            'discount': self.discount,
            'price_per_visit': self.price_per_visit
        }
    
    @property
    def features_list(self):
        """Список возможностей"""
        if not self.features:
            return []
        return [f.strip() for f in self.features.split('\n') if f.strip()]
    
    def __repr__(self):
        return f'<Abonement {self.name}>'


class UserAbonement(db.Model):
    """
    Модель купленного абонемента пользователя
    """
    __tablename__ = 'user_abonements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    abonement_id = db.Column(db.Integer, db.ForeignKey('abonements.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=False)
    visits_remaining = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    payment_info = db.Column(db.Text)
    
    user = db.relationship('User', backref='abonements')
    abonement = db.relationship('Abonement')
    
    @property
    def is_valid(self):
        """Проверка валидности абонемента"""
        if not self.is_active:
            return False
        if datetime.utcnow() > self.expiration_date:
            return False
        if self.visits_remaining is not None and self.visits_remaining <= 0:
            return False
        return True
    
    @property
    def is_expired(self):
        """Проверка истечения срока"""
        return datetime.utcnow() > self.expiration_date
    
    @property
    def visits_used(self):
        """Количество использованных посещений"""
        if self.visits_remaining is None:
            return None
        return self.abonement.visits_count - self.visits_remaining
    
    @property
    def days_remaining(self):
        """Оставшиеся дни"""
        if self.is_expired:
            return 0
        delta = self.expiration_date - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f'<UserAbonement {self.id} User:{self.user_id} Abonement:{self.abonement_id}>' 
