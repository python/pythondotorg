from django.apps import AppConfig


class UsersAppConfig(AppConfig):

    name = 'app.users'
    verbose_name = 'Users'

    def ready(self):
        import app.users.listeners
