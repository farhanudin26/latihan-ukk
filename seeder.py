from flask_bcrypt import Bcrypt
from app import app
from models.models import db, User

bcrypt = Bcrypt(app)

with app.app_context():
    # Cek apakah sudah ada user admin
    admin = User.query.filter_by(name='Admin').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(name='Admin', password=hashed_password, role='admin')
        db.session.add(admin_user)

    # Cek apakah sudah ada user employee
    employee = User.query.filter_by(name='Employee').first()
    if not employee:
        hashed_password = bcrypt.generate_password_hash('employee123').decode('utf-8')
        employee_user = User(name='Employee', password=hashed_password, role='employee')
        db.session.add(employee_user)

    db.session.commit()
    print("Seeder berhasil dijalankan!")
