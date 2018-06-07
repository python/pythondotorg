import importlib
import inspect
import pprint

from django.apps import apps
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    help = 'Create initial data by using factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app-label',
            dest='app_label',
            help='Provide an app label to create app specific data (e.g. --app-label boxes)',
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            dest='do_flush',
            help='Remove existing data in the database before creating new data.',
        )

    def collect_initial_data_functions(self, app_label):
        functions = {}
        if app_label:
            try:
                app_list = [apps.get_app_config(app_label)]
            except LookupError:
                self.stdout.write(self.style.ERROR('The app label provided does not exist as an application.'))
                return
        else:
            app_list = apps.get_app_configs()
        for app in app_list:
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

    def output(self, app_name, verbosity, *, done=False, result=False):
        if verbosity > 0:
            if done:
                self.stdout.write(self.style.SUCCESS('DONE'))
            else:
                self.stdout.write('Creating initial data for {!r}... '.format(app_name), ending='')
        if verbosity >= 2 and result:
            pprint.pprint(result)

    def flush_handler(self, do_flush, verbosity):
        if do_flush:
            msg = (
                'You have provided the --flush argument, this will cleanup '
                'the database before creating new data.\n'
                'Type \'y\' or \'yes\' to continue, \'n\' or \'no\' to cancel: '
                )
        else:
            msg = (
                'Note that this command won\'t cleanup the database before '
                'creating new data.\n'
                'If you would like to cleanup the database before creating '
                'new data, call create_initial_data with --flush.\n'
                'Type \'y\' or \'yes\' to continue, \'n\' or \'no\' to cancel: '
            )
        confirm = input(self.style.WARNING(msg))
        if do_flush and confirm in ('y', 'yes'):
            try:
                call_command('flush', verbosity=verbosity, interactive=False)
            except Exception as exc:
                self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
        return confirm

    def handle(self, **options):
        verbosity = options['verbosity']
        app_label = options['app_label']
        do_flush = options['do_flush']

        confirm = self.flush_handler(do_flush, verbosity)
        if confirm not in ('y', 'yes'):
            return
        # Collect relevant functions for data generation.
        functions = self.collect_initial_data_functions(app_label)
        if not functions:
            return

        if not app_label:
            self.output('sitetree', verbosity)
            try:
                call_command('loaddata', 'sitetree_menus', '-v0')
            except Exception as exc:
                self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
            else:
                self.output('sitetree', verbosity, done=True)

        for app_name, function in functions.items():
            self.output(app_name, verbosity)
            try:
                result = function()
            except Exception as exc:
                self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
                continue
            else:
                self.output(app_name, verbosity, done=True, result=result)
