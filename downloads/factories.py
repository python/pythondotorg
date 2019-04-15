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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                'Accept': 'application/json',
                'User-Agent': (
                    f'pythondotorg/create_initial_data'
                    f' ({requests.utils.default_user_agent()})'
                ),
            }
        )

    def request(self, method, url, **kwargs):
        url = urljoin(self.base_url, url)
        response = super().request(method, url, **kwargs)
        response.raise_for_status()
        return response


def _get_id(obj, key):
    """
    Get the ID of an object by extracting it from the resource_uri field.
    """
    resource_uri = obj.pop(key, '')
    if resource_uri:
        # i.e. /foo/1/ -> /foo/1 -> ('/foo', '/', '1') -> '1'
        return resource_uri.rstrip('/').rpartition('/')[-1]


def initial_data():
    """
    Create the data for the downloads section by importing
    it from the python.org API.
    """
    objects = {
        'oses': {},
        'releases': {},
        'release_files': {},
    }

    with APISession() as session:
        for key, resource_uri in [
            ('oses', 'downloads/os/'),
            ('releases', 'downloads/release/'),
            ('release_files', 'downloads/release_file/'),
        ]:
            response = session.get(resource_uri)
            object_list = response.json()

            for obj in object_list:
                objects[key][_get_id(obj, 'resource_uri')] = obj

    # Create the list of operating systems
    objects['oses'] = {k: OSFactory(**obj) for k, obj in objects['oses'].items()}

    # Create all the releases
    for key, obj in objects['releases'].items():
        # TODO: We are ignoring release pages for now.
        obj.pop('release_page')
        objects['releases'][key] = ReleaseFactory(**obj)

    # Create all release files.
    for key, obj in tuple(objects['release_files'].items()):
        release_id = _get_id(obj, 'release')
        try:
            release = objects['releases'][release_id]
        except KeyError:
            # Release files for draft releases are available through the API,
            # the releases are not. See #1308 for details.
            objects['release_files'].pop(key)
        else:
            obj['release'] = release
            obj['os'] = objects['oses'][_get_id(obj, 'os')]
            objects['release_files'][key] = ReleaseFileFactory(**obj)

    return {
        'oses': list(objects.pop('oses').values()),
        'releases': list(objects.pop('releases').values()),
        'release_files': list(objects.pop('release_files').values()),
    }
