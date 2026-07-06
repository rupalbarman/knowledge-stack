from saq import Queue

from app.config import settings

queue = Queue.from_url(settings.redis_url)
