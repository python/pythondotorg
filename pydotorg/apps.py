from django.apps import AppConfig


class PyDotOrgConfig(AppConfig):
    name = "pydotorg"

    def ready(self):
        import pydotorg.signals  # noqa: F401
