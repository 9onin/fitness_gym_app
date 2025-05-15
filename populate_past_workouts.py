import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sqlite3
import numpy as np

# Add the parent directory to the path so we can import our models
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import models directly
from models.models import User, Trainer, WorkoutType, Workout, Booking
from models.database import db

def populate_past_workouts():
    """
    Creates 300 workouts for the past period (before 01.05.2025) with uneven distribution
    among workout types, trainers, and users. Sets the no-show rate to 30%.
    """
    print("Connecting to database...")
    
    # Get the database URI - try different possible locations
    possible_db_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fitness_gym.db'),
        'instance/fitness_gym.db',
        './instance/fitness_gym.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Error: Could not find the database file.")
        print("Searched in:")
        for path in possible_db_paths:
            print(f"  - {os.path.abspath(path)}")
        return
    
    print(f"Using database at: {db_path}")
    DB_URI = f'sqlite:///{db_path}'
    
    # Create engine and session
    engine = create_engine(DB_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all workout types, trainers, and users
        workout_types = session.query(WorkoutType).all()
        trainers = session.query(Trainer).all()
        users = session.query(User).all()
        
        if not workout_types:
            print("Error: No workout types found in the database.")
            return
            
        if not trainers or len(trainers) < 3:
            print("Error: Need at least 3 trainers in the database.")
            return
            
        if not users:
            print("Error: No users found in the database.")
            return
            
        print(f"Found {len(workout_types)} workout types, {len(trainers)} trainers, and {len(users)} users.")
        
        # Define workout parameters
        total_workouts = 300
        end_date = datetime(2025, 4, 30)  # Just before 01.05.2025
        
        # Set duration for each workout (in hours)
        workout_duration = 1.5  # 1.5 hours per workout
        
        # Workouts per day (between 9:00 and 17:00, considering duration)
        workouts_per_day = 5  # e.g., 9:00, 11:00, 13:00, 15:00, 17:00
        
        # Calculate how many days we need to distribute workouts
        days_needed = total_workouts // workouts_per_day
        start_date = end_date - timedelta(days=days_needed)
        
        print(f"Creating {total_workouts} past workouts from {start_date.strftime('%d.%m.%Y')} to {end_date.strftime('%d.%m.%Y')}...")
        
        # Create popularity weights for workout types (uneven distribution)
        # Some workout types will be more popular than others
        workout_type_weights = np.random.dirichlet(np.ones(len(workout_types)) * 0.5) * 10
        # Convert to a list of weights that sums to 1
        workout_type_weights = [float(w) / sum(workout_type_weights) for w in workout_type_weights]
        
        # Create popularity weights for trainers (uneven distribution)
        # Some trainers will be more popular than others
        trainer_weights = np.random.dirichlet(np.ones(len(trainers)) * 0.5) * 10
        # Convert to a list of weights that sums to 1
        trainer_weights = [float(w) / sum(trainer_weights) for w in trainer_weights]
        
        # Create workouts
        workouts = []
        current_date = start_date
        workout_count = 0
        
        # Loop through days
        while current_date <= end_date and workout_count < total_workouts:
            # Determine how many workouts to schedule this day (random between 3-6)
            daily_workouts = random.randint(3, 6)
            
            # Schedule workouts for this day
            for _ in range(daily_workouts):
                if workout_count >= total_workouts:
                    break
                
                # Select a trainer using weighted random selection
                trainer = random.choices(trainers, weights=trainer_weights, k=1)[0]
                
                # Select a workout type using weighted random selection
                workout_type = random.choices(workout_types, weights=workout_type_weights, k=1)[0]
                
                # Generate a random hour between 9 and 17 (inclusive)
                hour = random.randint(9, 17)
                # Generate a random minute (0, 15, 30, 45)
                minute = random.choice([0, 15, 30, 45])
                
                # Calculate start and end times
                start_time = datetime(
                    current_date.year, 
                    current_date.month, 
                    current_date.day, 
                    hour,
                    minute
                )
                end_time = start_time + timedelta(hours=workout_duration)
                
                # Skip if the end time is after 18:00
                if end_time.hour >= 18 and end_time.minute > 0:
                    continue
                
                # Create workout
                workout = Workout(
                    trainer_id=trainer.id,
                    workout_type_id=workout_type.id,
                    start_time=start_time,
                    end_time=end_time,
                    max_participants=15,
                    description=f"{workout_type.name} с тренером {trainer.first_name} {trainer.last_name}"
                )
                
                workouts.append(workout)
                workout_count += 1
            
            current_date += timedelta(days=1)
        
        # Add all workouts to the database
        session.add_all(workouts)
        session.commit()
        
        print(f"Created {len(workouts)} past workouts.")
        
        # Create user popularity weights (uneven distribution)
        # Some users will book more workouts than others
        user_weights = np.random.dirichlet(np.ones(len(users)) * 0.3) * 10
        # Convert to a list of weights that sums to 1
        user_weights = [float(w) / sum(user_weights) for w in user_weights]
        
        # Create bookings with uneven distribution and 30% no-show rate
        print("Creating bookings with 70% attendance rate and uneven user distribution...")
        
        bookings = []
        
        # Calculate how many bookings should be marked as not attended (30%)
        total_unattended = int(len(workouts) * 0.3)
        unattended_workouts = random.sample(workouts, total_unattended)
        
        # For each workout, select a user based on the user weights
        for workout in workouts:
            # Select a user using weighted random selection
            user = random.choices(users, weights=user_weights, k=1)[0]
            
            # Determine if this workout is attended
            attended = workout not in unattended_workouts
            
            # Calculate a reasonable booking date (1-14 days before the workout)
            booking_window = min(14, (workout.start_time.date() - start_date.date()).days)
            days_before = random.randint(1, max(1, booking_window))
            booked_at = workout.start_time - timedelta(days=days_before)
            
            booking = Booking(
                user_id=user.id,
                workout_id=workout.id,
                booked_at=booked_at,
                attended=attended
            )
            
            bookings.append(booking)
        
        # Add all bookings to the database
        session.add_all(bookings)
        session.commit()
        
        # Print statistics about the bookings
        user_booking_counts = {}
        for booking in bookings:
            user_id = booking.user_id
            if user_id in user_booking_counts:
                user_booking_counts[user_id] += 1
            else:
                user_booking_counts[user_id] = 1
        
        # Find min, max, and average bookings per user
        if user_booking_counts:
            min_bookings = min(user_booking_counts.values())
            max_bookings = max(user_booking_counts.values())
            avg_bookings = sum(user_booking_counts.values()) / len(user_booking_counts)
            num_users_with_bookings = len(user_booking_counts)
            
            print(f"Booking distribution among {num_users_with_bookings} users:")
            print(f"  Min: {min_bookings} bookings")
            print(f"  Max: {max_bookings} bookings")
            print(f"  Avg: {avg_bookings:.1f} bookings")
        
        print(f"Created {len(bookings)} bookings ({len(bookings) - total_unattended} attended, {total_unattended} unattended).")
        print("Past workouts population completed successfully.")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    populate_past_workouts() 