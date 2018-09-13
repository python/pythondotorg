from urllib.parse import urljoin

import factory
import requests

from users.factories import UserFactory

from .models import OS, Release, ReleaseFile


class OSFactory(factory.DjangoModelFactory):

    class Meta:
        model = OS
        django_get_or_create = ('slug',)

    creator = factory.SubFactory(UserFactory)


class ReleaseFactory(factory.DjangoModelFactory):

    class Meta:
        model = Release
        django_get_or_create = ('slug',)

    creator = factory.SubFactory(UserFactory)
    is_published = True


class ReleaseFileFactory(factory.DjangoModelFactory):

    class Meta:
        model = ReleaseFile
        django_get_or_create = ('slug',)

    creator = factory.SubFactory(UserFactory)
    release = factory.SubFactory(ReleaseFactory)
    os = factory.SubFactory(OSFactory)


class APISession(requests.Session):
    base_url = 'https://www.python.org/api/v2/'

    def request(self, method, url, **kwargs):
        url = urljoin(self.base_url, url)
        return super().request(method, url, **kwargs)


def _get_id(obj, key):
    """
    Get the ID of an object by extracting it from the resource uri.
    """
    return (obj.pop(key, '') or '').rstrip('/').rpartition('/')[-1]


def initial_data():
    """
    Create the data for the downloads section by importing
    it from the python.org API.
    """
    objects = {
        'oss': {},
        'releases': {},
        'release_files': {},
    }

    with APISession() as session:
        for key, resource_uri in [
            ('oss', 'downloads/os/'),
            ('releases', 'downloads/release/'),
            ('release_files', 'downloads/release_file/')
        ]:
            response = session.get(resource_uri)
            object_list = response.json()

            for obj in object_list:
                objects[key][_get_id(obj, 'resource_uri')] = obj

    # Create the list of operating systems
    objects['oss'] = {k: OSFactory.build(**obj) for k, obj in objects['oss'].items()}
    OS.objects.bulk_create(objects['oss'].values())

    # Create all the releases
    for key, obj in objects['releases'].items():
        obj.pop('release_page')  # Ignore release pages
        objects['releases'][key] = ReleaseFactory.build(**obj)
    Release.objects.bulk_create(objects['releases'].values())

    # Create all release files
    for key, obj in tuple(objects['release_files'].items()):
        release_id = _get_id(obj, 'release')
        try:
            release = objects['releases'][release_id]
        except KeyError:
            # Release files for draft releases are available through the API,
            # the releases are not.
            # https://github.com/python/pythondotorg/issues/1308
            objects['release_files'].pop(key)
        else:
            obj['release'] = release
            obj['os'] = objects['oss'][_get_id(obj, 'os')]
            objects['release_files'][key] = ReleaseFileFactory.build(**obj)
    ReleaseFile.objects.bulk_create(objects['release_files'].values())

    return {
        'oss': list(objects.pop('oss').values()),
        'releases': list(objects.pop('releases').values()),
        'release_files': list(objects.pop('release_files').values()),
    }
