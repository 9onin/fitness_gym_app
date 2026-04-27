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
        'manager_notes': 'ALTER TABLE users ADD COLUMN manager_notes TEXT',
    }

    for column_name, statement in required_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(statement))

    db.session.execute(
        text("UPDATE users SET client_status = 'new' WHERE client_status IS NULL OR client_status = ''")
    )
    db.session.commit()


def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_user_columns()
