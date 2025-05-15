import os
import sqlite3
import random
from datetime import datetime, timedelta

def populate_database():
    """
    Reset and populate the database with workout and booking data.
    """
    try:
        # Database path
        db_path = 'instance/fitness_gym.db'
        
        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {os.path.abspath(db_path)}")
            return False
            
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Connected to database at {os.path.abspath(db_path)}")
        
        # Clear existing data
        print("Deleting existing bookings and workouts...")
        cursor.execute("DELETE FROM bookings")
        cursor.execute("DELETE FROM workouts")
        conn.commit()
        
        # Add workout types if needed
        cursor.execute("SELECT COUNT(*) FROM workout_types")
        workout_type_count = cursor.fetchone()[0]
        
        if workout_type_count == 0:
            print("Adding workout types...")
            workout_types = [
                ("Йога", "Улучшает гибкость и баланс"),
                ("Пилатес", "Укрепляет мышцы кора"),
                ("Кроссфит", "Высокоинтенсивные тренировки"),
                ("Зумба", "Танцевальная фитнес-программа"),
                ("Аэробика", "Кардио тренировка"),
                ("Силовая тренировка", "Развитие мышечной силы"),
                ("Функциональный тренинг", "Улучшение общей физической подготовки"),
                ("Стретчинг", "Развитие гибкости"),
                ("Бокс", "Обучение техникам бокса"),
                ("Спиннинг", "Велотренировки"),
                ("Плавание", "Тренировки в бассейне"),
                ("Бег", "Беговые тренировки"),
                ("ТРХ", "Тренировки с подвесными петлями"),
                ("Тай-чи", "Древнекитайская практика"),
                ("HIIT", "Высокоинтенсивный интервальный тренинг"),
                ("Степ-аэробика", "Аэробные тренировки со степ-платформой"),
                ("Каланетика", "Статические упражнения"),
                ("Аквааэробика", "Аэробика в воде"),
                ("Табата", "Интервальные тренировки"),
                ("Кардио", "Кардио тренировки различной интенсивности")
            ]
            cursor.executemany("INSERT INTO workout_types (name, description) VALUES (?, ?)", workout_types)
            conn.commit()
            print(f"Added {len(workout_types)} workout types")
        
        # Add trainers if needed
        cursor.execute("SELECT COUNT(*) FROM trainers")
        trainer_count = cursor.fetchone()[0]
        
        if trainer_count < 3:
            print("Adding trainers...")
            trainers_to_add = 3 - trainer_count
            trainers = [
                ("Иван", "Петров", 5, "Силовые тренировки", "Опытный тренер по силовым тренировкам"),
                ("Анна", "Сидорова", 7, "Йога и пилатес", "Сертифицированный инструктор по йоге"),
                ("Алексей", "Иванов", 3, "Кардио и HIIT", "Специалист по высокоинтенсивным тренировкам")
            ]
            
            for i in range(trainers_to_add):
                cursor.execute(
                    "INSERT INTO trainers (first_name, last_name, experience_years, specialization, profile) VALUES (?, ?, ?, ?, ?)",
                    trainers[i]
                )
            conn.commit()
            print(f"Added {trainers_to_add} trainers")
        
        # Check for users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("Error: No users found in database. Please create at least one user first.")
            conn.close()
            return False
        
        # Get workout types, trainers, and users
        cursor.execute("SELECT id, name FROM workout_types")
        workout_types = cursor.fetchall()
        
        cursor.execute("SELECT id, first_name, last_name FROM trainers LIMIT 3")
        trainers = cursor.fetchall()
        
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        
        print(f"Found {len(workout_types)} workout types, {len(trainers)} trainers, and {len(users)} users")
        
        # Create workouts
        total_workouts = 300
        start_date = datetime(2025, 5, 1)  # 01.05.2025
        workout_duration = 1.5  # 1.5 hours
        workout_times = [9, 11, 13, 15, 17]  # 9:00, 11:00, 13:00, 15:00, 17:00
        
        print(f"Creating {total_workouts} workouts...")
        
        workouts = []
        current_date = start_date
        workout_count = 0
        
        # Create workouts evenly distributed among trainers and workout types
        while workout_count < total_workouts:
            for trainer in trainers:
                trainer_id = trainer[0]
                for hour in workout_times:
                    if workout_count >= total_workouts:
                        break
                    
                    # Get workout type (cycling through all types evenly)
                    workout_type = workout_types[workout_count % len(workout_types)]
                    workout_type_id = workout_type[0]
                    workout_type_name = workout_type[1]
                    
                    # Calculate start and end times
                    start_time = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        hour
                    )
                    end_time = start_time + timedelta(hours=workout_duration)
                    
                    # Format times for SQLite
                    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Create workout
                    cursor.execute(
                        """
                        INSERT INTO workouts 
                        (trainer_id, workout_type_id, start_time, end_time, max_participants, description) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            trainer_id,
                            workout_type_id,
                            start_time_str,
                            end_time_str,
                            15,
                            f"{workout_type_name} с тренером {trainer[1]} {trainer[2]}"
                        )
                    )
                    
                    # Get the workout ID
                    cursor.execute("SELECT last_insert_rowid()")
                    workout_id = cursor.fetchone()[0]
                    workouts.append((workout_id, start_time))
                    
                    workout_count += 1
                    
                    # Commit periodically
                    if workout_count % 50 == 0:
                        conn.commit()
                        print(f"Created {workout_count} workouts so far...")
                
                if workout_count >= total_workouts:
                    break
            
            current_date += timedelta(days=1)
        
        # Commit all workouts
        conn.commit()
        print(f"Successfully created {len(workouts)} workouts")
        
        # Create bookings with 80% attendance
        print("Creating bookings with 80% attendance rate...")
        
        # Determine which workouts will be marked as not attended (20%)
        total_unattended = int(len(workouts) * 0.2)
        unattended_indices = random.sample(range(len(workouts)), total_unattended)
        unattended_workouts = set(workouts[i][0] for i in unattended_indices)
        
        # Create bookings
        bookings_created = 0
        
        for i, (workout_id, start_time) in enumerate(workouts):
            # Distribute bookings evenly among users
            user_id = users[i % len(users)][0]
            
            # Determine if attended
            attended = 1 if workout_id not in unattended_workouts else 0
            
            # Booking time (1-7 days before the workout)
            booked_at = start_time - timedelta(days=random.randint(1, 7))
            booked_at_str = booked_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create booking
            cursor.execute(
                """
                INSERT INTO bookings 
                (user_id, workout_id, booked_at, attended) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, workout_id, booked_at_str, attended)
            )
            
            bookings_created += 1
            
            # Commit periodically
            if bookings_created % 50 == 0:
                conn.commit()
                print(f"Created {bookings_created} bookings so far...")
        
        # Final commit
        conn.commit()
        
        attended_count = bookings_created - total_unattended
        print(f"Successfully created {bookings_created} bookings ({attended_count} attended, {total_unattended} unattended)")
        
        # Close connection
        conn.close()
        print("Database population completed successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    populate_database() 