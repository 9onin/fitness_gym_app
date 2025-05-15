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
    
    def __repr__(self):
        return f'<Booking {self.id} User:{self.user_id} Workout:{self.workout_id}>' 