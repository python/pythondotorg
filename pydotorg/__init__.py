"""Core package for the python.org Django project."""

from pydotorg.celery import app as celery_app

__all__ = ("celery_app",)
