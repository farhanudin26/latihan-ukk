from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # HANYA deklarasi, tanpa init_app

# Tidak ada import model di sini (hindari circular import)
