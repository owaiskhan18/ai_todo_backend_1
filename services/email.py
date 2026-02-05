# backend/services/email.py
from models.task import Task
from models.user import User

def send_reminder_email(user: User, task: Task):
    print(f"Sending reminder to {user.email} for task: {task.title}")
    # This is a placeholder. A real implementation would use a service like SendGrid.