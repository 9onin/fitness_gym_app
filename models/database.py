from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text


db = SQLAlchemy()


def ensure_user_columns():
    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns('users')}

    required_columns = {
        'phone': 'ALTER TABLE users ADD COLUMN phone VARCHAR(30)',
        'client_status': "ALTER TABLE users ADD COLUMN client_status VARCHAR(20) NOT NULL DEFAULT 'new'",
        'fitness_goal': 'ALTER TABLE users ADD COLUMN fitness_goal VARCHAR(255)',
        'fitness_plan_height_cm': 'ALTER TABLE users ADD COLUMN fitness_plan_height_cm FLOAT',
        'fitness_plan_weight_kg': 'ALTER TABLE users ADD COLUMN fitness_plan_weight_kg FLOAT',
        'fitness_plan_goal_key': 'ALTER TABLE users ADD COLUMN fitness_plan_goal_key VARCHAR(50)',
        'fitness_plan_updated_at': 'ALTER TABLE users ADD COLUMN fitness_plan_updated_at DATETIME',
        'manager_notes': 'ALTER TABLE users ADD COLUMN manager_notes TEXT',
    }

    for column_name, statement in required_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(statement))

    db.session.execute(
        text("UPDATE users SET client_status = 'new' WHERE client_status IS NULL OR client_status = ''")
    )
    db.session.commit()


def ensure_user_abonement_columns():
    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns('user_abonements')}

    required_columns = {
        'frozen_from': 'ALTER TABLE user_abonements ADD COLUMN frozen_from DATETIME',
        'frozen_until': 'ALTER TABLE user_abonements ADD COLUMN frozen_until DATETIME',
        'freeze_days_used': 'ALTER TABLE user_abonements ADD COLUMN freeze_days_used INTEGER DEFAULT 0',
        'extension_count': 'ALTER TABLE user_abonements ADD COLUMN extension_count INTEGER DEFAULT 0',
    }

    for column_name, statement in required_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(statement))

    db.session.execute(
        text('UPDATE user_abonements SET freeze_days_used = 0 WHERE freeze_days_used IS NULL')
    )
    db.session.execute(
        text('UPDATE user_abonements SET extension_count = 0 WHERE extension_count IS NULL')
    )
    db.session.commit()


def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_user_columns()
        ensure_user_abonement_columns()
