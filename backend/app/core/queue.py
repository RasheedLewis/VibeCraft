"""Queue management utilities."""

from functools import lru_cache

import redis
from rq import Queue

from app.core.config import get_settings


@lru_cache
def get_queue(queue_name: str | None = None, timeout: int | None = None) -> Queue:
    """
    Get an RQ queue instance.
    
    Args:
        queue_name: Optional queue name (defaults to settings.rq_worker_queue)
        timeout: Optional default timeout in seconds for jobs in this queue
    
    Returns:
        Queue instance
    """
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    queue_name = queue_name or settings.rq_worker_queue
    
    kwargs = {}
    if timeout:
        kwargs["default_timeout"] = timeout
    
    return Queue(queue_name, connection=connection, **kwargs)

