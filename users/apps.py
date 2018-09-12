from django.apps import AppConfig


class UsersAppConfig(AppConfig):

    name = 'users'
    verbose_name = 'Users'

    def ready(self):
        import users.listeners
