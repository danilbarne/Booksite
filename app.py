from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from extensions import db, bcrypt, login_manager
from models import User, Message
from comment_models import Comment
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail 
import datetime
import random  # Добавлено для генерации кодов

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)


with app.app_context():
    db.create_all()

login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'
login_manager.login_message_category = 'info'

def send_email(to_email, subject, body):
    message = Mail(
        from_email=app.config["MAIL_DEFAULT_SENDER"],
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )

    try:
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])
        response = sg.send(message)

        print("EMAIL SENT")
        print(response.status_code)

    except Exception as e:
        print("SENDGRID ERROR:")
        print(str(e))
        raise

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html", title="Главная")

@app.route("/ad", methods=["GET", "POST"])
def ad():
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Чтобы оставить комментарий, нужно войти или зарегистрироваться.", "warning")
            return redirect(url_for('login'))
        comment_content = request.form.get("comment")
        if comment_content and len(comment_content.strip()) > 0:
            new_comment = Comment(content=comment_content, user_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
            flash("Комментарий успешно добавлен!", "success")
        else:
            flash("Комментарий не может быть пустым.", "danger")
        return redirect(url_for('ad'))
    comments = Comment.query.order_by(Comment.date_posted.desc()).all()
    return render_template("ad.html", title="Раздел АД", comments=comments)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Проверяем email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Пользователь с такой почтой уже существует!", "danger")
            return redirect(url_for("register"))

        # Проверяем username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Пользователь с таким именем уже существует!", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        verification_code = str(random.randint(100000, 999999))
        code_expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            verified=False,
            verification_code=verification_code,
            code_expires=code_expires
        )

        db.session.add(user)
        db.session.commit()

        
        print("MAIL_DEFAULT_SENDER:", app.config["MAIL_DEFAULT_SENDER"])

        send_email(
    email,
    "Код подтверждения BookSite",
    f"""Ваш код для регистрации: {verification_code}

Код действителен 10 минут."""
)

        try:
            print("Письмо отправлено успешно")
        except Exception as e:
            print("SMTP ERROR:", repr(e))
            raise

        flash(f"На почту {email} отправлен код. Введите его.", "success")
        return redirect(url_for("verify", email=email))

    return render_template("register.html", title="Регистрация")

@app.route("/verify/<email>", methods=["GET", "POST"])
def verify(email):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Пользователь не найден.", "danger")
        return redirect(url_for('register'))
    if user.verified:
        flash("Аккаунт уже подтверждён.", "success")
        return redirect(url_for('login'))
    if request.method == "POST":
        code = request.form.get("code")
        if code == user.verification_code and datetime.datetime.utcnow() < user.code_expires:
            user.verified = True
            user.verification_code = None
            user.code_expires = None
            db.session.commit()
            flash("Аккаунт подтверждён! Войдите.", "success")
            return redirect(url_for('login'))
        else:
            flash("Неверный код или срок истёк.", "danger")
    return render_template("verify.html", email=email)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.verified and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash("Вы успешно вошли!", "success")
            return redirect(next_page) if next_page else redirect(url_for('home'))
        elif user and not user.verified:
            flash("Аккаунт не подтверждён. Проверьте почту.", "warning")
        else:
            flash("Неверная почта или пароль.", "danger")
    return render_template("login.html", title="Вход")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            verification_code = str(random.randint(100000, 999999))
            code_expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

            user.verification_code = verification_code
            user.code_expires = code_expires
            db.session.commit()

            send_email(
                email,
                "Код для сброса пароля BookSite",
                f"""Ваш код для сброса пароля: {verification_code}

Код действителен 10 минут."""
            )

            print("Письмо отправлено успешно")

            flash(f"Код отправлен на почту {email}.", "success")
            return redirect(url_for("reset_verify", email=email))

        else:
            flash("Пользователь с такой почтой не найден.", "danger")

    return render_template("reset_request.html", title="Сброс пароля")

@app.route("/reset-verify/<email>", methods=["GET", "POST"])
def reset_verify(email):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.query.filter_by(email=email).first()
    if request.method == "POST":
        code = request.form.get("code")
        new_password = request.form.get("new_password")
        new_password_confirm = request.form.get("new_password_confirm")
        if new_password != new_password_confirm:
            flash("Пароли не совпадают.", "danger")
            return render_template("reset_verify.html", email=email)
        if code == user.verification_code and datetime.datetime.utcnow() < user.code_expires:
            hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
            user.password = hashed_password
            user.verification_code = None
            user.code_expires = None
            db.session.commit()
            flash("Пароль успешно изменён! Войдите.", "success")
            return redirect(url_for('login'))
        else:
            flash("Неверный код или срок истёк.", "danger")
    return render_template("reset_verify.html", email=email)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for('home'))

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        if current_user.is_authenticated:
            content = request.form.get("message")
            if content and len(content.strip()) > 0:
                new_msg = Message(content=content, user_id=current_user.id)
                db.session.add(new_msg)
                db.session.commit()
                flash("Сообщение отправлено!", "success")
                return redirect(url_for('chat'))
    if request.args.get('clear') == 'true' and current_user.is_authenticated and current_user.username == 'ADMIN':
        db.session.query(Message).delete()
        db.session.commit()
        flash("Чат полностью очищен.", "success")
        return redirect(url_for('chat'))
    messages = Message.query.order_by(Message.date_posted.asc()).all()
    return render_template("chat.html", title="Групповой чат", messages=messages)

@app.route("/delete_message/<int:msg_id>")
def delete_message(msg_id):
    if not current_user.is_authenticated or current_user.username != 'ADMIN':
        flash("Только администратор может удалять сообщения.", "danger")
        return redirect(url_for('chat'))
    msg = Message.query.get(msg_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        flash("Сообщение удалено.", "success")
    return redirect(url_for('chat'))

if __name__ == "__main__":
    app.run(debug=False)