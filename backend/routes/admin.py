from flask import Blueprint, request, jsonify, current_app
from backend.models.database import db, User, Subject, Chapter, Quiz, Question, Score, Admin
from backend.auth.jwt_utils import jwt_required, get_jwt_identity
from datetime import datetime
import hashlib
from functools import wraps
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)

# Helper function to check if the user is an admin
def admin_required(f):
    """
    Decorator to check if the user is an admin
    Must be used after jwt_required
    """
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        # Check if user_id corresponds to an admin
        admin = Admin.query.get(int(user_id))
        if not admin:
            return jsonify({'status': 'error', 'message': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'username' not in data or 'password' not in data:
            return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
        
        # Authenticate admin
        admin = Admin.authenticate(data['username'], data['password'])
        
        if not admin:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401
        
        # Generate access token
        from backend.auth.jwt_utils import create_access_token
        access_token = create_access_token(admin.id, is_admin=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Admin login successful',
            'admin': admin.to_dict(exclude=['password']),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Admin login error: {e}")
        return jsonify({'status': 'error', 'message': f'Login failed: {str(e)}'}), 500

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    """Get system statistics for admin dashboard"""
    try:
        # Count of users
        user_count = User.query.count()
        
        # Count of subjects
        subject_count = Subject.query.count()
        
        # Count of quizzes
        quiz_count = Quiz.query.count()
        
        # Recent quiz attempts
        recent_scores = Score.query.order_by(desc(Score.time_stamp_of_attempt)).limit(10).all()
        
        # Average score by quiz
        avg_scores = db.session.query(
            Quiz.id,
            func.avg(Score.total_scored).label('average_score')
        ).join(Score).group_by(Quiz.id).all()
        
        quiz_stats = {}
        for quiz_id, avg_score in avg_scores:
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                quiz_stats[quiz_id] = {
                    'quiz_date': quiz.date_of_quiz.isoformat() if hasattr(quiz.date_of_quiz, 'isoformat') else str(quiz.date_of_quiz),
                    'chapter_name': quiz.chapter.name if quiz.chapter else 'Unknown',
                    'average_score': round(avg_score, 2)
                }
        
        return jsonify({
            'status': 'success',
            'statistics': {
                'user_count': user_count,
                'subject_count': subject_count,
                'quiz_count': quiz_count,
                'quiz_stats': quiz_stats,
                'recent_scores': [score.to_dict() for score in recent_scores]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Admin dashboard error: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to get dashboard data: {str(e)}'}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users for admin"""
    try:
        users = User.query.all()
        return jsonify({
            'status': 'success',
            'users': [user.to_dict(exclude=['password']) for user in users]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting users: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        return jsonify({
            'status': 'success',
            'user': user.to_dict(exclude=['password'])
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User deleted successfully'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/scores', methods=['GET'])
@admin_required
def get_all_scores():
    """Get all quiz scores for admin"""
    try:
        scores = Score.query.order_by(desc(Score.time_stamp_of_attempt)).all()
        
        return jsonify({
            'status': 'success',
            'scores': [score.to_dict() for score in scores]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting scores: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/report', methods=['GET'])
@admin_required
def get_report():
    """Generate system report for admin"""
    try:
        # User statistics
        users = User.query.count()
        users_with_quiz = db.session.query(func.count(func.distinct(Score.user_id))).scalar() or 0
        
        # Quiz statistics
        quizzes = Quiz.query.count()
        total_questions = Question.query.count()
        
        # Subject statistics
        subjects = Subject.query.count()
        chapters = Chapter.query.count()
        
        # Participation statistics
        quiz_attempts = Score.query.count()
        avg_score = db.session.query(func.avg(Score.total_scored)).scalar() or 0
        
        return jsonify({
            'status': 'success',
            'report': {
                'generated_at': datetime.utcnow().isoformat(),
                'user_statistics': {
                    'total_users': users,
                    'active_users': users_with_quiz,
                    'participation_rate': round((users_with_quiz / users) * 100 if users > 0 else 0, 2)
                },
                'content_statistics': {
                    'subjects': subjects,
                    'chapters': chapters,
                    'quizzes': quizzes,
                    'questions': total_questions,
                    'avg_questions_per_quiz': round(total_questions / quizzes if quizzes > 0 else 0, 2)
                },
                'performance_statistics': {
                    'quiz_attempts': quiz_attempts,
                    'avg_score': round(avg_score, 2),
                    'attempts_per_user': round(quiz_attempts / users_with_quiz if users_with_quiz > 0 else 0, 2)
                }
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error generating report: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# SUBJECT CRUD OPERATIONS
@admin_bp.route('/subjects', methods=['POST'])
@admin_required
def create_subject():
    """Create a new subject"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'status': 'error', 'message': 'Subject name is required'}), 400
        
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(name=data['name']).first()
        if existing_subject:
            return jsonify({'status': 'error', 'message': 'Subject already exists'}), 409
        
        new_subject = Subject(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(new_subject)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Subject created successfully',
            'subject': new_subject.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating subject: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/subjects/<int:subject_id>', methods=['PUT'])
@admin_required
def update_subject(subject_id):
    """Update a subject"""
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if name already exists for another subject
            existing_subject = Subject.query.filter_by(name=data['name']).first()
            if existing_subject and existing_subject.id != subject_id:
                return jsonify({'status': 'error', 'message': 'Subject name already exists'}), 409
            subject.name = data['name']
        
        if 'description' in data:
            subject.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Subject updated successfully',
            'subject': subject.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating subject: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@admin_required
def delete_subject(subject_id):
    """Delete a subject"""
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
        
        # Check if subject has chapters
        if subject.chapters:
            return jsonify({'status': 'error', 'message': 'Cannot delete subject with existing chapters'}), 400
        
        db.session.delete(subject)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Subject deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting subject: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# CHAPTER CRUD OPERATIONS
@admin_bp.route('/chapters', methods=['POST'])
@admin_required
def create_chapter():
    """Create a new chapter"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'subject_id' not in data:
            return jsonify({'status': 'error', 'message': 'Chapter name and subject_id are required'}), 400
        
        # Check if subject exists
        subject = Subject.query.get(data['subject_id'])
        if not subject:
            return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
        
        # Check if chapter already exists in this subject
        existing_chapter = Chapter.query.filter_by(
            name=data['name'], 
            subject_id=data['subject_id']
        ).first()
        if existing_chapter:
            return jsonify({'status': 'error', 'message': 'Chapter already exists in this subject'}), 409
        
        new_chapter = Chapter(
            name=data['name'],
            description=data.get('description', ''),
            subject_id=data['subject_id']
        )
        
        db.session.add(new_chapter)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Chapter created successfully',
            'chapter': new_chapter.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating chapter: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/chapters/<int:chapter_id>', methods=['PUT'])
@admin_required
def update_chapter(chapter_id):
    """Update a chapter"""
    try:
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'status': 'error', 'message': 'Chapter not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if name already exists in the same subject
            existing_chapter = Chapter.query.filter_by(
                name=data['name'], 
                subject_id=chapter.subject_id
            ).first()
            if existing_chapter and existing_chapter.id != chapter_id:
                return jsonify({'status': 'error', 'message': 'Chapter name already exists in this subject'}), 409
            chapter.name = data['name']
        
        if 'description' in data:
            chapter.description = data['description']
        
        if 'subject_id' in data:
            # Check if new subject exists
            subject = Subject.query.get(data['subject_id'])
            if not subject:
                return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
            chapter.subject_id = data['subject_id']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Chapter updated successfully',
            'chapter': chapter.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating chapter: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/chapters/<int:chapter_id>', methods=['DELETE'])
@admin_required
def delete_chapter(chapter_id):
    """Delete a chapter"""
    try:
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'status': 'error', 'message': 'Chapter not found'}), 404
        
        # Check if chapter has quizzes
        if chapter.quizzes:
            return jsonify({'status': 'error', 'message': 'Cannot delete chapter with existing quizzes'}), 400
        
        db.session.delete(chapter)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Chapter deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting chapter: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# QUIZ CRUD OPERATIONS
@admin_bp.route('/quizzes', methods=['POST'])
@admin_required
def create_quiz():
    """Create a new quiz"""
    try:
        data = request.get_json()
        
        if not data or 'chapter_id' not in data or 'date_of_quiz' not in data or 'time_duration' not in data:
            return jsonify({'status': 'error', 'message': 'Chapter ID, date, and time duration are required'}), 400
        
        # Check if chapter exists
        chapter = Chapter.query.get(data['chapter_id'])
        if not chapter:
            return jsonify({'status': 'error', 'message': 'Chapter not found'}), 404
        
        new_quiz = Quiz(
            chapter_id=data['chapter_id'],
            date_of_quiz=datetime.strptime(data['date_of_quiz'], '%Y-%m-%d').date(),
            time_duration=data['time_duration'],
            remarks=data.get('remarks', '')
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Quiz created successfully',
            'quiz': new_quiz.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating quiz: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/quizzes/<int:quiz_id>', methods=['PUT'])
@admin_required
def update_quiz(quiz_id):
    """Update a quiz"""
    try:
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
        
        data = request.get_json()
        
        if 'chapter_id' in data:
            # Check if chapter exists
            chapter = Chapter.query.get(data['chapter_id'])
            if not chapter:
                return jsonify({'status': 'error', 'message': 'Chapter not found'}), 404
            quiz.chapter_id = data['chapter_id']
        
        if 'date_of_quiz' in data:
            quiz.date_of_quiz = datetime.strptime(data['date_of_quiz'], '%Y-%m-%d').date()
        
        if 'time_duration' in data:
            quiz.time_duration = data['time_duration']
        
        if 'remarks' in data:
            quiz.remarks = data['remarks']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Quiz updated successfully',
            'quiz': quiz.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating quiz: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
@admin_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    try:
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
        
        # Check if quiz has scores (attempts)
        if quiz.scores:
            return jsonify({'status': 'error', 'message': 'Cannot delete quiz with existing attempts'}), 400
        
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Quiz deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting quiz: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ADMIN GET ROUTES FOR SUBJECTS, CHAPTERS, AND QUIZZES
@admin_bp.route('/subjects', methods=['GET'])
@admin_required
def get_admin_subjects():
    """Get all subjects for admin"""
    try:
        subjects = Subject.query.all()
        return jsonify({
            'status': 'success',
            'subjects': [subject.to_dict(include=['chapters']) for subject in subjects]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting subjects: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/chapters', methods=['GET'])
@admin_required
def get_admin_chapters():
    """Get all chapters for admin"""
    try:
        subject_id = request.args.get('subject_id', type=int)
        
        if subject_id:
            chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        else:
            chapters = Chapter.query.all()
            
        return jsonify({
            'status': 'success',
            'chapters': [chapter.to_dict(include=['subject', 'quizzes']) for chapter in chapters]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chapters: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/quizzes', methods=['GET'])
@admin_required
def get_admin_quizzes():
    """Get all quizzes for admin"""
    try:
        chapter_id = request.args.get('chapter_id', type=int)
        
        if chapter_id:
            quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        else:
            quizzes = Quiz.query.all()
            
        return jsonify({
            'status': 'success',
            'quizzes': [quiz.to_dict(include=['chapter', 'questions']) for quiz in quizzes]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting quizzes: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# CSV IMPORT FUNCTIONALITY
@admin_bp.route('/import/subjects', methods=['POST'])
@admin_required
def import_subjects_csv():
    """Import subjects from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        # Read CSV file
        import csv
        import io
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Validate required fields
                if not row.get('name'):
                    errors.append(f"Row {row_num}: Subject name is required")
                    continue
                
                # Check if subject already exists
                existing_subject = Subject.query.filter_by(name=row['name']).first()
                if existing_subject:
                    errors.append(f"Row {row_num}: Subject '{row['name']}' already exists")
                    continue
                
                # Create new subject
                new_subject = Subject(
                    name=row['name'],
                    description=row.get('description', '')
                )
                
                db.session.add(new_subject)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully imported {imported_count} subjects',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error importing subjects CSV: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/import/chapters', methods=['POST'])
@admin_required
def import_chapters_csv():
    """Import chapters from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        # Read CSV file
        import csv
        import io
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                if not row.get('name') or not row.get('subject_id'):
                    errors.append(f"Row {row_num}: Chapter name and subject_id are required")
                    continue
                
                # Check if subject exists
                subject = Subject.query.get(int(row['subject_id']))
                if not subject:
                    errors.append(f"Row {row_num}: Subject with ID {row['subject_id']} not found")
                    continue
                
                # Check if chapter already exists in this subject
                existing_chapter = Chapter.query.filter_by(
                    name=row['name'], 
                    subject_id=int(row['subject_id'])
                ).first()
                if existing_chapter:
                    errors.append(f"Row {row_num}: Chapter '{row['name']}' already exists in subject")
                    continue
                
                # Create new chapter
                new_chapter = Chapter(
                    name=row['name'],
                    description=row.get('description', ''),
                    subject_id=int(row['subject_id'])
                )
                
                db.session.add(new_chapter)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully imported {imported_count} chapters',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error importing chapters CSV: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/import/quizzes', methods=['POST'])
@admin_required
def import_quizzes_csv():
    """Import quizzes from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        # Read CSV file
        import csv
        import io
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                if not row.get('chapter_id') or not row.get('date_of_quiz') or not row.get('time_duration'):
                    errors.append(f"Row {row_num}: Chapter ID, date, and time duration are required")
                    continue
                
                # Check if chapter exists
                chapter = Chapter.query.get(int(row['chapter_id']))
                if not chapter:
                    errors.append(f"Row {row_num}: Chapter with ID {row['chapter_id']} not found")
                    continue
                
                # Parse date
                try:
                    quiz_date = datetime.strptime(row['date_of_quiz'], '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid date format. Use YYYY-MM-DD")
                    continue
                
                # Create new quiz
                new_quiz = Quiz(
                    chapter_id=int(row['chapter_id']),
                    date_of_quiz=quiz_date,
                    time_duration=row['time_duration'],
                    remarks=row.get('remarks', '')
                )
                
                db.session.add(new_quiz)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully imported {imported_count} quizzes',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error importing quizzes CSV: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# QUESTION CRUD OPERATIONS
@admin_bp.route('/questions', methods=['POST'])
@admin_required
def create_question():
    """Create a new question"""
    try:
        data = request.get_json()
        
        if not data or 'quiz_id' not in data or 'question_statement' not in data:
            return jsonify({'status': 'error', 'message': 'Quiz ID and question statement are required'}), 400
        
        # Check if quiz exists
        quiz = Quiz.query.get(data['quiz_id'])
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
        
        # Validate options
        required_options = ['option1', 'option2', 'option3', 'option4', 'correct_option']
        for option in required_options:
            if option not in data:
                return jsonify({'status': 'error', 'message': f'{option} is required'}), 400
        
        # Validate correct_option
        try:
            correct_option = int(data['correct_option'])
            if correct_option not in [1, 2, 3, 4]:
                return jsonify({'status': 'error', 'message': 'Correct option must be 1, 2, 3, or 4'}), 400
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Correct option must be a number'}), 400
        
        new_question = Question(
            quiz_id=data['quiz_id'],
            question_statement=data['question_statement'],
            option1=data['option1'],
            option2=data['option2'],
            option3=data['option3'],
            option4=data['option4'],
            correct_option=correct_option
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Question created successfully',
            'question': new_question.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating question: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>', methods=['PUT'])
@admin_required
def update_question(question_id):
    """Update a question"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'status': 'error', 'message': 'Question not found'}), 404
        
        data = request.get_json()
        
        if 'question_statement' in data:
            question.question_statement = data['question_statement']
        
        if 'option1' in data:
            question.option1 = data['option1']
        
        if 'option2' in data:
            question.option2 = data['option2']
        
        if 'option3' in data:
            question.option3 = data['option3']
        
        if 'option4' in data:
            question.option4 = data['option4']
        
        if 'correct_option' in data:
            try:
                correct_option = int(data['correct_option'])
                if correct_option not in [1, 2, 3, 4]:
                    return jsonify({'status': 'error', 'message': 'Correct option must be 1, 2, 3, or 4'}), 400
                question.correct_option = correct_option
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Correct option must be a number'}), 400
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Question updated successfully',
            'question': question.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating question: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(question_id):
    """Delete a question"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'status': 'error', 'message': 'Question not found'}), 404
        
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Question deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting question: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/questions', methods=['GET'])
@admin_required
def get_admin_questions():
    """Get all questions for admin"""
    try:
        quiz_id = request.args.get('quiz_id', type=int)
        
        if quiz_id:
            questions = Question.query.filter_by(quiz_id=quiz_id).all()
        else:
            questions = Question.query.all()
            
        return jsonify({
            'status': 'success',
            'questions': [question.to_dict() for question in questions]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting questions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>', methods=['GET'])
@admin_required
def get_admin_question(question_id):
    """Get a specific question for admin"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'status': 'error', 'message': 'Question not found'}), 404
            
        return jsonify({
            'status': 'success',
            'question': question.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting question: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/trigger-daily-reminders', methods=['POST'])
@admin_required
def trigger_daily_reminders():
    """Manually trigger daily reminders for testing"""
    try:
        from tasks import celery
        task = celery.send_task('tasks.send_daily_reminders')
        
        return jsonify({
            'status': 'success',
            'message': 'Daily reminders task triggered successfully',
            'task_id': task.id
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error triggering daily reminders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/trigger-monthly-reports', methods=['POST'])
@admin_required
def trigger_monthly_reports():
    """Manually trigger monthly reports for testing"""
    try:
        from tasks import celery
        task = celery.send_task('tasks.send_monthly_report')
        
        return jsonify({
            'status': 'success',
            'message': 'Monthly reports task triggered successfully',
            'task_id': task.id
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error triggering monthly reports: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500