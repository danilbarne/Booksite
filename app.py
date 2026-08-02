from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, bcrypt, login_manager, mail
from models import User
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Настройка – куда переадресовывать неавторизованных пользователей
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html", title="Главная")

@app.route("/ad")
def ad():
    return render_template("ad.html", title="АД")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Проверка на существующего пользователя
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Пользователь с такой почтой уже существует!", "danger")
            return redirect(url_for('register'))
        
        # Хешируем пароль
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash("Регистрация успешна! Теперь войдите.", "success")
        return redirect(url_for('login'))
    
    return render_template("register.html", title="Регистрация")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash("Вы успешно вошли!", "success")
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Неверная почта или пароль.", "danger")
    
    return render_template("login.html", title="Вход")

# Генератор токенов для сброса пароля
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

# Проверка токена
def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return email

@app.route("/reset-password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Генерируем токен
            token = generate_reset_token(email)
            # Ссылка для сброса (локально или на твоём домене)
            reset_url = url_for('reset_token', token=token, _external=True)
            
            # Отправляем письмо
            msg = Message(
                subject="Сброс пароля на BookSite",
                recipients=[email]
            )
            msg.body = f"""
Чтобы сбросить пароль, перейди по ссылке:

{reset_url}

Если ты не запрашивал сброс пароля, просто проигнорируй это письмо.

Ссылка действительна 1 час.

BookSite
"""
            mail.send(msg)
            flash("Письмо с инструкцией отправлено на вашу почту.", "success")
            return redirect(url_for('login'))
        else:
            flash("Пользователь с такой почтой не найден.", "danger")
    
    return render_template("reset_request.html", title="Сброс пароля")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    email = verify_reset_token(token)
    if not email:
        flash("Ссылка недействительна или истекла.", "danger")
        return redirect(url_for('reset_request'))
    
    if request.method == "POST":
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        
        if password != password_confirm:
            flash("Пароли не совпадают.", "danger")
            return render_template("reset_token.html", title="Новый пароль")
        
        user = User.query.filter_by(email=email).first()
        if user:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user.password = hashed_password
            db.session.commit()
            flash("Пароль успешно изменён! Теперь войдите.", "success")
            return redirect(url_for('login'))
    
    return render_template("reset_token.html", title="Новый пароль")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for('home'))

@app.route("/send-test")
def send_test():
    msg = Message(
        subject="Проверка BookSite",
        recipients=["danabaranec71@gmail.com"]  # замени на свою почту
    )
    msg.body = """
Поздравляем!

Если ты получил это письмо, значит отправка почты работает.

BookSite
"""
    mail.send(msg)
    return "Письмо отправлено!"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)