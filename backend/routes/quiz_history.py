from flask import Blueprint, request, jsonify, current_app
from models.database import db, Subject, Chapter, Quiz, Question, Score
from auth.jwt_utils import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import desc, func

quiz_history_bp = Blueprint('quiz_history', __name__)

@quiz_history_bp.route('/scores', methods=['GET'])
@jwt_required
def get_user_scores():
    """Get all quiz scores for the logged in user"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters for filtering
        subject_id = request.args.get('subject_id', type=int)
        chapter_id = request.args.get('chapter_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Base query
        query = Score.query.filter_by(user_id=user_id)
        
        # Apply filters if provided
        if subject_id:
            query = query.join(Quiz).join(Chapter).filter(Chapter.subject_id == subject_id)
            
        if chapter_id:
            query = query.join(Quiz).filter(Quiz.chapter_id == chapter_id)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Score.time_stamp_of_attempt >= date_from_obj)
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Score.time_stamp_of_attempt <= date_to_obj)
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
                
        # Order by most recent first
        scores = query.order_by(desc(Score.time_stamp_of_attempt)).all()
        
        return jsonify({
            'status': 'success',
            'scores': [score.to_dict() for score in scores]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user scores: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_history_bp.route('/scores/<int:score_id>', methods=['GET'])
@jwt_required
def get_score_details(score_id):
    """Get detailed information about a specific score"""
    try:
        user_id = get_jwt_identity()
        
        # Get score with owner verification
        score = Score.query.filter_by(id=score_id, user_id=user_id).first()
        
        if not score:
            return jsonify({'status': 'error', 'message': 'Score not found or access denied'}), 404
            
        # Get quiz details
        quiz = Quiz.query.get(score.quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
            
        # Get questions for this quiz
        questions = Question.query.filter_by(quiz_id=quiz.id).all()
        
        # Get chapter and subject info
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id) if chapter else None
        
        # Build detailed response
        result = {
            'score': score.to_dict(),
            'quiz': quiz.to_dict(),
            'questions': [q.to_dict() for q in questions],
            'chapter': chapter.to_dict() if chapter else None,
            'subject': subject.to_dict() if subject else None,
            'attempt_date': score.time_stamp_of_attempt.isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'details': result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting score details: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_history_bp.route('/stats', methods=['GET'])
@jwt_required
def get_user_stats():
    """Get statistics about the user's quiz performance"""
    try:
        user_id = get_jwt_identity()
        
        # Total quizzes attempted
        quiz_count = db.session.query(func.count(Score.id)).filter(Score.user_id == user_id).scalar() or 0
        
        # Average score
        avg_score = db.session.query(func.avg(Score.total_scored)).filter(Score.user_id == user_id).scalar() or 0
        
        # Best score
        best_score = db.session.query(func.max(Score.total_scored)).filter(Score.user_id == user_id).scalar() or 0
        
        # Recent attempts
        recent_scores = Score.query.filter_by(user_id=user_id).order_by(desc(Score.time_stamp_of_attempt)).limit(5).all()
        
        # Performance by subject
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
         
        subjects_data = []
        for subject_id, subject_name, avg, attempts in subject_performance:
            subjects_data.append({
                'subject_id': subject_id,
                'subject_name': subject_name,
                'average_score': round(avg, 2),
                'attempts': attempts
            })
        
        return jsonify({
            'status': 'success',
            'statistics': {
                'total_quizzes': quiz_count,
                'average_score': round(avg_score, 2),
                'best_score': round(best_score, 2),
                'recent_attempts': [score.to_dict() for score in recent_scores],
                'subject_performance': subjects_data
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@quiz_history_bp.route('/progress', methods=['GET'])
@jwt_required
def get_user_progress():
    """Get the user's progress over time"""
    try:
        user_id = get_jwt_identity()
        
        # Get scores ordered by date
        scores = Score.query.filter_by(user_id=user_id).order_by(Score.time_stamp_of_attempt).all()
        
        # Format data for timeline visualization
        timeline_data = []
        for score in scores:
            quiz = Quiz.query.get(score.quiz_id)
            chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            
            timeline_data.append({
                'date': score.time_stamp_of_attempt.isoformat(),
                'score': score.total_scored,
                'quiz_id': score.quiz_id,
                'chapter_name': chapter.name if chapter else 'Unknown',
                'subject_name': subject.name if subject else 'Unknown'
            })
        
        # Calculate improvement trend
        improvement = 0
        if len(scores) >= 2:
            first_score = scores[0].total_scored
            last_score = scores[-1].total_scored
            improvement = last_score - first_score
            
        return jsonify({
            'status': 'success',
            'progress': {
                'timeline': timeline_data,
                'total_attempts': len(scores),
                'improvement': round(improvement, 2),
                'improvement_percentage': round((improvement / first_score * 100) if first_score > 0 else 0, 2)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user progress: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500