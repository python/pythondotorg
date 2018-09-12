from pydotorg.tests.test_classes import TemplateTestCase

from ..factories import UserFactory


class UsersTagsTest(TemplateTestCase):

    def test_parse_location(self):
        user = UserFactory()
        template = "{% load users_tags %}{{ user|user_location }}"
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "")

        template = "{% load users_tags %}{{ user|user_location }}"
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "")
        template = "{% load users_tags %}{{ user|user_location|default:'Not Specified' }}"

        user = UserFactory(membership__city='Lawrence')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence")

        user = UserFactory(membership__city='Lawrence', membership__region='KS')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence, KS")

        user = UserFactory(membership__region='KS', membership__country='USA')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, 'KS USA')

        user = UserFactory(
            membership__city='Lawrence',
            membership__region='KS',
            membership__country='US',
        )
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence, KS US")

        user = UserFactory(membership__city='Paris', membership__country='France')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Paris, France")

        user = UserFactory(membership__country='France')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "France")
