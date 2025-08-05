from flask import Blueprint, request, jsonify, current_app, g, send_file, Response
from datetime import datetime, timedelta
from models.database import db, User, Score
from auth.jwt_utils import jwt_required, get_jwt_identity, admin_required
import uuid
import io
from utils.cache import RedisCache

export_bp = Blueprint('export', __name__)

@export_bp.route('/user-quiz-data', methods=['POST'])
@jwt_required
def export_user_quiz_data():
    """
    Start an asynchronous task to export the user's quiz data as a CSV file.
    """
    try:
        user_id = get_jwt_identity()
        
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Queue the export task
        try:
            from tasks import celery
            task = celery.send_task('tasks.export_user_quiz_data', args=[user_id], task_id=task_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Export task started',
                'task_id': task_id,
                'check_status_url': f'/api/v2/export/status/{task_id}'
            }), 202
            
        except Exception as e:
            current_app.logger.error(f"Error queueing export task: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to start export task'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Error in export_user_quiz_data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@export_bp.route('/admin/users-data', methods=['POST'])
@jwt_required
@admin_required
def export_admin_quiz_data():
    """
    Start an asynchronous task to export all users' quiz data for admin as a CSV file.
    Admin access required.
    """
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Queue the export task
        try:
            from tasks import celery
            task = celery.send_task('tasks.export_admin_quiz_data', task_id=task_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Export task started',
                'task_id': task_id,
                'check_status_url': f'/api/v2/export/status/{task_id}'
            }), 202
            
        except Exception as e:
            current_app.logger.error(f"Error queueing admin export task: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to start export task'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Error in export_admin_quiz_data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@export_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required
def get_export_status(task_id):
    """
    Check the status of an export task.
    """
    try:
        # Check if Celery task is completed
        try:
            from tasks import celery
            task_result = celery.AsyncResult(task_id)
            
            if task_result.state == 'PENDING':
                return jsonify({
                    'status': 'pending',
                    'message': 'Export task is still running'
                })
            elif task_result.state == 'SUCCESS':
                result = task_result.get()
                
                if result.get('status') == 'success':
                    return jsonify({
                        'status': 'completed',
                        'message': 'Export completed successfully',
                        'file_key': result.get('file_key'),
                        'download_url': f'/api/v2/export/download/{result.get("file_key")}'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('message', 'Unknown error during export')
                    })
            elif task_result.state == 'FAILURE':
                return jsonify({
                    'status': 'failed',
                    'message': str(task_result.result)
                })
            else:
                return jsonify({
                    'status': task_result.state.lower(),
                    'message': f'Task is in {task_result.state} state'
                })
                
        except Exception as e:
            # If Celery task status check fails, check Redis for task progress
            from tasks import TaskProgressManager
            progress = TaskProgressManager.get_task_progress(task_id)
            
            if progress:
                return jsonify({
                    'status': progress.get('status', 'unknown'),
                    'message': progress.get('message', 'Task in progress'),
                    'progress': progress.get('current_step', 0),
                    'total_steps': progress.get('total_steps', 100)
                })
            else:
                return jsonify({
                    'status': 'unknown',
                    'message': f'Could not determine task status: {str(e)}'
                })
        
    except Exception as e:
        current_app.logger.error(f"Error checking export status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@export_bp.route('/download/<file_key>', methods=['GET'])
@jwt_required
def download_export(file_key):
    """
    Download a previously exported file from Redis cache.
    """
    try:
        if not RedisCache.is_redis_available():
            return jsonify({'status': 'error', 'message': 'Redis cache is not available'}), 503
        
        # Get file from Redis
        csv_data = RedisCache.get(file_key)
        
        if not csv_data:
            return jsonify({'status': 'error', 'message': 'Export file not found or expired'}), 404
        
        # Create a file-like object
        file_obj = io.BytesIO(csv_data.encode('utf-8') if isinstance(csv_data, str) else csv_data)
        
        # Extract timestamp and type from file_key
        # Format: export:user_quiz_data:1:20230715120000 or export:admin_quiz_data:20230715120000
        parts = file_key.split(':')
        export_type = parts[1] if len(parts) > 1 else 'export'
        timestamp = parts[-1] if len(parts) > 2 else datetime.now().strftime('%Y%m%d%H%M%S')
        
        filename = f"{export_type}_{timestamp}.csv"
        
        # Create a response with the file
        return Response(
            file_obj.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading export: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@export_bp.route('/reports/monthly/<user_id>', methods=['GET'])
@jwt_required
def get_monthly_report(user_id):
    """
    Get a user's monthly activity report.
    User can only access their own reports, admin can access any user's reports.
    """
    try:
        # Check if user has permission to access this report
        current_user_id = get_jwt_identity()
        
        # If not admin and not requesting own report, deny access
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Get month parameter (format: YYYYMM)
        month = request.args.get('month', datetime.utcnow().strftime('%Y%m'))
        
        # Check if report exists in Redis
        if not RedisCache.is_redis_available():
            return jsonify({'status': 'error', 'message': 'Redis cache is not available'}), 503
        
        report_key = f"report:monthly:{user_id}:{month}"
        report_html = RedisCache.get(report_key)
        
        if not report_html:
            # Report not found, return an error
            return jsonify({
                'status': 'error',
                'message': f'Monthly report for {month} not found'
            }), 404
        
        # Return the HTML report
        return Response(
            report_html,
            mimetype='text/html'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error getting monthly report: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@export_bp.route('/reports/generate-monthly', methods=['POST'])
@jwt_required
@admin_required
def generate_monthly_reports():
    """
    Manually trigger generation of monthly reports for all users.
    Admin access required.
    """
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Queue the report generation task
        try:
            from tasks import celery
            task = celery.send_task('tasks.generate_monthly_report', task_id=task_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Monthly report generation task started',
                'task_id': task_id
            }), 202
            
        except Exception as e:
            current_app.logger.error(f"Error queueing report generation task: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to start report generation'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Error in generate_monthly_reports: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500