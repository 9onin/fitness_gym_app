import os
import sqlite3
import sys

def find_database():
    """Find the database file in common locations."""
    possible_db_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fitness_gym.db'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'fitness_gym.db'),
        'instance/fitness_gym.db',
        './instance/fitness_gym.db',
        '../instance/fitness_gym.db'
    ]
    
    for path in possible_db_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    print("Error: Could not find the database file.")
    print("Searched in:")
    for path in possible_db_paths:
        print(f"  - {os.path.abspath(path)}")
    return None

def delete_users(db_path, emails):
    """Delete users and their bookings using direct SQLite commands."""
    print(f"Opening database at: {db_path}")
    
    # Connect to the database with a timeout
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    
    for email in emails:
        try:
            print(f"\nProcessing user with email: {email}")
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Find the user
            cursor = conn.execute("SELECT id, email, first_name, last_name FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User with email {email} not found in the database.")
                conn.execute("ROLLBACK")
                continue
            
            user_id = user['id']
            print(f"Found user: {user['email']} (ID: {user_id}, Name: {user['first_name']} {user['last_name']})")
            
            # Count and delete bookings
            cursor = conn.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ?", (user_id,))
            booking_count = cursor.fetchone()[0]
            print(f"Found {booking_count} bookings for this user.")
            
            if booking_count > 0:
                print(f"Deleting bookings for user {email}...")
                conn.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
                print(f"Deleted {booking_count} bookings.")
            
            # Delete the user
            print(f"Deleting user {email}...")
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            # Commit the transaction
            conn.execute("COMMIT")
            print(f"User {email} deleted successfully.")
            
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            print("Rolling back transaction...")
            conn.execute("ROLLBACK")
    
    # Close connection
    conn.close()
    print("\nUser deletion process completed.")

if __name__ == "__main__":
    # Emails to delete
    emails_to_delete = ["ctrlaltdelite908@gmail.com", "wasd908315@gmail.com"]
    
    # Find the database
    db_path = find_database()
    if not db_path:
        sys.exit(1)
    
    # Confirm before proceeding
    print(f"This will delete the following users and all their associated data:")
    for email in emails_to_delete:
        print(f"  - {email}")
    
    confirm = input("Are you sure you want to continue? (y/n): ")
    if confirm.lower() in ['y', 'yes']:
        delete_users(db_path, emails_to_delete)
    else:
        print("Operation cancelled.") 