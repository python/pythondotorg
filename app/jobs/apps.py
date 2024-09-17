from django.apps import AppConfig


class JobsAppConfig(AppConfig):

    name = 'app.jobs'
    verbose_name = 'Jobs Application'

    def ready(self):
        import app.jobs.listeners
