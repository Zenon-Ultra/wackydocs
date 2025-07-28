from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # Import db from extensions.py

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pdf_requests = db.relationship('PDFRequest', backref='user', lazy=True)
    vocabulary_words = db.relationship('VocabularyWord', backref='user', lazy=True)
    quiz_scores = db.relationship('QuizScore', backref='user', lazy=True)

    def __init__(self, username=None, email=None, password_hash=None, is_admin=False):
        if username:
            self.username = username
        if email:
            self.email = email
        if password_hash:
            self.password_hash = password_hash
        self.is_admin = is_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PDFRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    def __init__(self, user_id=None, subject=None, topic=None, description=None, status='pending'):
        if user_id:
            self.user_id = user_id
        if subject:
            self.subject = subject
        if topic:
            self.topic = topic
        if description:
            self.description = description
        self.status = status

    @staticmethod
    def can_user_request_today(user_id):
        """사용자가 오늘 요청할 수 있는지 확인"""
        from datetime import date
        today = date.today()
        today_requests = PDFRequest.query.filter(
            PDFRequest.user_id == user_id,
            db.func.date(PDFRequest.requested_at) == today
        ).count()
        return today_requests == 0

    @staticmethod
    def get_user_today_request_count(user_id):
        """사용자의 오늘 요청 수 반환"""
        from datetime import date
        today = date.today()
        return PDFRequest.query.filter(
            PDFRequest.user_id == user_id,
            db.func.date(PDFRequest.requested_at) == today
        ).count()

class PDFResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # suneung or naeshin
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    download_count = db.Column(db.Integer, default=0)

    def __init__(self, title=None, subject=None, category=None, filename=None, original_filename=None, uploaded_by=None, file_size=None):
        if title:
            self.title = title
        if subject:
            self.subject = subject
        if category:
            self.category = category
        if filename:
            self.filename = filename
        if original_filename:
            self.original_filename = original_filename
        if uploaded_by:
            self.uploaded_by = uploaded_by
        if file_size:
            self.file_size = file_size

class KoreanVocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 호칭, 기타 등
    difficulty = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word=None, meaning=None, category=None, difficulty='medium'):
        if word:
            self.word = word
        if meaning:
            self.meaning = meaning
        if category:
            self.category = category
        self.difficulty = difficulty

    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'meaning': self.meaning,
            'category': self.category,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VocabularyWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    korean_meaning = db.Column(db.Text, nullable=True)  # Add Korean meaning field
    language = db.Column(db.String(10), nullable=False)  # 'en' or 'ko'
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    mastery_level = db.Column(db.Integer, default=0)  # 0-5 scale

    def __init__(self, user_id=None, word=None, meaning=None, korean_meaning=None, language=None, mastery_level=0):
        if user_id:
            self.user_id = user_id
        if word:
            self.word = word
        if meaning:
            self.meaning = meaning
        self.korean_meaning = korean_meaning
        if language:
            self.language = language
        self.mastery_level = mastery_level

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'word': self.word,
            'meaning': self.meaning,
            'korean_meaning': self.korean_meaning,
            'language': self.language,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'mastery_level': self.mastery_level
        }

class QuizScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_type = db.Column(db.String(50), nullable=False)  # korean_vocab, english_vocab
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    quiz_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id=None, quiz_type=None, score=None, total_questions=None):
        if user_id:
            self.user_id = user_id
        if quiz_type:
            self.quiz_type = quiz_type
        if score:
            self.score = score
        if total_questions:
            self.total_questions = total_questions

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), default='all')  # 'all', 'members', 'non_members'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    creator = db.relationship('User', backref=db.backref('announcements', lazy=True))

    def __init__(self, title=None, content=None, visibility='all', priority='normal', created_by=None, expires_at=None, is_active=True):
        if title:
            self.title = title
        if content:
            self.content = content
        self.visibility = visibility
        self.priority = priority
        if created_by:
            self.created_by = created_by
        if expires_at:
            self.expires_at = expires_at
        self.is_active = is_active

    def is_visible_to_user(self, user):
        """Check if announcement is visible to a specific user"""
        if not self.is_active:
            return False

        if self.expires_at and self.expires_at < datetime.now():
            return False

        if self.visibility == 'all':
            return True
        elif self.visibility == 'members' and user and user.is_authenticated:
            return True
        elif self.visibility == 'non_members' and (not user or not user.is_authenticated):
            return True

        return False

class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    focus_minutes = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('focus_sessions', lazy=True))

    def __init__(self, user_id=None, session_date=None, focus_minutes=None, completed=True):
        if user_id:
            self.user_id = user_id
        if session_date:
            self.session_date = session_date
        if focus_minutes:
            self.focus_minutes = focus_minutes
        self.completed = completed

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'focus_minutes': self.focus_minutes,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CustomerSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # 'open', 'answered', 'closed'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True))

    def __init__(self, user_id=None, subject=None, message=None, priority='normal'):
        if user_id:
            self.user_id = user_id
        if subject:
            self.subject = subject
        if message:
            self.message = message
        self.priority = priority

class SupportReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('customer_support.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship('CustomerSupport', backref=db.backref('replies', lazy=True, order_by='SupportReply.created_at'))
    user = db.relationship('User', backref=db.backref('support_replies', lazy=True))

    def __init__(self, ticket_id=None, user_id=None, message=None, is_admin_reply=False):
        if ticket_id:
            self.ticket_id = ticket_id
        if user_id:
            self.user_id = user_id
        if message:
            self.message = message
        self.is_admin_reply = is_admin_reply