"""Jinja2 template environment for Local Farm Map.

Django's Jinja2 backend does not run context processors, so the helpers
templates need — URL reversing, static files, CSRF token, flash messages —
are exposed here as request-taking globals (SRS 7.1).
"""

from django.conf import settings
from django.contrib.messages import get_messages
from django.urls import reverse
from django.templatetags.static import static


def flash_messages(request):
    return list(get_messages(request))


def environment(**options):
    from jinja2 import Environment

    # Note: csrf_input/csrf_token come from Django's Jinja2 backend itself
    # (injected into every render context) — templates use {{ csrf_input }}.
    env = Environment(**options)
    env.globals.update(
        url=reverse,
        static=static,
        debug=settings.DEBUG,
        flash_messages=flash_messages,
    )
    return env
