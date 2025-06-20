from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Наприклад: 'Керівник' або 'Працівник'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='нове')  # статус: 'нове', 'в процесі', 'виконано'
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # додано поле

    # Відношення (не обов’язково, але корисно)
    assignee = db.relationship('User', backref='tasks', lazy=True)
