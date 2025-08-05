from flask import Blueprint, request, jsonify, current_app, g
from models.database import db, User, Quiz, Score, Chapter, Subject
from auth.jwt_utils import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from utils.cache import RedisCache, cached_response
import uuid
import json

user_activity_bp = Blueprint('user_activity', __name__, url_prefix='/api')

@user_activity_bp.route('/leaderboard', methods=['GET'])
@jwt_required
@cached_response(expire_seconds=900, key_prefix='leaderboard')  # Cache for 15 minutes
def get_leaderboard():
    """Get user leaderboard across all quizzes"""
    try:
        # Get average score per user across all quizzes
        user_rankings = db.session.query(
            User.id,
            User.username,
            User.full_name,
            func.avg(Score.total_scored).label('average_score'),
            func.count(Score.id).label('quizzes_taken')
        ).join(Score, User.id == Score.user_id)\
         .group_by(User.id, User.username, User.full_name)\
         .having(func.count(Score.id) >= 1)\
         .order_by(desc('average_score'))\
         .limit(10).all()
            
        leaderboard = []
        for user_id, username, full_name, avg_score, quizzes_taken in user_rankings:
            display_name = full_name if full_name else username
            leaderboard.append({
                'user_id': user_id,
                'user_name': display_name,
                'average_score': round(avg_score, 1),
                'quizzes_taken': quizzes_taken
            })
            
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/recent_activity', methods=['GET'])
@jwt_required
def get_recent_activity():
    """Get recent activity for current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get recent quiz attempts
        recent_scores = Score.query.filter_by(user_id=user_id)\
            .order_by(desc(Score.time_stamp_of_attempt))\
            .limit(5).all()
            
        activities = []
        
        # Process quiz attempts into activity items
        for score in recent_scores:
            quiz = Quiz.query.get(score.quiz_id)
            if not quiz:
                continue
                
            chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            
            subject_name = subject.name if subject else "Unknown Subject"
            chapter_name = chapter.name if chapter else "Unknown Chapter"
            
            activities.append({
                'id': str(uuid.uuid4()),
                'title': 'Quiz Completed',
                'description': f"You scored {score.total_scored:.1f}% on {subject_name} - {chapter_name} quiz",
                'timestamp': score.time_stamp_of_attempt
            })
        
        # Get achievement unlocks (simulated for now)
        # In a real app, you'd have an achievements table to query
        achievements = _get_user_achievements(user_id)
        for achievement in achievements:
            if achievement['unlocked'] and achievement['unlock_date']:
                activities.append({
                    'id': str(uuid.uuid4()),
                    'title': 'Achievement Unlocked',
                    'description': f"You earned the \"{achievement['title']}\" achievement",
                    'timestamp': achievement['unlock_date']
                })
        
        # Get new quizzes added recently that might interest the user
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_quizzes = Quiz.query.filter(Quiz.created_at >= week_ago)\
            .order_by(desc(Quiz.created_at))\
            .limit(3).all()
            
        for quiz in new_quizzes:
            chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            
            if subject and chapter:
                activities.append({
                    'id': str(uuid.uuid4()),
                    'title': 'New Quiz Available',
                    'description': f"{subject.name} - {chapter.name} quiz is now available",
                    'timestamp': quiz.created_at
                })
        
        # Sort by timestamp descending
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Convert datetime objects to string for JSON serialization
        for activity in activities:
            activity['timestamp'] = activity['timestamp'].isoformat() \
                if hasattr(activity['timestamp'], 'isoformat') else str(activity['timestamp'])
        
        return jsonify({
            'success': True,
            'activities': activities[:10]  # Limit to 10 most recent
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent activity: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/featured_quizzes', methods=['GET'])
@jwt_required
def get_featured_quizzes():
    """Get featured quizzes for the user"""
    try:
        user_id = get_jwt_identity()
        
        # Strategy: Mix of popular quizzes and personalized recommendations
        featured_quizzes = []
        
        # 1. Get popular quizzes from cache if available
        popular_quiz_ids = []
        if RedisCache.is_redis_available():
            popular_quiz_ids = RedisCache.get("stats:popular_quizzes") or []
        
        # If not in cache, calculate
        if not popular_quiz_ids:
            popular_quiz_data = db.session.query(
                Quiz.id,
                func.count(Score.id).label('attempts')
            ).join(Score, Quiz.id == Score.quiz_id)\
             .group_by(Quiz.id)\
             .order_by(desc('attempts'))\
             .limit(5).all()
             
            popular_quiz_ids = [quiz_id for quiz_id, _ in popular_quiz_data]
        
        # 2. Get quizzes user hasn't taken yet
        taken_quiz_ids = db.session.query(Score.quiz_id)\
            .filter_by(user_id=user_id).all()
        taken_quiz_ids = [q[0] for q in taken_quiz_ids]
        
        # Combine strategies: popular quizzes user hasn't taken + new quizzes
        available_quizzes = Quiz.query.filter(
            ~Quiz.id.in_(taken_quiz_ids) if taken_quiz_ids else True
        ).order_by(desc(Quiz.created_at)).limit(10).all()
        
        # Prioritize popular quizzes
        prioritized_quizzes = []
        for quiz in available_quizzes:
            quiz_dict = quiz.to_dict()
            
            # Add chapter and subject info
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                quiz_dict['chapter_name'] = chapter.name
                subject = Subject.query.get(chapter.subject_id) if chapter else None
                if subject:
                    quiz_dict['subject_name'] = subject.name
            
            # Count questions
            quiz_dict['question_count'] = db.session.query(func.count('*'))\
                .select_from(db.text('questions'))\
                .where(db.text(f'quiz_id = {quiz.id}'))\
                .scalar() or 0
            
            # Add statistics if available
            if RedisCache.is_redis_available():
                stats = RedisCache.get(f"stats:quiz:{quiz.id}")
                if stats:
                    quiz_dict['statistics'] = stats
            
            # Give higher priority to popular quizzes
            if quiz.id in popular_quiz_ids:
                prioritized_quizzes.insert(0, quiz_dict)
            else:
                prioritized_quizzes.append(quiz_dict)
        
        # Return top 6 quizzes
        return jsonify({
            'success': True,
            'quizzes': prioritized_quizzes[:6]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting featured quizzes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/user_achievements', methods=['GET'])
@jwt_required
def get_user_achievements():
    """Get achievements for current user"""
    try:
        user_id = get_jwt_identity()
        achievements = _get_user_achievements(user_id)
        
        return jsonify({
            'success': True,
            'achievements': achievements
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user achievements: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/user_settings', methods=['GET'])
@jwt_required
def get_user_settings():
    """Get user settings"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get report format preference
        report_format = 'html'  # Default
        
        # In a real app, this would be stored in the database
        # For now, we'll check if it's stored in Redis
        if RedisCache.is_redis_available():
            settings = RedisCache.get(f"settings:user:{user_id}")
            if settings:
                report_format = settings.get('report_format', 'html')
        
        notification_settings = {
            'email': True,
            'reminders': True,
            'reports': True
        }
        
        if RedisCache.is_redis_available():
            stored_settings = RedisCache.get(f"notification_settings:user:{user_id}")
            if stored_settings:
                notification_settings.update(stored_settings)
        
        return jsonify({
            'success': True,
            'report_format': report_format,
            'notification_settings': notification_settings
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/set_report_format', methods=['POST'])
@jwt_required
def set_report_format():
    """Set report format preference"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'format' not in data:
            return jsonify({'success': False, 'message': 'No format specified'}), 400
        
        report_format = data['format']
        if report_format not in ['html', 'pdf']:
            return jsonify({'success': False, 'message': 'Invalid format'}), 400
        
        # In a real app, update user settings in database
        # For now, we'll store in Redis
        if RedisCache.is_redis_available():
            settings = RedisCache.get(f"settings:user:{user_id}") or {}
            settings['report_format'] = report_format
            RedisCache.set(f"settings:user:{user_id}", settings, expire_seconds=2592000)  # 30 days
        
        return jsonify({'success': True, 'message': 'Report format updated'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error setting report format: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/update_notification_settings', methods=['POST'])
@jwt_required
def update_notification_settings():
    """Update notification settings"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'settings' not in data:
            return jsonify({'success': False, 'message': 'No settings specified'}), 400
        
        settings = data['settings']
        
        # Validate settings
        required_keys = ['email', 'reminders', 'reports']
        for key in required_keys:
            if key not in settings:
                return jsonify({'success': False, 'message': f'Missing setting: {key}'}), 400
        
        # In a real app, update user settings in database
        # For now, we'll store in Redis
        if RedisCache.is_redis_available():
            RedisCache.set(
                f"notification_settings:user:{user_id}", 
                settings, 
                expire_seconds=2592000  # 30 days
            )
        
        return jsonify({'success': True, 'message': 'Notification settings updated'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating notification settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/export-user-quiz-csv', methods=['POST'])
@jwt_required
def export_user_quiz_csv():
    """Export user quiz data as CSV"""
    try:
        user_id = get_jwt_identity()
        
        # In a real app, we'd queue this task with Celery
        # For now, we'll simulate it
        task_id = f"export_quiz_data_{uuid.uuid4()}"
        
        if RedisCache.is_redis_available():
            # Store task status
            task_data = {
                'status': 'PENDING',
                'created_at': datetime.utcnow().isoformat()
            }
            RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            # In a real app, we'd send this to Celery
            # For demo, we'll simulate completing the task after a delay
            def complete_task():
                # This would be handled by Celery in a real app
                import time
                time.sleep(5)  # Simulate processing time
                
                task_data['status'] = 'SUCCESS'
                task_data['completed_at'] = datetime.utcnow().isoformat()
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            import threading
            thread = threading.Thread(target=complete_task)
            thread.daemon = True
            thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Export task queued',
            'task_id': task_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error queuing export task: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_activity_bp.route('/task-status/<task_id>', methods=['GET'])
@jwt_required
def get_task_status(task_id):
    """Get status of a background task"""
    try:
        if not RedisCache.is_redis_available():
            return jsonify({'success': False, 'message': 'Task tracking not available'}), 500
        
        task_data = RedisCache.get(f"task:{task_id}")
        if not task_data:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        return jsonify({
            'success': True,
            'status': task_data.get('status', 'UNKNOWN'),
            'created_at': task_data.get('created_at'),
            'completed_at': task_data.get('completed_at')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error checking task status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def _get_user_achievements(user_id):
    """Helper function to get user achievements"""
    # In a real app, this would query the database
    # For now, we'll generate them based on the user's scores
    
    achievements = [
        {
            'id': 'first_quiz',
            'title': 'First Quiz',
            'description': 'Complete your first quiz',
            'icon': 'fas fa-star',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        },
        {
            'id': 'quiz_master',
            'title': 'Quiz Master',
            'description': 'Score 90% or higher on 5 quizzes',
            'icon': 'fas fa-crown',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        },
        {
            'id': 'subject_expert',
            'title': 'Subject Expert',
            'description': 'Complete all quizzes in a subject',
            'icon': 'fas fa-brain',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        },
        {
            'id': 'streak',
            'title': '7-Day Streak',
            'description': 'Take quizzes for 7 consecutive days',
            'icon': 'fas fa-fire',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        },
        {
            'id': 'perfect_score',
            'title': 'Perfect Score',
            'description': 'Get 100% on any quiz',
            'icon': 'fas fa-trophy',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        },
        {
            'id': 'speed_demon',
            'title': 'Speed Demon',
            'description': 'Complete a quiz in half the allotted time',
            'icon': 'fas fa-bolt',
            'progress': 0,
            'unlocked': False,
            'unlock_date': None
        }
    ]
    
    # Check user's scores to calculate achievements
    scores = Score.query.filter_by(user_id=user_id).all()
    
    # First Quiz
    if scores:
        achievements[0]['progress'] = 100
        achievements[0]['unlocked'] = True
        achievements[0]['unlock_date'] = min(scores, key=lambda s: s.time_stamp_of_attempt).time_stamp_of_attempt
    
    # Quiz Master
    high_scores = [s for s in scores if s.total_scored >= 90]
    if high_scores:
        progress = min(len(high_scores) * 20, 100)
        achievements[1]['progress'] = progress
        if progress >= 100:
            achievements[1]['unlocked'] = True
            achievements[1]['unlock_date'] = max(high_scores, key=lambda s: s.time_stamp_of_attempt).time_stamp_of_attempt
    
    # Subject Expert - check if user has completed all quizzes in any subject
    # This would need a more complex query in a real app
    if scores:
        # Simulate partial progress
        achievements[2]['progress'] = min(len(scores) * 5, 45)
    
    # 7-Day Streak
    if scores:
        # Check for consecutive days
        dates = set([s.time_stamp_of_attempt.date() for s in scores])
        today = datetime.utcnow().date()
        
        # For demo, check if there are scores on 3 different days in the last week
        week_ago = today - timedelta(days=7)
        recent_dates = [d for d in dates if d >= week_ago]
        
        if recent_dates:
            days = len(recent_dates)
            achievements[3]['progress'] = min(days * 14, 100)
            if days >= 7:
                achievements[3]['unlocked'] = True
                achievements[3]['unlock_date'] = datetime.combine(max(recent_dates), datetime.min.time())
    
    # Perfect Score
    perfect_scores = [s for s in scores if s.total_scored == 100]
    if perfect_scores:
        achievements[4]['progress'] = 100
        achievements[4]['unlocked'] = True
        achievements[4]['unlock_date'] = perfect_scores[0].time_stamp_of_attempt
    
    # Speed Demon - would need to track completion time in a real app
    # For demo, we'll simulate it
    if scores and len(scores) > 5:
        achievements[5]['progress'] = 80
    
    return achievements