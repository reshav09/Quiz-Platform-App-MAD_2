import os
import sys
import logging
from flask import Flask, render_template, send_from_directory, g, jsonify
from flask_cors import CORS

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import configuration
from backend.config import get_config

# Create Flask app
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend')

# Load configuration
config = get_config()
app.config.from_object(config)

# Import database models and initialization function
from backend.models.database import db, init_db
import redis

# Initialize database
init_db(app)

# Setup CORS to allow cross-origin requests
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Redis setup - Try to connect, but make it optional
redis_client = None
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'), 
        port=int(os.environ.get('REDIS_PORT', 6379)), 
        db=int(os.environ.get('REDIS_DB', 0))
    )
    redis_client.ping()  # Test the connection
    print("Redis connection successful")
except (redis.ConnectionError, redis.exceptions.ConnectionError):
    print("Redis server is not available. Some features may not work.")
    logging.warning("Redis server is not available. Some features may not work.")

# Make redis_client available to routes
@app.before_request
def before_request():
    g.redis_client = redis_client

# Initialize Celery
from backend.tasks import make_celery, register_celery_tasks, schedule_periodic_tasks
celery = make_celery(app)
# Register Celery tasks
celery_tasks = register_celery_tasks(celery)
# Schedule periodic tasks
schedule_periodic_tasks(celery)

# Import blueprints after app is initialized to avoid circular imports
from backend.routes.auth_v2 import auth_v2_bp  as auth_bp
from backend.routes.admin import admin_bp
from backend.routes.quiz_history import quiz_history_bp
from backend.routes.export import export_bp
from backend.routes.quiz import quiz_bp  # New quiz routes with better organization
from backend.routes.user_activity import user_activity_bp  # Phase 3: User activity features

# Register blueprints
app.register_blueprint(auth_bp)  # New JWT auth routes
app.register_blueprint(admin_bp, url_prefix='/api/v2/admin')  # Moved admin under v2
app.register_blueprint(quiz_history_bp, url_prefix='/api/v2/history')  # Updated prefix
app.register_blueprint(export_bp, url_prefix='/api/v2/export')  # Updated prefix
app.register_blueprint(quiz_bp, url_prefix='/api/v2/quiz')  # New quiz routes
app.register_blueprint(user_activity_bp)  # Phase 3: User activity endpoints

# For backward compatibility, also register original routes
from backend.routes.auth import auth_bp as auth_bp_v1
app.register_blueprint(auth_bp_v1, url_prefix='/api')

# Additional legacy routes for frontend compatibility
@app.route('/api/user_dashboard')
def user_dashboard_legacy():
    """Legacy route for user dashboard - redirect to new endpoint"""
    from backend.routes.auth import user_dashboard
    return user_dashboard()

@app.route('/api/chapters/<int:subject_id>')
def chapters_legacy(subject_id):
    """Legacy route for chapters by subject"""
    from backend.models.database import Chapter, Subject
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
            
        chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        return jsonify({
            'chapters': [{'id': c.id, 'name': c.name} for c in chapters],
            'subject_name': subject.name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chapter_quizzes/<int:chapter_id>')
def chapter_quizzes_legacy(chapter_id):
    """Legacy route for quizzes by chapter"""
    from backend.models.database import Quiz, Chapter, Subject
    try:
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404
            
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        subject = Subject.query.get(chapter.subject_id) if chapter else None
        
        return jsonify({
            'quizzes': [{'id': q.id, 'date_of_quiz': q.date_of_quiz.strftime('%Y-%m-%d'), 'time_duration': q.time_duration, 'remarks': q.remarks} for q in quizzes],
            'chapter_name': chapter.name,
            'subject_name': subject.name if subject else 'Unknown',
            'subject_id': chapter.subject_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz_history')
def quiz_history_legacy():
    """Legacy route for quiz history"""
    from flask import session
    from backend.models.database import Score, Quiz, Chapter, Subject, User
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Please log in'}), 403
            
        # Get user's quiz history
        history_data = db.session.query(Score, Quiz, Chapter, Subject).join(
            Quiz, Score.quiz_id == Quiz.id
        ).join(
            Chapter, Quiz.chapter_id == Chapter.id
        ).join(
            Subject, Chapter.subject_id == Subject.id
        ).filter(Score.user_id == user_id).order_by(Score.time_stamp_of_attempt.desc()).all()
        
        history = []
        for score, quiz, chapter, subject in history_data:
            history.append({
                'quiz_id': quiz.id,
                'subject_name': subject.name,
                'chapter_name': chapter.name,
                'quiz_date': quiz.date_of_quiz.strftime('%Y-%m-%d'),
                'time_of_attempt': score.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M:%S'),
                'score': score.total_scored
            })
            
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-user-quiz-csv', methods=['POST'])
def export_user_quiz_csv_legacy():
    """Legacy route for CSV export"""
    from flask import session
    import uuid
    import threading
    import time
    from datetime import datetime
    
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Please log in'}), 403
            
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Store task status in a simple dict (in production, use Redis)
        if not hasattr(app, 'export_tasks'):
            app.export_tasks = {}
            
        app.export_tasks[task_id] = {
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Simulate async task
        def complete_task():
            time.sleep(2)  # Simulate processing
            app.export_tasks[task_id] = {
                'status': 'SUCCESS',
                'created_at': app.export_tasks[task_id]['created_at'],
                'completed_at': datetime.utcnow().isoformat()
            }
            
        thread = threading.Thread(target=complete_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Export task started',
            'task_id': task_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/task-status/<task_id>')
def task_status_legacy(task_id):
    """Legacy route for task status"""
    try:
        if not hasattr(app, 'export_tasks') or task_id not in app.export_tasks:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
            
        task_data = app.export_tasks[task_id]
        return jsonify({
            'success': True,
            'status': task_data.get('status', 'UNKNOWN'),
            'created_at': task_data.get('created_at'),
            'completed_at': task_data.get('completed_at')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Frontend Entry Point
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug():
    return render_template('index_debug.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend/static', path)

@app.errorhandler(404)
def page_not_found(e):
    # Handle 404 errors for SPA routing
    return render_template('index.html')

@app.errorhandler(500)
def server_error(e):
    # Log server errors
    app.logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
