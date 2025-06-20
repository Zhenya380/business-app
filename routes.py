from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Task, db

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks, current_user=current_user)


@main.route('/add', methods=['POST'])
@login_required
def add_task():
    if current_user.role != 'керівник':
        flash('Додавати завдання може лише керівник', 'error')
        return redirect(url_for('main.index'))

    title = request.form.get('title')
    subtitle = request.form.get('subtitle')

    if not title:
        flash('Заголовок обов’язковий', 'error')
        return redirect(url_for('main.index'))

    new_task = Task(title=title, subtitle=subtitle)
    db.session.add(new_task)
    db.session.commit()

    flash('Завдання додано', 'success')
    return redirect(url_for('main.index'))


@main.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    if current_user.role != 'керівник':
        flash('Видаляти завдання може лише керівник', 'error')
        return redirect(url_for('main.index'))

    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('Завдання видалено', 'success')
    return redirect(url_for('main.index'))


@main.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_task(id):
    if current_user.role != 'керівник':
        flash('Редагувати завдання може лише керівник', 'error')
        return redirect(url_for('main.index'))

    task = Task.query.get_or_404(id)
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')

    if not title:
        flash('Заголовок обов’язковий', 'error')
        return redirect(url_for('main.index'))

    task.title = title
    task.subtitle = subtitle
    db.session.commit()
    flash('Завдання оновлено', 'success')
    return redirect(url_for('main.index'))


@main.route('/status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    task = Task.query.get_or_404(id)

    # Тільки працівник або керівник можуть змінювати статус
    if current_user.role not in ['керівник', 'працівник']:
        flash('Недостатньо прав для зміни статусу', 'error')
        return redirect(url_for('main.index'))

    # Працівник може лише змінювати статус (без редагування тексту)
    if task.status == 'в роботі':
        task.status = 'виконано'
    else:
        task.status = 'в роботі'

    db.session.commit()
    flash('Статус змінено', 'success')
    return redirect(url_for('main.index'))
