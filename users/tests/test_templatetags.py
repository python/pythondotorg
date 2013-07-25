from pydotorg.tests.test_classes import TemplateTestCase


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
