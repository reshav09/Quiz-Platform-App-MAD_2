from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .serializer import SerializerMixin
import hashlib

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        admin = Admin.query.first()
        if not admin:
            admin = Admin(username="admin", password="admin123")
            db.session.add(admin)
            db.session.commit()

class Admin(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    def verify_password(self, password):
        """Verify the password against stored hash"""
        return self.password == password  # For admin, we're using plaintext as in original code
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate admin user"""
        user = cls.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            return user
        return None

class User(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # Added email field
    qualification = db.Column(db.String(120))
    dob = db.Column(db.Date)
    report_format = db.Column(db.String(10), default='html')
    is_active = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    scores = db.relationship('Score', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def verify_password(self, password):
        """Verify the password against stored hash"""
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        return self.password == hashed_input
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate user"""
        user = cls.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            return user
        return None
    
    def to_dict(self, exclude=None, include=None):
        """Override to_dict to exclude sensitive information"""
        exclude = exclude or ['password']
        return super().to_dict(exclude=exclude, include=include)

class Subject(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade="all, delete-orphan")

class Quiz(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(5), nullable=False)
    remarks = db.Column(db.Text)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade="all, delete-orphan")

class Question(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Score(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    total_scored = db.Column(db.Float, nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self, exclude=None, include=None):
        """Override to_dict to include related quiz and user information"""
        exclude = exclude or []
        include = include or {}
        
        result = super().to_dict(exclude=exclude, include=include)
        
        # Add user name if user is loaded
        if hasattr(self, 'user') and self.user is not None:
            result['user_name'] = self.user.full_name
            
        # Add quiz info if quiz is loaded
        if hasattr(self, 'quiz') and self.quiz is not None:
            result['quiz_info'] = {
                'date_of_quiz': self.quiz.date_of_quiz.isoformat() if hasattr(self.quiz.date_of_quiz, 'isoformat') else str(self.quiz.date_of_quiz),
                'time_duration': self.quiz.time_duration,
                'remarks': self.quiz.remarks
            }
            
            # Add chapter and subject info if loaded
            if hasattr(self.quiz, 'chapter') and self.quiz.chapter is not None:
                result['chapter_name'] = self.quiz.chapter.name
                
                if hasattr(self.quiz.chapter, 'subject') and self.quiz.chapter.subject is not None:
                    result['subject_name'] = self.quiz.chapter.subject.name
                    
        return result