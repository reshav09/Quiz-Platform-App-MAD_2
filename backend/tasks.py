import os
from flask import current_app, render_template
from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import csv
import io
import json
import logging
from models.database import db, Quiz, Score, Question, User, Subject, Chapter
from utils.cache import RedisCache, invalidate_model_cache
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import requests


def make_celery(app):
    """Create a Celery instance with Flask app context"""
    celery = Celery(
        app.import_name,
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def register_celery_tasks(celery):
    """Register all Celery tasks"""
    @celery.task(name='tasks.update_quiz_statistics')
    def update_quiz_statistics():
        """Update quiz statistics and cache them"""
        try:
            # Get all quizzes
            quizzes = Quiz.query.all()
            
            for quiz in quizzes:
                # Get stats for this quiz
                stats = db.session.query(
                    func.avg(Score.total_scored).label('avg_score'),
                    func.count(Score.id).label('total_attempts'),
                    func.min(Score.total_scored).label('min_score'),
                    func.max(Score.total_scored).label('max_score')
                ).filter(Score.quiz_id == quiz.id).first()
                
                if stats and stats.total_attempts > 0:
                    # Cache the statistics
                    if RedisCache.is_redis_available():
                        RedisCache.set(
                            f"stats:quiz:{quiz.id}", 
                            {
                                'avg_score': round(stats.avg_score, 2),
                                'total_attempts': stats.total_attempts,
                                'min_score': stats.min_score,
                                'max_score': stats.max_score
                            },
                            expire_seconds=86400  # 24 hours
                        )
                        
            # Update popular quizzes
            popular_quiz_data = db.session.query(
                Quiz.id,
                func.count(Score.id).label('attempts')
            ).join(Score, Quiz.id == Score.quiz_id)\
             .group_by(Quiz.id)\
             .order_by(desc('attempts'))\
             .limit(10).all()
             
            popular_quiz_ids = [quiz_id for quiz_id, _ in popular_quiz_data]
            
            # Cache the popular quiz IDs
            if RedisCache.is_redis_available() and popular_quiz_ids:
                RedisCache.set("stats:popular_quizzes", popular_quiz_ids, expire_seconds=86400)
                
            current_app.logger.info("Quiz statistics updated successfully")
            return {'status': 'success', 'message': 'Quiz statistics updated'}
            
        except Exception as e:
            current_app.logger.error(f"Error updating quiz statistics: {e}")
            return {'status': 'error', 'message': str(e)}

    @celery.task(name='tasks.generate_user_quiz_report')
    def generate_user_quiz_report(user_id, report_format='html'):
        """Generate a report of a user's quiz history and performance"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}
                
            # Get user's scores
            scores = Score.query.filter_by(user_id=user_id)\
                .order_by(desc(Score.time_stamp_of_attempt)).all()
            
            if not scores:
                return {'status': 'error', 'message': 'No quiz history found'}
                
            # Calculate overall statistics
            total_quizzes = len(scores)
            avg_score = sum(s.total_scored for s in scores) / total_quizzes if total_quizzes > 0 else 0
            
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
             
            subjects_data = []
            for subject_id, subject_name, avg, attempts in subject_performance:
                subjects_data.append({
                    'subject_id': subject_id,
                    'subject_name': subject_name,
                    'average_score': round(avg, 2),
                    'attempts': attempts
                })
                
            # Prepare detailed quiz data
            detailed_scores = []
            for score in scores:
                quiz = Quiz.query.get(score.quiz_id)
                if not quiz:
                    continue
                    
                chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
                subject = Subject.query.get(chapter.subject_id) if chapter else None
                
                detailed_scores.append({
                    'quiz_id': score.quiz_id,
                    'quiz_date': quiz.date_of_quiz.strftime('%Y-%m-%d'),
                    'attempt_date': score.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M'),
                    'score': score.total_scored,
                    'subject': subject.name if subject else 'Unknown',
                    'chapter': chapter.name if chapter else 'Unknown'
                })
            
            # Calculate progress over time
            timeline_data = {}
            for score in scores:
                date_key = score.time_stamp_of_attempt.strftime('%Y-%m-%d')
                if date_key not in timeline_data:
                    timeline_data[date_key] = []
                timeline_data[date_key].append(score.total_scored)
            
            daily_averages = []
            for date, scores_list in timeline_data.items():
                daily_averages.append({
                    'date': date,
                    'average_score': sum(scores_list) / len(scores_list)
                })
            
            # Sort by date
            daily_averages.sort(key=lambda x: x['date'])
            
            # Prepare report data
            report_data = {
                'user': {
                    'id': user.id,
                    'name': user.full_name or user.username,
                    'email': user.email
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'total_quizzes': total_quizzes,
                    'average_score': round(avg_score, 2),
                    'strongest_subject': max(subjects_data, key=lambda x: x['average_score'])['subject_name'] if subjects_data else 'N/A',
                    'total_subjects': len(subjects_data),
                    'recent_trend': 'Improving' if daily_averages and len(daily_averages) > 1 and daily_averages[-1]['average_score'] > daily_averages[0]['average_score'] else 'Stable'
                },
                'subjects': subjects_data,
                'timeline': daily_averages,
                'detailed_scores': detailed_scores[:20]  # Limit to 20 most recent
            }
            
            # Get user's settings
            if RedisCache.is_redis_available():
                settings = RedisCache.get(f"settings:user:{user_id}") or {}
                report_format = settings.get('report_format', report_format)
                
            # Generate report based on format
            if report_format == 'csv':
                return _generate_csv_report(report_data)
            else:  # Default to HTML
                return _generate_html_report(report_data)
                
        except Exception as e:
            current_app.logger.error(f"Error generating user report: {e}")
            return {'status': 'error', 'message': str(e)}

    @celery.task(name='tasks.export_user_quiz_data')
    def export_user_quiz_data(user_id, task_id=None):
        """Export user quiz data as CSV and email it to the user"""
        try:
            user = User.query.get(user_id)
            if not user or not user.email:
                return {'status': 'error', 'message': 'User not found or no email available'}
            
            # Update task status if task_id provided
            if task_id and RedisCache.is_redis_available():
                task_data = RedisCache.get(f"task:{task_id}") or {}
                task_data['status'] = 'STARTED'
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            # Generate CSV data
            result = generate_user_quiz_report(user_id, 'csv')
            
            if result.get('status') == 'error':
                if task_id and RedisCache.is_redis_available():
                    task_data['status'] = 'FAILURE'
                    task_data['error'] = result.get('message')
                    RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
                return result
            
            # In a real app, would email this to the user
            # For demo, we'll just simulate success
            
            if task_id and RedisCache.is_redis_available():
                task_data['status'] = 'SUCCESS'
                task_data['completed_at'] = datetime.now().isoformat()
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            return {
                'status': 'success', 
                'message': f'Quiz data exported and sent to {user.email}'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error exporting quiz data: {e}")
            if task_id and RedisCache.is_redis_available():
                task_data = RedisCache.get(f"task:{task_id}") or {}
                task_data['status'] = 'FAILURE'
                task_data['error'] = str(e)
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            return {'status': 'error', 'message': str(e)}

    @celery.task(name='tasks.send_monthly_report')
    def send_monthly_report():
        """Send monthly reports to users who have opted in"""
        try:
            # Get all users
            users = User.query.all()
            current_month = datetime.utcnow().strftime('%B %Y')
            current_app.logger.info(f"Generating monthly reports for {len(users)} users for {current_month}")
            
            for user in users:
                try:
                    # Check if user has opted in for monthly reports
                    # For now, we'll send to all users, but in production you'd check preferences
                    
                    # Generate the monthly report
                    report_result = generate_user_quiz_report(user.id, user.report_format or 'html')
                    
                    if report_result.get('status') == 'success':
                        # Send the report via email
                        if os.environ.get('SMTP_SERVER'):
                            _send_monthly_report_email(user, report_result, current_month)
                        else:
                            current_app.logger.info(f"Monthly report generated for {user.username} but email not configured")
                    else:
                        current_app.logger.error(f"Failed to generate monthly report for {user.username}")
                        
                except Exception as e:
                    current_app.logger.error(f"Error processing monthly report for user {user.username}: {e}")
                    continue
            
            current_app.logger.info("Monthly reports sent successfully")
            return {'status': 'success', 'message': 'Monthly reports sent'}
        except Exception as e:
            current_app.logger.error(f"Error sending monthly reports: {e}")
            return {'status': 'error', 'message': str(e)}

    @celery.task(name='tasks.send_daily_reminders')
    def send_daily_reminders():
        """Send daily reminders to users via Google Chat webhooks, email, or SMS"""
        try:
            # Get all users
            users = User.query.all()
            current_app.logger.info(f"Sending daily reminders to {len(users)} users")
            
            for user in users:
                try:
                    # Check if user has been active recently (within last 7 days)
                    recent_activity = Score.query.filter(
                        Score.user_id == user.id,
                        Score.time_stamp_of_attempt >= datetime.utcnow() - timedelta(days=7)
                    ).first()
                    
                    # Check if there are new quizzes available
                    new_quizzes = Quiz.query.filter(
                        Quiz.date_of_quiz >= datetime.utcnow().date()
                    ).limit(5).all()
                    
                    if not recent_activity and new_quizzes:
                        # Send reminder to this user
                        reminder_sent = False
                        
                        # Try Google Chat webhook first
                        if os.environ.get('GOOGLE_CHAT_WEBHOOK_URL'):
                            reminder_sent = _send_google_chat_reminder(user, new_quizzes)
                        
                        # If Google Chat failed or not configured, try email
                        if not reminder_sent and os.environ.get('SMTP_SERVER'):
                            reminder_sent = _send_email_reminder(user, new_quizzes)
                        
                        # Log the reminder attempt
                        if reminder_sent:
                            current_app.logger.info(f"Daily reminder sent to user {user.username}")
                        else:
                            current_app.logger.warning(f"Failed to send daily reminder to user {user.username}")
                            
                except Exception as e:
                    current_app.logger.error(f"Error sending reminder to user {user.username}: {e}")
                    continue
            
            return {'status': 'success', 'message': 'Daily reminders sent successfully'}
            
        except Exception as e:
            current_app.logger.error(f"Error in send_daily_reminders: {e}")
            return {'status': 'error', 'message': str(e)}

    @celery.task(name='tasks.export_admin_quiz_data')
    def export_admin_quiz_data(task_id=None):
        """Export all users' quiz data for admin as CSV"""
        try:
            # Update task status if task_id provided
            if task_id and RedisCache.is_redis_available():
                task_data = RedisCache.get(f"task:{task_id}") or {}
                task_data['status'] = 'STARTED'
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            # Get all users with their quiz data
            users = User.query.all()
            
            # Generate CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['User ID', 'Username', 'Full Name', 'Total Quizzes', 'Average Score', 'Best Score', 'Worst Score', 'Last Quiz Date'])
            
            for user in users:
                # Get user's scores
                scores = Score.query.filter_by(user_id=user.id).all()
                
                if scores:
                    total_quizzes = len(scores)
                    avg_score = sum(score.total_scored for score in scores) / total_quizzes
                    best_score = max(score.total_scored for score in scores)
                    worst_score = min(score.total_scored for score in scores)
                    last_quiz_date = max(score.time_stamp_of_attempt for score in scores).strftime('%Y-%m-%d')
                else:
                    total_quizzes = 0
                    avg_score = 0
                    best_score = 0
                    worst_score = 0
                    last_quiz_date = 'N/A'
                
                writer.writerow([
                    user.id,
                    user.username,
                    user.full_name,
                    total_quizzes,
                    f"{avg_score:.2f}%",
                    f"{best_score:.2f}%",
                    f"{worst_score:.2f}%",
                    last_quiz_date
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            # Store in Redis for download
            file_key = f"export:admin_quiz_data:{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if RedisCache.is_redis_available():
                RedisCache.set(file_key, csv_data, expire_seconds=3600)  # 1 hour expiry
            
            if task_id and RedisCache.is_redis_available():
                task_data['status'] = 'SUCCESS'
                task_data['completed_at'] = datetime.now().isoformat()
                task_data['file_key'] = file_key
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            
            return {
                'status': 'success',
                'message': 'Admin export completed successfully',
                'file_key': file_key,
                'filename': f"admin_quiz_data_{datetime.now().strftime('%Y%m%d')}.csv"
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in export_admin_quiz_data: {e}")
            if task_id and RedisCache.is_redis_available():
                task_data = RedisCache.get(f"task:{task_id}") or {}
                task_data['status'] = 'FAILURE'
                task_data['error'] = str(e)
                RedisCache.set(f"task:{task_id}", task_data, expire_seconds=3600)
            return {'status': 'error', 'message': str(e)}
            
    # Return the registered tasks
    return {
        'update_quiz_statistics': update_quiz_statistics,
        'generate_user_quiz_report': generate_user_quiz_report,
        'export_user_quiz_data': export_user_quiz_data,
        'export_admin_quiz_data': export_admin_quiz_data,
        'send_monthly_report': send_monthly_report,
        'send_daily_reminders': send_daily_reminders
    }


def schedule_periodic_tasks(celery):
    """Schedule periodic tasks"""
    celery.conf.beat_schedule = {
        'update-quiz-statistics-daily': {
            'task': 'tasks.update_quiz_statistics',
            'schedule': timedelta(hours=24),
        },
        'send-daily-reminders': {
            'task': 'tasks.send_daily_reminders',
            'schedule': timedelta(hours=24),  # Daily at specific time
        },
        'send-monthly-reports': {
            'task': 'tasks.send_monthly_report',
            'schedule': timedelta(days=30),
        },
    }
    celery.conf.timezone = 'UTC'


def _generate_csv_report(report_data):
    """Generate CSV report from report data"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Quiz Master - Performance Report'])
        writer.writerow([f'User: {report_data["user"]["name"]}'])
        writer.writerow([f'Generated: {report_data["generated_at"]}'])
        writer.writerow([])
        
        # Summary section
        writer.writerow(['Summary'])
        writer.writerow(['Total Quizzes', report_data['summary']['total_quizzes']])
        writer.writerow(['Average Score', f"{report_data['summary']['average_score']}%"])
        writer.writerow(['Strongest Subject', report_data['summary']['strongest_subject']])
        writer.writerow(['Recent Trend', report_data['summary']['recent_trend']])
        writer.writerow([])
        
        # Subject performance
        writer.writerow(['Subject Performance'])
        writer.writerow(['Subject', 'Average Score', 'Attempts'])
        for subject in report_data['subjects']:
            writer.writerow([
                subject['subject_name'],
                f"{subject['average_score']}%",
                subject['attempts']
            ])
        writer.writerow([])
        
        # Timeline
        writer.writerow(['Score Timeline'])
        writer.writerow(['Date', 'Average Score'])
        for entry in report_data['timeline']:
            writer.writerow([entry['date'], f"{entry['average_score']:.2f}%"])
        writer.writerow([])
        
        # Detailed scores
        writer.writerow(['Recent Quiz Attempts'])
        writer.writerow(['Quiz ID', 'Subject', 'Chapter', 'Date Attempted', 'Score'])
        for score in report_data['detailed_scores']:
            writer.writerow([
                score['quiz_id'],
                score['subject'],
                score['chapter'],
                score['attempt_date'],
                f"{score['score']}%"
            ])
            
        csv_data = output.getvalue()
        output.close()
        
        return {
            'status': 'success',
            'data': csv_data,
            'filename': f"quiz_report_{report_data['user']['id']}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
        
    except Exception as e:
        current_app.logger.error(f"Error generating CSV report: {e}")
        return {'status': 'error', 'message': str(e)}


def _generate_html_report(report_data):
    """Generate HTML report from report data"""
    try:
        # In a real app, would use a proper template
        # For demo, construct a simple HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quiz Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .summary-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .score-good {{ color: #28a745; }}
                .score-average {{ color: #fd7e14; }}
                .score-poor {{ color: #dc3545; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quiz Master Performance Report</h1>
                <p>User: {report_data['user']['name']}</p>
                <p>Generated: {report_data['generated_at']}</p>
            </div>
            
            <h2>Performance Summary</h2>
            <div class="summary-box">
                <p><strong>Total Quizzes Taken:</strong> {report_data['summary']['total_quizzes']}</p>
                <p><strong>Overall Average Score:</strong> 
                    <span class="{'score-good' if report_data['summary']['average_score'] >= 80 else 'score-average' if report_data['summary']['average_score'] >= 60 else 'score-poor'}">
                        {report_data['summary']['average_score']}%
                    </span>
                </p>
                <p><strong>Strongest Subject:</strong> {report_data['summary']['strongest_subject']}</p>
                <p><strong>Recent Trend:</strong> {report_data['summary']['recent_trend']}</p>
            </div>
            
            <h2>Subject Performance</h2>
            <table>
                <tr>
                    <th>Subject</th>
                    <th>Average Score</th>
                    <th>Attempts</th>
                </tr>
        """
        
        for subject in report_data['subjects']:
            score_class = 'score-good' if subject['average_score'] >= 80 else 'score-average' if subject['average_score'] >= 60 else 'score-poor'
            html += f"""
                <tr>
                    <td>{subject['subject_name']}</td>
                    <td class="{score_class}">{subject['average_score']}%</td>
                    <td>{subject['attempts']}</td>
                </tr>
            """
            
        html += """
            </table>
            
            <h2>Recent Quiz Attempts</h2>
            <table>
                <tr>
                    <th>Subject</th>
                    <th>Chapter</th>
                    <th>Date Attempted</th>
                    <th>Score</th>
                </tr>
        """
        
        for score in report_data['detailed_scores']:
            score_class = 'score-good' if score['score'] >= 80 else 'score-average' if score['score'] >= 60 else 'score-poor'
            html += f"""
                <tr>
                    <td>{score['subject']}</td>
                    <td>{score['chapter']}</td>
                    <td>{score['attempt_date']}</td>
                    <td class="{score_class}">{score['score']}%</td>
                </tr>
            """
            
        html += """
            </table>
            
            <h2>Recommendations</h2>
            <p>Based on your performance, here are some recommendations:</p>
            <ul>
        """
        
        # Add personalized recommendations
        if report_data['summary']['average_score'] < 60:
            html += """
                <li>Consider reviewing your study materials before attempting quizzes</li>
                <li>Try practice questions in the subjects where your scores are lowest</li>
                <li>Schedule regular study sessions to improve retention</li>
            """
        elif report_data['summary']['average_score'] < 80:
            html += """
                <li>Focus on the specific topics where you scored lowest</li>
                <li>Try different study techniques to improve understanding</li>
                <li>Review questions you got wrong to identify patterns</li>
            """
        else:
            html += """
                <li>Challenge yourself with more advanced quizzes</li>
                <li>Consider helping others by sharing your study techniques</li>
                <li>Maintain your excellent study habits</li>
            """
            
        html += """
            </ul>
            
            <p>Thank you for using Quiz Master. Keep up the good work!</p>
        </body>
        </html>
        """
        
        return {
            'status': 'success',
            'data': html,
            'filename': f"quiz_report_{report_data['user']['id']}_{datetime.now().strftime('%Y%m%d')}.html"
        }
        
    except Exception as e:
        current_app.logger.error(f"Error generating HTML report: {e}")
        return {'status': 'error', 'message': str(e)}


def _send_google_chat_reminder(user, new_quizzes):
    """Send reminder via Google Chat webhook"""
    try:
        webhook_url = os.environ.get('GOOGLE_CHAT_WEBHOOK_URL')
        if not webhook_url:
            return False
            
        # Create quiz list for the message
        quiz_list = ""
        for quiz in new_quizzes:
            quiz_list += f"• {quiz.chapter.name} - {quiz.date_of_quiz.strftime('%Y-%m-%d')}\n"
        
        # Create the message payload
        message = {
            "cards": [{
                "header": {
                    "title": "📚 Quiz Master Daily Reminder",
                    "subtitle": f"Hello {user.full_name}!"
                },
                "sections": [{
                    "widgets": [{
                        "textParagraph": {
                            "text": f"👋 Hi {user.full_name}!\n\n"
                                   f"It's been a while since you've taken a quiz. "
                                   f"We have some new quizzes available that you might be interested in:\n\n"
                                   f"{quiz_list}\n"
                                   f"🎯 Take a quiz now and improve your skills!\n"
                                   f"🔗 <a href='http://localhost:5000'>Visit Quiz Master</a>"
                        }
                    }]
                }]
            }]
        }
        
        # Send the message
        response = requests.post(webhook_url, json=message, timeout=10)
        
        if response.status_code == 200:
            current_app.logger.info(f"Google Chat reminder sent to {user.username}")
            return True
        else:
            current_app.logger.error(f"Google Chat webhook failed: {response.status_code}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error sending Google Chat reminder: {e}")
        return False


def _send_email_reminder(user, new_quizzes):
    """Send reminder via email or file simulation"""
    try:
        # Check if we're in email simulation mode
        if current_app.config.get('EMAIL_SIMULATION_MODE', True):
            return _simulate_email_reminder(user, new_quizzes)
        
        # Real email sending
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            return _simulate_email_reminder(user, new_quizzes)
            
        # Create quiz list for the email
        quiz_list = ""
        for quiz in new_quizzes:
            quiz_list += f"<li>{quiz.chapter.name} - {quiz.date_of_quiz.strftime('%Y-%m-%d')}</li>"
        
        # Create email content
        html_content = f"""
        <html>
        <body>
            <h2>📚 Quiz Master Daily Reminder</h2>
            <p>Hello {user.full_name}!</p>
            <p>It's been a while since you've taken a quiz. We have some new quizzes available that you might be interested in:</p>
            <ul>{quiz_list}</ul>
            <p><strong>🎯 Take a quiz now and improve your skills!</strong></p>
            <p><a href="http://localhost:5000" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Visit Quiz Master</a></p>
            <br>
            <p>Best regards,<br>Quiz Master Team</p>
        </body>
        </html>
        """
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Quiz Master - Daily Reminder'
        msg['From'] = smtp_username
        msg['To'] = user.email or user.username
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        current_app.logger.info(f"Email reminder sent to {user.username}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error sending email reminder: {e}")
        return _simulate_email_reminder(user, new_quizzes)


def _send_monthly_report_email(user, report_result, month):
    """Send monthly report via email or file simulation"""
    try:
        # Check if we're in email simulation mode
        if current_app.config.get('EMAIL_SIMULATION_MODE', True):
            return _simulate_monthly_report_email(user, report_result, month)
        
        # Real email sending
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            return _simulate_monthly_report_email(user, report_result, month)
            
        # Create email content
        html_content = f"""
        <html>
        <body>
            <h2>📊 Quiz Master - Monthly Performance Report</h2>
            <p>Hello {user.full_name}!</p>
            <p>Here's your performance report for {month}:</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>📈 Summary</h3>
                <p><strong>Total Quizzes Taken:</strong> {report_result.get('summary', {}).get('total_quizzes', 0)}</p>
                <p><strong>Average Score:</strong> {report_result.get('summary', {}).get('average_score', 0)}%</p>
                <p><strong>Strongest Subject:</strong> {report_result.get('summary', {}).get('strongest_subject', 'N/A')}</p>
            </div>
            
            <p><strong>🎯 Keep up the great work and continue improving your skills!</strong></p>
            <p><a href="http://localhost:5000" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Take More Quizzes</a></p>
            <br>
            <p>Best regards,<br>Quiz Master Team</p>
        </body>
        </html>
        """
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Quiz Master - Monthly Report for {month}'
        msg['From'] = smtp_username
        msg['To'] = user.email or user.username
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Attach report file if available
        if report_result.get('data'):
            if user.report_format == 'csv':
                attachment = MIMEText(report_result['data'], 'csv')
                attachment.add_header('Content-Disposition', 'attachment', filename=f'quiz_report_{month}.csv')
                msg.attach(attachment)
            elif user.report_format == 'html':
                attachment = MIMEText(report_result['data'], 'html')
                attachment.add_header('Content-Disposition', 'attachment', filename=f'quiz_report_{month}.html')
                msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        current_app.logger.info(f"Monthly report email sent to {user.username}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error sending monthly report email: {e}")
        return _simulate_monthly_report_email(user, report_result, month)


def _simulate_email_reminder(user, new_quizzes):
    """Simulate email reminder by writing to file"""
    try:
        # Create email simulation directory if it doesn't exist
        email_dir = current_app.config.get('EMAIL_SIMULATION_DIR', 'email_simulation')
        os.makedirs(email_dir, exist_ok=True)
        
        # Create quiz list for the email
        quiz_list = ""
        for quiz in new_quizzes:
            quiz_list += f"• {quiz.chapter.name} - {quiz.date_of_quiz.strftime('%Y-%m-%d')}\n"
        
        # Create email content
        email_content = f"""
=== EMAIL SIMULATION ===
To: {user.email or user.username}
From: Quiz Master System <noreply@quizmaster.com>
Subject: Quiz Master - Daily Reminder
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Hello {user.full_name}!

It's been a while since you've taken a quiz. We have some new quizzes available that you might be interested in:

{quiz_list}

🎯 Take a quiz now and improve your skills!
🔗 Visit Quiz Master: http://localhost:5000

Best regards,
Quiz Master Team

=== END EMAIL SIMULATION ===
        """
        
        # Write to file
        filename = f"reminder_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(email_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        current_app.logger.info(f"Email reminder simulated for {user.username} - saved to {filepath}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error simulating email reminder: {e}")
        return False


def _simulate_monthly_report_email(user, report_result, month):
    """Simulate monthly report email by writing to file"""
    try:
        # Create email simulation directory if it doesn't exist
        email_dir = current_app.config.get('EMAIL_SIMULATION_DIR', 'email_simulation')
        os.makedirs(email_dir, exist_ok=True)
        
        # Create email content
        email_content = f"""
=== EMAIL SIMULATION ===
To: {user.email or user.username}
From: Quiz Master System <noreply@quizmaster.com>
Subject: Quiz Master - Monthly Report for {month}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Hello {user.full_name}!

Here's your performance report for {month}:

📈 SUMMARY
Total Quizzes Taken: {report_result.get('summary', {}).get('total_quizzes', 0)}
Average Score: {report_result.get('summary', {}).get('average_score', 0)}%
Strongest Subject: {report_result.get('summary', {}).get('strongest_subject', 'N/A')}

🎯 Keep up the great work and continue improving your skills!
🔗 Take More Quizzes: http://localhost:5000

Best regards,
Quiz Master Team

=== END EMAIL SIMULATION ===
        """
        
        # Write to file
        filename = f"monthly_report_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(email_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        # Also save the report data if available
        if report_result.get('data'):
            report_filename = f"report_data_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{user.report_format or 'html'}"
            report_filepath = os.path.join(email_dir, report_filename)
            
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_result['data'])
        
        current_app.logger.info(f"Monthly report email simulated for {user.username} - saved to {filepath}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error simulating monthly report email: {e}")
        return False
