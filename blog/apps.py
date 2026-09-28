import os
import sys

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        # RUN_MAIN guard: with `manage.py runserver`, Django starts the app
        # twice (parent watcher + reloaded child) — only start the
        # scheduler in the actual serving process.
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        from . import scheduler
        scheduler.start()