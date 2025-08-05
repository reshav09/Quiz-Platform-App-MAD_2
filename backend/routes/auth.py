from flask import Blueprint, request, session, jsonify
from models.database import User, Score, Quiz, Chapter, Subject
from models.database import db
import hashlib
from datetime import datetime, timedelta

# Access redis_client via Flask's g object
from flask import g

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    from models.database import Admin
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
        
    # Check for user login
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = User.query.filter_by(username=username, password=hashed_password).first()
    if user:
        session['user_id'] = user.id
        return jsonify({'success': True, 'message': 'Login successful'})
    
    # Check for admin login
    admin = Admin.query.filter_by(username=username, password=password).first()
    if admin:
        session['admin'] = True
        return jsonify({'success': True, 'message': 'Admin login successful'})
    
    # Invalid credentials
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    qualification = data.get('qualification')
    dob = data.get('dob')
    report_format = data.get('report_format', 'html')
    
    # Validate required fields
    if not username or not password or not full_name:
        return jsonify({'error': 'Username, password, and full name are required'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            username=username, 
            password=hashed_password, 
            full_name=full_name, 
            qualification=qualification, 
            dob=datetime.strptime(dob, '%Y-%m-%d') if dob else None,
            report_format=report_format
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin', None)
    return jsonify({'message': 'Logged out'})

@auth_bp.route('/user_dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please log in'}), 403
    user = User.query.get(user_id)
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quizzes = Quiz.query.all()
    scores = db.session.query(Score, Quiz, Chapter, Subject).join(Quiz, Score.quiz_id == Quiz.id).join(Chapter, Quiz.chapter_id == Chapter.id).join(Subject, Chapter.subject_id == Subject.id).filter(Score.user_id == user_id).all()
    summary_data = {
        'subjects': [s.name for s in subjects],
        'subjectAttempts': [len(Score.query.filter_by(user_id=user_id).join(Quiz).join(Chapter).filter(Chapter.subject_id == s.id).all()) for s in subjects],
        'dates': [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30, -1, -1)],
        'avg_scores': [Score.query.filter(Score.user_id == user_id, Score.time_stamp_of_attempt >= datetime.now() - timedelta(days=30-x)).with_entities(db.func.avg(Score.total_scored)).scalar() or 0 for x in range(30, -1, -1)],
        'attempts': [Score.query.filter(Score.user_id == user_id, Score.time_stamp_of_attempt >= datetime.now() - timedelta(days=30-x)).count() for x in range(30, -1, -1)]
    }
    return jsonify({
        'user_name': user.full_name,
        'subjects': [{'id': s.id, 'name': s.name} for s in subjects],
        'chapters': [{'id': c.id, 'name': c.name, 'subject_id': c.subject_id} for c in chapters],
        'quizzes': [{'id': q.id, 'chapter_id': q.chapter_id, 'date_of_quiz': q.date_of_quiz.strftime('%Y-%m-%d')} for q in quizzes],
        'scores': [{'quiz': {'id': s.Quiz.id}, 'subject': {'name': s.Subject.name}, 'chapter': {'name': s.Chapter.name}, 'score': {'total_scored': s.Score.total_scored, 'time_stamp_of_attempt': s.Score.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M:%S')}} for s in scores],
        'summary_data': summary_data,
        'report_format': user.report_format
    })

@auth_bp.route('/attempt_quiz/<int:quiz_id>')
def attempt_quiz(quiz_id):
    from models.database import Question
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please log in'}), 403
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return jsonify({'questions': [{'id': q.id, 'question_statement': q.question_statement, 'option1': q.option1, 'option2': q.option2, 'option3': q.option3, 'option4': q.option4} for q in questions]})

@auth_bp.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    from models.database import Question
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please log in'}), 403
    data = request.get_json()
    answers = data.get('answers', {})
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    correct = sum(1 for q in questions if str(q.correct_option) == answers.get(str(q.id)))
    total_scored = (correct / len(questions)) * 100 if questions else 0
    score = Score(user_id=user_id, quiz_id=quiz_id, total_scored=total_scored)
    db.session.add(score)
    db.session.commit()
    return jsonify({'message': 'Quiz submitted', 'score': total_scored})

@auth_bp.route('/view_answers/<int:quiz_id>')
def view_answers(quiz_id):
    from models.database import Question, Quiz, Score
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please log in to view answers'}), 403
    score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if not score:
        return jsonify({'error': "You haven't attempted this quiz yet"}), 400
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return jsonify({
        'remarks': quiz.remarks,
        'questions': [{'id': q.id, 'question_statement': q.question_statement, 'option1': q.option1, 'option2': q.option2, 'option3': q.option3, 'option4': q.option4} for q in questions],
        'score': score.total_scored
    })

@auth_bp.route('/set_report_format', methods=['POST'])
def set_report_format():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please log in'}), 403
    data = request.get_json()
    format = data.get('format')
    if format not in ['html', 'pdf']:
        return jsonify({'error': 'Invalid format'}), 400
    user = User.query.get(user_id)
    user.report_format = format
    db.session.commit()
    return jsonify({'message': 'Report format updated'})

@auth_bp.route('/check_auth', methods=['GET'])
def check_auth():
    """Check if user is logged in and get their role"""
    user_id = session.get('user_id')
    is_admin = session.get('admin', False)
    
    if user_id or is_admin:
        return jsonify({
            'logged_in': True,
            'is_admin': is_admin
        })
    else:
        return jsonify({
            'logged_in': False,
            'is_admin': False
        }), 200