import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sl.settings')

app = Celery('sl')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
