"""
WSGI config for RID project.

Note: The primary entrypoint is ASGI (core.asgi). This WSGI file
is retained for compatibility with deployment tools that expect it.
For production, use Uvicorn with core.asgi:application.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()
