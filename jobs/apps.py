from django.apps import AppConfig


class JobsAppConfig(AppConfig):

    name = 'jobs'
    verbose_name = 'Jobs Application'

    def ready(self):
        import jobs.listeners
