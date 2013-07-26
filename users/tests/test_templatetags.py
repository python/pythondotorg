from pydotorg.tests.test_classes import TemplateTestCase

from ..factories import UserFactory, MembershipFactory


class UsersTagsTest(TemplateTestCase):
    def test_ifempty_regression(self):
        """
        This is just to make sure the `{% firstof %}` templatetag's behaviour
        stays the say as our deprecated `ifempty` filter
        """
        template = "{% firstof variable 'default' %}"
        ctx = {
            'variable': ''
        }
        rendered = self.render_string(template, ctx)
        self.assertEqual(rendered, 'default')

        ctx = {
            'variable': 'something'
        }
        rendered = self.render_string(template, ctx)
        self.assertEqual(rendered, 'something')

    def test_parse_location(self):
        user = UserFactory.create()
        template = "{% load users_tags %}{{ user|user_location }}"
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "")

        MembershipFactory.create(creator=user)
        template = "{% load users_tags %}{{ user|user_location }}"
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "")
        template = "{% load users_tags %}{{ user|user_location|default:'Not Specified' }}"

        user = UserFactory.create()
        MembershipFactory.create(creator=user, city='Lawrence')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence")

        user = UserFactory.create()
        MembershipFactory.create(creator=user, city='Lawrence', region='KS')
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence, KS")

        user = UserFactory.create()
        MembershipFactory.create(creator=user, city='Lawrence', region='KS', country="US")
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Lawrence, KS US")

        user = UserFactory.create()
        MembershipFactory.create(creator=user, city='Paris', country="France")
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "Paris, France")

        user = UserFactory.create()
        MembershipFactory.create(creator=user, country="France")
        rendered = self.render_string(template, {'user': user})
        self.assertEqual(rendered, "France")
