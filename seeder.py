# seed.py

from flask_bcrypt import Bcrypt
from app import app
from models.models import db, User

bcrypt = Bcrypt(app)

# Data yang akan di‑seed: (username, password_plain, role)
SEED_USERS = [
    ('Admin',    'admin123',    'admin'),
    ('Employee', 'employee123', 'employee'),
]

def seed_users():
    with app.app_context():
        for name, raw_pw, role in SEED_USERS:
            if not User.query.filter_by(name=name).first():
                hashed = bcrypt.generate_password_hash(raw_pw).decode('utf-8')
                db.session.add(User(name=name, password=hashed, role=role))
        db.session.commit()
        print("Seeder berhasil dijalankan!")

if __name__ == '__main__':
    seed_users()
