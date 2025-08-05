import celery.schedules
from celery.schedules import crontab
celery.conf.beat_schedule = {
    'daily-reminders': {
        'task': 'tasks.send_daily_reminders',
        'schedule': crontab(hour=19, minute=0),  # Every day at 7 PM
    },
    'monthly-reports': {
        'task': 'tasks.send_monthly_report',
        'schedule': crontab(day_of_month=1, hour=8, minute=0),  # 1st day of month at 8 AM
    },
}
