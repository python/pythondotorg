import importlib
import inspect
import pprint

from django.apps import apps
from django.core.management import BaseCommand


class Command(BaseCommand):

    help = 'Create initial data by using factories.'

    def collect_initial_data_functions(self):
        functions = {}
        for app in apps.get_app_configs():
            try:
                factory_module = importlib.import_module('{}.factories'.format(app.name))
            except ImportError:
                continue
            else:
                for name, function in inspect.getmembers(factory_module, inspect.isfunction):
                    if name == 'initial_data':
                        functions[app.name] = function
                        break
        return functions

    def handle(self, **options):
        verbosity = options['verbosity']
        msg = (
            'Note that this command won\'t cleanup the database before '
            'creating new data.\n'
            'Type \'y\' or \'yes\' to continue, \'n\' or \'no\' to cancel: '
        )
        confirm = input(self.style.WARNING(msg))
        if confirm not in ('y', 'yes'):
            return
        functions = self.collect_initial_data_functions()
        for app_name, function in functions.items():
            if verbosity > 0:
                self.stdout.write('Creating initial data for {!r}... '.format(app_name), ending='')
            try:
                result = function()
            except Exception as exc:
                self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
                continue
            else:
                if verbosity > 0:
                    self.stdout.write(self.style.SUCCESS('DONE'))
                if verbosity >= 2:
                    pprint.pprint(result)
