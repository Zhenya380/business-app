from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm  # Імпорт форми логіну
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length

app = Flask(__name__)
app.config['SECRET_KEY'] = 'твій_секретний_ключ_тут'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Керівник' або 'Працівник'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Модель завдання
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='нове')  # статус: нове, в процесі, виконано


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Форма реєстрації (можна імпортувати з forms.py, але тут для повноти)
class RegisterForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Підтвердження пароля',
                            validators=[DataRequired(), EqualTo('password', message='Паролі повинні співпадати')])
    role = SelectField('Роль', choices=[('Керівник', 'Керівник'), ('Працівник', 'Працівник')],
                       validators=[DataRequired()])
    submit = SubmitField('Зареєструватися')


@app.route('/')
@login_required
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Невірний логін або пароль')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data

        if User.query.filter_by(username=username).first():
            flash('Користувач з таким іменем вже існує')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Реєстрація пройшла успішно! Увійдіть у систему.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# Додати завдання (тільки Керівник)
@app.route('/add', methods=['POST'])
@login_required
def add_task():
    if current_user.role != 'Керівник':
        flash('Доступ заборонено')
        return redirect(url_for('index'))
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')
    new_task = Task(title=title, subtitle=subtitle)
    db.session.add(new_task)
    db.session.commit()
    flash('Завдання додано')
    return redirect(url_for('index'))


# Редагувати завдання (тільки Керівник)
@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    if current_user.role != 'Керівник':
        flash('Доступ заборонено')
        return redirect(url_for('index'))
    task = Task.query.get_or_404(task_id)
    task.title = request.form.get('title')
    task.subtitle = request.form.get('subtitle')
    db.session.commit()
    flash('Завдання оновлено')
    return redirect(url_for('index'))


# Видалити завдання (тільки Керівник)
@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'Керівник':
        flash('Доступ заборонено')
        return redirect(url_for('index'))
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Завдання видалено')
    return redirect(url_for('index'))


# Змінити статус (усі користувачі)
@app.route('/status/<int:task_id>', methods=['POST'])
@login_required
def change_status(task_id):
    task = Task.query.get_or_404(task_id)
    # Логіка циклу статусів: нове → в процесі → виконано → нове
    if task.status == 'нове':
        task.status = 'в процесі'
    elif task.status == 'в процесі':
        task.status = 'виконано'
    else:
        task.status = 'нове'
    db.session.commit()
    flash(f'Статус завдання "{task.title}" змінено на {task.status}')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # створює таблиці, якщо ще не створені
    app.run(debug=True)
