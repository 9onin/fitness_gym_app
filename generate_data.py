#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для генерации тренировок и пользователей с записями на тренировки
"""

import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker
import random
import string

# Добавляем родительский каталог в путь импорта для импорта модулей приложения
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from models.database import db
from models.models import User, Trainer, WorkoutType, Workout, Booking

# Инициализируем Faker для генерации случайных данных
fake = Faker('ru_RU')

def generate_password(length=10):
    """Генерирует случайный пароль"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

def generate_data():
    """
    Генерирует тренировки и пользователей с записями на тренировки
    """
    app = create_app()
    
    with app.app_context():
        # Получаем все существующие типы тренировок
        workout_types = WorkoutType.query.all()
        print(f"Найдено {len(workout_types)} типов тренировок:")
        for i, wt in enumerate(workout_types):
            print(f"  {i+1}. {wt.name} (ID: {wt.id})")
        
        if not workout_types:
            print("ОШИБКА: В базе данных нет типов тренировок")
            print("Хотите создать тестовые типы тренировок? (y/n)")
            response = input().strip().lower()
            if response == 'y':
                # Создаем тестовые типы тренировок
                print("Создание тестовых типов тренировок...")
                test_types = [
                    "Силовая тренировка", "Кардио", "Йога", "Пилатес", "Зумба",
                    "Бокс", "Кроссфит", "Стретчинг", "Аквааэробика", "Танцы",
                    "TRX", "Функциональный тренинг", "Спиннинг", "Тай-бо", "Степ-аэробика",
                    "Табата", "Калланетика", "Бодифлекс", "Боди-памп", "ЛФК"
                ]
                for type_name in test_types:
                    wt = WorkoutType(name=type_name, description=f"Описание для {type_name}")
                    db.session.add(wt)
                
                db.session.commit()
                workout_types = WorkoutType.query.all()
                print(f"Создано {len(workout_types)} типов тренировок")
            else:
                return False
        
        # Получаем всех существующих тренеров
        trainers = Trainer.query.all()
        print(f"Найдено {len(trainers)} тренеров:")
        for i, trainer in enumerate(trainers):
            print(f"  {i+1}. {trainer.first_name} {trainer.last_name} (ID: {trainer.id})")
        
        if not trainers or len(trainers) < 3:
            print("ВНИМАНИЕ: В базе данных меньше 3 тренеров")
            print("Хотите создать тестовых тренеров? (y/n)")
            response = input().strip().lower()
            if response == 'y':
                # Создаем тестовых тренеров
                print("Создание тестовых тренеров...")
                test_trainers = [
                    {"first_name": "Иван", "last_name": "Петров", "specialization": "Силовые тренировки", "experience_years": 5},
                    {"first_name": "Мария", "last_name": "Иванова", "specialization": "Йога", "experience_years": 7},
                    {"first_name": "Алексей", "last_name": "Сидоров", "specialization": "Кроссфит", "experience_years": 4}
                ]
                for trainer_data in test_trainers:
                    trainer = Trainer(
                        first_name=trainer_data["first_name"],
                        last_name=trainer_data["last_name"],
                        specialization=trainer_data["specialization"],
                        experience_years=trainer_data["experience_years"]
                    )
                    db.session.add(trainer)
                
                db.session.commit()
                trainers = Trainer.query.all()
                print(f"Создано {len(trainers)} тренеров")
            else:
                if not trainers:
                    print("ОШИБКА: Без тренеров невозможно создать тренировки")
                    return False
                print("Продолжаем с имеющимися тренерами")
        
        # Число тренировок для каждого типа
        workouts_per_type = 15
        total_workouts = len(workout_types) * workouts_per_type
        
        print(f"Будет создано {total_workouts} тренировок ({workouts_per_type} для каждого типа)")
        
        # Начальная дата для тренировок (1 мая 2025)
        start_date = datetime(2025, 5, 1, 9, 0)
        
        # Генерируем тренировки
        workouts = []
        current_date = start_date
        
        print("Генерация тренировок...")
        
        # Продолжительности тренировок (в минутах)
        durations = [45, 60, 90]
        
        # Временные слоты для тренировок
        time_slots = [
            (9, 0),    # 9:00
            (10, 30),  # 10:30
            (12, 0),   # 12:00
            (14, 0),   # 14:00
            (15, 30)   # 15:30
        ]
        
        # Распределяем тренировки по типам
        count = 0
        for wt in workout_types:
            for _ in range(workouts_per_type):
                # Выбираем случайного тренера
                trainer = random.choice(trainers)
                
                # Выбираем случайную продолжительность
                duration = random.choice(durations)
                
                # Выбираем случайный временной слот
                hour, minute = random.choice(time_slots)
                
                # Устанавливаем время начала
                workout_start = current_date.replace(hour=hour, minute=minute)
                
                # Вычисляем время окончания
                workout_end = workout_start + timedelta(minutes=duration)
                
                # Проверяем, что время окончания не превышает 17:00
                if workout_end.hour > 17 or (workout_end.hour == 17 and workout_end.minute > 0):
                    # Если превышает, переносим на следующий день
                    current_date = current_date + timedelta(days=1)
                    workout_start = current_date.replace(hour=hour, minute=minute)
                    workout_end = workout_start + timedelta(minutes=duration)
                
                # Создаем тренировку
                workout = Workout(
                    trainer_id=trainer.id,
                    workout_type_id=wt.id,
                    start_time=workout_start,
                    end_time=workout_end,
                    max_participants=20,  # Максимум участников для каждой тренировки
                    description=f"Тренировка типа '{wt.name}' с тренером {trainer.first_name} {trainer.last_name}"
                )
                
                workouts.append(workout)
                count += 1
                if count % 20 == 0:
                    print(f"Создано {count} тренировок из {total_workouts}...")
                
                # Переходим к следующему дню для равномерного распределения
                current_date = current_date + timedelta(days=1)
        
        # Добавляем тренировки в базу данных
        db.session.add_all(workouts)
        db.session.commit()
        
        print(f"Сгенерировано {len(workouts)} тренировок")
        
        # Создаем 20 пользователей
        num_users = 20
        users = []
        user_credentials = []
        
        print(f"Генерация {num_users} пользователей...")
        
        for i in range(1, num_users + 1):
            # Генерируем данные пользователя
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"user{i}@example.com"
            password = generate_password()
            
            # Создаем пользователя
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            
            users.append(user)
            user_credentials.append({
                'email': email,
                'password': password,
                'name': f"{first_name} {last_name}"
            })
            
            if i % 5 == 0:
                print(f"Создано {i} пользователей из {num_users}...")
        
        # Добавляем пользователей в базу данных
        db.session.add_all(users)
        db.session.commit()
        
        # Получаем ID созданных пользователей
        for i, user in enumerate(users):
            user_credentials[i]['id'] = user.id
        
        print(f"Сгенерировано {len(users)} пользователей")
        
        # Создаем записи на тренировки
        print("Создание записей на тренировки...")
        
        try:
            # Получаем все тренировки, отсортированные по дате
            all_workouts = Workout.query.order_by(Workout.start_time).all()
            print(f"Получено {len(all_workouts)} тренировок для создания записей")
            
            # Распределяем тренировки между пользователями
            bookings = []
            
            # Отслеживаем количество записей для каждого пользователя
            user_bookings_count = {user.id: 0 for user in users}
            
            # Определяем целевое количество записей на пользователя
            # (N тренировок * среднее число пользователей на тренировку) / M пользователей
            target_bookings_per_user = (len(all_workouts) * 10) // len(users)
            
            print(f"Целевое количество записей на пользователя: ~{target_bookings_per_user}")
            
            # Распределяем записи, начиная с самых ранних тренировок
            booking_count = 0
            for workout in all_workouts:
                # Отбираем пользователей, у которых меньше всего записей
                eligible_users = sorted(users, key=lambda u: user_bookings_count[u.id])
                
                # Берем первых N пользователей с наименьшим количеством записей
                num_to_book = random.randint(5, 15)
                users_to_book = eligible_users[:num_to_book]
                
                for user in users_to_book:
                    booking = Booking(
                        user_id=user.id,
                        workout_id=workout.id,
                        booked_at=datetime.now()
                    )
                    bookings.append(booking)
                    user_bookings_count[user.id] += 1
                    booking_count += 1
                
                if booking_count % 100 == 0:
                    print(f"Создано {booking_count} записей...")
            
            # Добавляем записи в базу данных
            print(f"Сохранение {len(bookings)} записей в базу данных...")
            db.session.add_all(bookings)
            db.session.commit()
            
            # Выводим статистику по записям
            print(f"Создано {len(bookings)} записей на тренировки")
            
            min_bookings = min(user_bookings_count.values())
            max_bookings = max(user_bookings_count.values())
            avg_bookings = sum(user_bookings_count.values()) / len(user_bookings_count)
            
            print(f"Статистика записей на пользователя:")
            print(f"  Минимум: {min_bookings}")
            print(f"  Максимум: {max_bookings}")
            print(f"  Среднее: {avg_bookings:.1f}")
            
            print("Детальная статистика по пользователям:")
            for i, user in enumerate(users):
                print(f"  Пользователь {user.email}: {user_bookings_count[user.id]} записей")
        
        except Exception as e:
            print(f"ОШИБКА при создании записей: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # Записываем учетные данные пользователей в файл
        with open('user_credentials.txt', 'w', encoding='utf-8') as f:
            f.write("Учетные данные сгенерированных пользователей\n")
            f.write("========================================\n\n")
            
            for cred in user_credentials:
                f.write(f"Имя: {cred['name']}\n")
                f.write(f"Email: {cred['email']}\n")
                f.write(f"Пароль: {cred['password']}\n")
                f.write("----------------------------------------\n")
        
        print("Учетные данные пользователей сохранены в файл user_credentials.txt")
        
        return True

if __name__ == "__main__":
    print("Начало генерации данных...")
    success = generate_data()
    
    if success:
        print("Генерация данных успешно завершена!")
    else:
        print("Ошибка при генерации данных.")
        sys.exit(1) 