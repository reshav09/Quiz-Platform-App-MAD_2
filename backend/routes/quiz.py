from flask import Blueprint, request, jsonify, current_app, g
from models.database import db, Subject, Chapter, Quiz, Question, Score, User
from auth.jwt_utils import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func, desc
from utils.cache import RedisCache, cached_response, invalidate_model_cache

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api/v2/quiz')

# SUBJECT ENDPOINTS
@quiz_bp.route('/subjects', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_subjects():
    """Get all subjects"""
    try:
        subjects = Subject.query.all()
        
        return jsonify({
            'status': 'success',
            'subjects': [subject.to_dict() for subject in subjects]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting subjects: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/subjects/<int:subject_id>', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_subject(subject_id):
    """Get a specific subject"""
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
            
        return jsonify({
            'status': 'success',
            'subject': subject.to_dict(include=['chapters'])
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting subject: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# CHAPTER ENDPOINTS
@quiz_bp.route('/chapters', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_chapters():
    """Get chapters with optional subject filter"""
    try:
        subject_id = request.args.get('subject_id', type=int)
        
        # Filter by subject if specified
        if subject_id:
            chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        else:
            chapters = Chapter.query.all()
            
        return jsonify({
            'status': 'success',
            'chapters': [chapter.to_dict() for chapter in chapters]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chapters: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/chapters/<int:chapter_id>', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_chapter(chapter_id):
    """Get a specific chapter"""
    try:
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'status': 'error', 'message': 'Chapter not found'}), 404
            
        return jsonify({
            'status': 'success',
            'chapter': chapter.to_dict(include=['quizzes']),
            'subject': chapter.subject.to_dict() if chapter.subject else None
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chapter: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# QUIZ ENDPOINTS
@quiz_bp.route('/quizzes', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_quizzes():
    """Get quizzes with optional chapter filter"""
    try:
        chapter_id = request.args.get('chapter_id', type=int)
        
        # Filter by chapter if specified
        if chapter_id:
            quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        else:
            quizzes = Quiz.query.all()
            
        # Format the results
        result = []
        for quiz in quizzes:
            quiz_dict = quiz.to_dict()
            
            # Add chapter and subject info
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                quiz_dict['chapter_name'] = chapter.name
                subject = Subject.query.get(chapter.subject_id) if chapter else None
                if subject:
                    quiz_dict['subject_name'] = subject.name
                    
            # Add question count
            quiz_dict['question_count'] = Question.query.filter_by(quiz_id=quiz.id).count()
            
            result.append(quiz_dict)
            
        return jsonify({
            'status': 'success',
            'quizzes': result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting quizzes: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
@jwt_required
def get_quiz(quiz_id):
    """Get a specific quiz"""
    try:
        # Check if quiz statistics are in cache
        cached_stats = None
        if RedisCache.is_redis_available():
            cached_stats = RedisCache.get(f"stats:quiz:{quiz_id}")
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
            
        # Check if user has already taken this quiz
        user_id = get_jwt_identity()
        user_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
        
        quiz_data = quiz.to_dict()
        
        # Add chapter and subject info
        chapter = Chapter.query.get(quiz.chapter_id)
        if chapter:
            quiz_data['chapter_name'] = chapter.name
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            if subject:
                quiz_data['subject_name'] = subject.name
                
        result = {
            'quiz': quiz_data,
            'has_attempted': user_score is not None,
            'score': user_score.total_scored if user_score else None,
            'attempt_date': user_score.time_stamp_of_attempt.isoformat() if user_score else None
        }
        
        # Add quiz statistics if available
        if cached_stats:
            result['statistics'] = cached_stats
            
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting quiz: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/quizzes/<int:quiz_id>/questions', methods=['GET'])
@jwt_required
def get_quiz_questions(quiz_id):
    """Get questions for a specific quiz"""
    try:
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
            
        # Check if user has already taken this quiz
        user_id = get_jwt_identity()
        user_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
        
        # Get questions
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        
        # If user has not attempted, don't send correct answers
        if not user_score:
            # Remove correct option from response
            questions_data = []
            for q in questions:
                q_dict = q.to_dict()
                # Only remove correct_option if quiz is not yet attempted
                if 'correct_option' in q_dict:
                    del q_dict['correct_option']
                questions_data.append(q_dict)
        else:
            questions_data = [q.to_dict() for q in questions]
            
        return jsonify({
            'status': 'success',
            'quiz_id': quiz_id,
            'quiz_info': quiz.to_dict(),
            'questions': questions_data,
            'has_attempted': user_score is not None
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting quiz questions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/attempt/<int:quiz_id>', methods=['POST'])
@jwt_required
def submit_quiz_attempt(quiz_id):
    """Submit answers for a quiz and receive score"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'answers' not in data:
            return jsonify({'status': 'error', 'message': 'No answers provided'}), 400
            
        # Check if quiz exists
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
            
        # Check if user has already taken this quiz
        existing_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
        if existing_score:
            return jsonify({
                'status': 'error', 
                'message': 'You have already attempted this quiz',
                'score': existing_score.total_scored,
                'attempt_date': existing_score.time_stamp_of_attempt.isoformat()
            }), 400
            
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        if not questions:
            return jsonify({'status': 'error', 'message': 'No questions found for this quiz'}), 404
            
        # Calculate score
        answers = data['answers']  # Expected format: {question_id: selected_option, ...}
        
        total_questions = len(questions)
        correct_answers = 0
        
        for question in questions:
            # Check if user answered this question
            if str(question.id) in answers:
                # Check if answer is correct
                if int(answers[str(question.id)]) == question.correct_option:
                    correct_answers += 1
                    
        # Calculate percentage score
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Save score to database
        new_score = Score(
            user_id=user_id,
            quiz_id=quiz_id,
            total_scored=score_percentage,
            time_stamp_of_attempt=datetime.utcnow()
        )
        
        db.session.add(new_score)
        db.session.commit()
        
        # Invalidate related caches
        if RedisCache.is_redis_available():
            # Invalidate user dashboard and quiz statistics
            invalidate_model_cache('quiz', quiz_id)
            invalidate_model_cache('dashboard')
            # Queue task to update quiz statistics
            try:
                from tasks import celery
                celery.send_task('tasks.update_quiz_statistics')
            except Exception as e:
                current_app.logger.error(f"Failed to queue statistics update: {e}")
        
        # Create response with correct answers
        questions_with_answers = []
        for question in questions:
            q_dict = question.to_dict()
            q_dict['user_answer'] = int(answers.get(str(question.id), 0))
            q_dict['is_correct'] = q_dict['user_answer'] == question.correct_option
            questions_with_answers.append(q_dict)
            
        return jsonify({
            'status': 'success',
            'message': 'Quiz submitted successfully',
            'score': {
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'percentage': score_percentage,
                'id': new_score.id
            },
            'questions': questions_with_answers,
            'quiz_info': quiz.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error submitting quiz: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/dashboard', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=300, key_prefix='dashboard')  # Cache for 5 minutes
def get_user_quiz_dashboard():
    """Get user's quiz dashboard information"""
    try:
        user_id = get_jwt_identity()
        
        # Get user information
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Get overall stats
        quiz_count = Score.query.filter_by(user_id=user_id).count()
        if quiz_count == 0:
            # No quizzes taken yet
            return jsonify({
                'status': 'success',
                'message': 'No quizzes taken yet',
                'user': user.to_dict(exclude=['password']),
                'stats': {
                    'total_quizzes': 0,
                    'average_score': 0,
                    'recent_scores': []
                }
            }), 200
            
        avg_score = db.session.query(func.avg(Score.total_scored))\
            .filter_by(user_id=user_id).scalar() or 0
            
        # Get recent scores
        recent_scores = Score.query.filter_by(user_id=user_id)\
            .order_by(desc(Score.time_stamp_of_attempt))\
            .limit(5).all()
            
        recent_score_data = []
        for score in recent_scores:
            quiz = Quiz.query.get(score.quiz_id)
            chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            
            recent_score_data.append({
                'score_id': score.id,
                'score': score.total_scored,
                'quiz_id': score.quiz_id,
                'quiz_date': quiz.date_of_quiz.isoformat() if hasattr(quiz.date_of_quiz, 'isoformat') else str(quiz.date_of_quiz),
                'attempt_date': score.time_stamp_of_attempt.isoformat(),
                'chapter_name': chapter.name if chapter else 'Unknown',
                'subject_name': subject.name if subject else 'Unknown'
            })
            
        # Get subject performance
        subject_performance = db.session.query(
            Subject.id,
            Subject.name,
            func.avg(Score.total_scored).label('average_score'),
            func.count(Score.id).label('attempts')
        ).join(Chapter, Subject.id == Chapter.subject_id)\
         .join(Quiz, Chapter.id == Quiz.chapter_id)\
         .join(Score, Quiz.id == Score.quiz_id)\
         .filter(Score.user_id == user_id)\
         .group_by(Subject.id, Subject.name)\
         .all()
         
        subject_data = []
        for subject_id, subject_name, avg, attempts in subject_performance:
            subject_data.append({
                'subject_id': subject_id,
                'subject_name': subject_name,
                'average_score': round(avg, 2),
                'attempts': attempts
            })
        
        # Get popular quizzes from cache if available
        popular_quizzes = []
        if RedisCache.is_redis_available():
            popular_quiz_ids = RedisCache.get("stats:popular_quizzes")
            if popular_quiz_ids:
                popular_quizzes = Quiz.query.filter(Quiz.id.in_(popular_quiz_ids)).all()
                popular_quizzes = [q.to_dict() for q in popular_quizzes]
            
        return jsonify({
            'status': 'success',
            'user': user.to_dict(exclude=['password']),
            'stats': {
                'total_quizzes': quiz_count,
                'average_score': round(avg_score, 2),
                'recent_scores': recent_score_data,
                'subject_performance': subject_data,
                'popular_quizzes': popular_quizzes
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user dashboard: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# New endpoints for leaderboards
@quiz_bp.route('/leaderboard/quiz/<int:quiz_id>', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=600, key_prefix='leaderboard')  # Cache for 10 minutes
def get_quiz_leaderboard(quiz_id):
    """Get leaderboard for a specific quiz"""
    try:
        # Verify quiz exists
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
            
        # Get top scores for this quiz
        top_scores = db.session.query(
            Score, User.full_name
        ).join(User, Score.user_id == User.id)\
         .filter(Score.quiz_id == quiz_id)\
         .order_by(desc(Score.total_scored))\
         .limit(10).all()
            
        leaderboard = []
        for score, user_name in top_scores:
            leaderboard.append({
                'user_name': user_name,
                'score': score.total_scored,
                'attempt_date': score.time_stamp_of_attempt.isoformat()
            })
            
        return jsonify({
            'status': 'success',
            'quiz_id': quiz_id,
            'leaderboard': leaderboard
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting quiz leaderboard: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/leaderboard/global', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='leaderboard')  # Cache for 1 hour
def get_global_leaderboard():
    """Get global leaderboard across all quizzes"""
    try:
        # Get average score per user across all quizzes
        user_rankings = db.session.query(
            User.id,
            User.full_name,
            func.avg(Score.total_scored).label('average_score'),
            func.count(Score.id).label('quizzes_taken')
        ).join(Score, User.id == Score.user_id)\
         .group_by(User.id, User.full_name)\
         .having(func.count(Score.id) >= 3)\
         .order_by(desc('average_score'))\
         .limit(20).all()
            
        leaderboard = []
        for user_id, full_name, avg_score, quizzes_taken in user_rankings:
            leaderboard.append({
                'user_id': user_id,
                'user_name': full_name,
                'average_score': round(avg_score, 2),
                'quizzes_taken': quizzes_taken
            })
            
        return jsonify({
            'status': 'success',
            'leaderboard': leaderboard
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting global leaderboard: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_bp.route('/popular', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=3600, key_prefix='quiz')  # Cache for 1 hour
def get_popular_quizzes():
    """Get most popular quizzes based on number of attempts"""
    try:
        # Check if popular quizzes are in cache
        popular_quizzes = None
        if RedisCache.is_redis_available():
            popular_quiz_ids = RedisCache.get("stats:popular_quizzes")
            if popular_quiz_ids:
                popular_quizzes = Quiz.query.filter(Quiz.id.in_(popular_quiz_ids)).all()
        
        # If not in cache, calculate
        if not popular_quizzes:
            popular_quiz_data = db.session.query(
                Quiz.id,
                func.count(Score.id).label('attempts')
            ).join(Score, Quiz.id == Score.quiz_id)\
             .group_by(Quiz.id)\
             .order_by(desc('attempts'))\
             .limit(10).all()
             
            popular_quiz_ids = [quiz_id for quiz_id, _ in popular_quiz_data]
            popular_quizzes = Quiz.query.filter(Quiz.id.in_(popular_quiz_ids)).all()
            
            # Cache the results
            if RedisCache.is_redis_available():
                RedisCache.set("stats:popular_quizzes", popular_quiz_ids, expire_seconds=86400)
        
        # Format results
        result = []
        for quiz in popular_quizzes:
            quiz_dict = quiz.to_dict()
            
            # Add chapter and subject info
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                quiz_dict['chapter_name'] = chapter.name
                subject = Subject.query.get(chapter.subject_id) if chapter else None
                if subject:
                    quiz_dict['subject_name'] = subject.name
            
            # Add statistics if available
            if RedisCache.is_redis_available():
                stats = RedisCache.get(f"stats:quiz:{quiz.id}")
                if stats:
                    quiz_dict['statistics'] = stats
            
            result.append(quiz_dict)
            
        return jsonify({
            'status': 'success',
            'popular_quizzes': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting popular quizzes: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500