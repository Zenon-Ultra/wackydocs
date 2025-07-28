import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
from forms import RegistrationForm, LoginForm, PDFRequestForm, AnnouncementForm
from models import User, PDFRequest, PDFResource, KoreanVocabulary, VocabularyWord, QuizScore, Notification, Announcement
from sqlalchemy import func
from flask_migrate import Migrate
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db  # Import db from extensions.py
from flask_wtf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# CSRF 보호 활성화
csrf = CSRFProtect(app)

# Configure the database
db_path = os.path.join(os.path.dirname(__file__), 'studyhub.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = '로그인이 필요합니다.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    logging.error("Unhandled Exception: %s\n%s", e, traceback.format_exc())
    return render_template("error.html", message="서버 오류가 발생했습니다. 관리자에게 문의하세요."), 500

@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except:
        return "", 204  # No content


with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    logging.info("Database tables created")
    logging.info("Database tables created")
