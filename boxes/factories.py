import json
import pathlib

import factory

from django.conf import settings

from .models import Box

from users.factories import UserFactory


class BoxFactory(factory.DjangoModelFactory):

    class Meta:
        model = Box
        django_get_or_create = ('label',)

    creator = factory.SubFactory(UserFactory)
    content = factory.Faker('sentence', nb_words=10)


def initial_data():
    boxes = []
    fixtures_dir = pathlib.Path(settings.FIXTURE_DIRS[0])
    boxes_json = fixtures_dir / 'boxes.json'
    with boxes_json.open() as f:
        data = json.loads(f.read())
    for d in data:
        fields = d['fields']
        box = BoxFactory(
            label=fields['label'],
            content_markup_type=fields['content_markup_type'],
            content=fields['content'],
        )
        boxes.append(box)
    return {
        'boxes': boxes,
    }
