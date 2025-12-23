from celery import Celery
from config import settings
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建Celery应用
celery_app = Celery(
    'ai_mentor',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
    include=['tasks']
)

# 配置Celery
celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    worker_concurrency=4,
    task_default_queue='ai_mentor_queue',
    task_queues={
        'ai_mentor_queue': {
            'exchange': 'ai_mentor_queue',
            'exchange_type': 'direct',
            'routing_key': 'ai_mentor_queue'
        }
    },
    task_routes={
        'tasks.*': {'queue': 'ai_mentor_queue'}
    },
    beat_schedule={},
)

if __name__ == '__main__':
    celery_app.start()
