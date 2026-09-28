# blog/scheduler.py
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

logger = logging.getLogger(__name__)

_scheduler = None


def publish_due_posts():
    from .models import Blog, BlogStatus  # imported here to avoid app-loading issues

    due = Blog.objects.filter(status=BlogStatus.SCHEDULED, publish_at__lte=timezone.now())
    count = due.update(status=BlogStatus.PUBLISHED)
    if count:
        logger.info("Published %s scheduled post(s).", count)


def start():
    global _scheduler
    if _scheduler is not None:
        return  # already running — avoid double-start under the dev autoreloader

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        publish_due_posts,
        "interval",
        seconds=60,
        id="publish_due_posts",
        replace_existing=True,
        next_run_time=timezone.now(),  # also run once immediately on startup
    )
    _scheduler.start()
    logger.info("Scheduled-post publisher started (checks every 60s).")