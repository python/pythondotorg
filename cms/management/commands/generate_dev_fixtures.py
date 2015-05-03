import gzip

from collections import OrderedDict
from optparse import make_option

from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.core.management.commands.dumpdata import sort_dependencies

from django.core import serializers
from django.db import router, DEFAULT_DB_ALIAS


class Command(BaseCommand):
    """
    Generate fixtures necessary for local development of production database.

    NOTE: This should be run as a cron job on the production www.python.org
    infrastructure, it is not useful to run this in a local environment except
    for testing/debugging purposes of this command itself.
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--file',
            default='/tmp/dev-fixtures.json',
            dest='outputfile',
            help='Specifies the output file location of the fixtures.',
        ),
    )

    help = "Generate development fixtures for local development"

    def handle(self, **options):
        outputfile = options.get('outputfile')

        app_labels = [
            'auth',
            'users',
            'sitetree',
            'boxes',
            'pages',
            'companies',
            'jobs',
            'sponsors',
            'successstories',
            'events',
            'peps',
            'blogs',
            'downloads',
            'codesamples',
            'comments',
        ]

        # Get app label list for serialization
        app_list = OrderedDict()
        for label in app_labels:
            try:
                app_label, model_label = label.split('.')
                try:
                    app_config = apps.get_app_config(app_label)
                except LookupError:
                    raise CommandError("Unknown application: %s" % app_label)
                if app_config.models_module is None:
                    continue
                try:
                    model = app_config.get_model(model_label)
                except LookupError:
                    raise CommandError("Unknown model: %s.%s" % (app_label, model_label))

                app_list_value = app_list.setdefault(app_config, [])

                # We may have previously seen a "all-models" request for
                # this app (no model qualifier was given). In this case
                # there is no need adding specific models to the list.
                if app_list_value is not None:
                    if model not in app_list_value:
                        app_list_value.append(model)
            except ValueError:
                # This is just an app - no model qualifier
                app_label = label
                try:
                    app_config = apps.get_app_config(app_label)
                except LookupError:
                    raise CommandError("Unknown application: %s" % app_label)
                if app_config.models_module is None:
                    continue
                app_list[app_config] = None

        def get_objects():
            """
            Collate the objects for serialization, taken from dumpdata command
            and adjusted to sanitize User password hashes
            """
            # Collate the objects to be serialized.
            for model in sort_dependencies(app_list.items()):
                if not model._meta.proxy and router.allow_migrate(DEFAULT_DB_ALIAS, model):
                    objects = model._base_manager

                    queryset = objects.using(DEFAULT_DB_ALIAS).order_by(model._meta.pk.name)
                    for obj in queryset.iterator():

                        # Sanitize user objects
                        if model._meta.model_name == 'user':
                            obj.set_unusable_password()
                        yield obj

        # Create serializer
        data = serializers.serialize(
            format='json',
            queryset=get_objects(),
            indent=4,
            use_natural_foreign_keys=False,
            use_natural_primary_keys=False,
        )

        data = bytes(data, 'utf-8')
        with gzip.open(outputfile, 'wb') as out:
            out.write(data)
