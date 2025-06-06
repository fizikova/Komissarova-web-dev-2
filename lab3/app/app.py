from flask import (
    Flask, render_template, session,
    request, redirect, url_for, flash
)
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    current_user, login_required
)

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = (
    'Необходима регистрация! :<'
)
login_manager.login_message_category = 'warning'

# Храним пользователей в словаре, но возвращаем список (как раньше)
_USERS = {
    '1': {'login': 'user', 'password': 'qwerty'},
}

def get_users():
    return [
        {'id': uid, 'login': data['login'], 'password': data['password']}
        for uid, data in _USERS.items()
    ]

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
    
    @property
    def login(self):
        return _USERS[self.id]['login']

@login_manager.user_loader
def load_user(user_id):
    if user_id in _USERS:
        return User(user_id)
    return None

@app.context_processor
def inject_nav_links():
    links = [
        {'name': 'Главная', 'endpoint': 'index'},
        {'name': 'Счётчик', 'endpoint': 'counter'},
    ]
    if current_user.is_authenticated:
        links.append({'name': 'Секрет','endpoint': 'secret'})
        links.append({'name': 'Выйти','endpoint': 'logout'})
    else:
        links.append({'name': 'Войти','endpoint': 'login'})
    return dict(nav_links=links)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    if current_user.is_authenticated:
        user_id = current_user.id
        # Забираем словарь или создаём новый
        counters = session.get('counters', {})
        counters[user_id] = counters.get(user_id, 0) + 1
        # Критично: кладём обновлённый словарь обратно в session
        session['counters'] = counters
        counter_value = counters[user_id]
    else:
        # Для анонима храним простой integer
        session['counter'] = session.get('counter', 0) + 1
        counter_value = session['counter']

    return render_template('counter.html', counter=counter_value)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # сначала пытаемся взять next из args, потом из form, или ставим /
    next_page = request.args.get('next') or request.form.get('next') or url_for('index')
    if request.method == 'POST':
        login_input = request.form.get('username')
        password_input = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        if login_input and password_input:
            for u in get_users():
                if u['login'] == login_input and u['password'] == password_input:
                    user = User(u['id'])
                    login_user(user, remember=remember_me)
                    flash('Вы успешно аутентифицированы', 'success')
                    return redirect(next_page)
            # не нашли совпадений
            return render_template(
                'auth.html',
                error='Пользователь не найден, проверьте данные!',
                next=next_page
            )
    return render_template('auth.html', next=next_page)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')
