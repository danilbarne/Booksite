import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- ДОБАВЛЕН НОВЫЙ БЛОК ---
# Создаем папку 'database', если её нет (это важно для Render)
db_dir = os.path.join(BASE_DIR, "database")
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

db_path = os.path.join(db_dir, "site.db")
# ---------------------------

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    # ИЗМЕНЕНА СТРОКА: теперь используем динамический путь, созданный выше
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")