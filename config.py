import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

db_dir = os.path.join(BASE_DIR, "database")
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

db_path = os.path.join(db_dir, "site.db")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")