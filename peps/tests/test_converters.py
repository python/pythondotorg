from django.test import TestCase, override_settings
from django.test.utils import captured_stdout

from unittest.mock import Mock, patch

from peps.converters import (
    get_pep_page,
    add_pep_image,
    get_commit_history_info,
)

from . import FAKE_PEP_REPO


class PEPConverterTests(TestCase):

    @patch('peps.converters.get_commit_history_info')
    def test_source_link(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''
        pep = get_pep_page(FAKE_PEP_REPO, '0525')
        self.assertEqual(pep.title, 'PEP 525 -- Asynchronous Generators')
        self.assertIn(
            'Source: <a href="https://github.com/python/peps/blob/master/'
            'pep-0525.txt">https://github.com/python/peps/blob/master/pep-0525.txt</a>',
            pep.content.rendered
        )

    @patch('peps.converters.get_commit_history_info')
    def test_source_link_rst(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''
        pep = get_pep_page(FAKE_PEP_REPO, '0012')
        self.assertEqual(pep.title, 'PEP 12 -- Sample reStructuredText PEP Template')
        self.assertIn(
            '<div>Source: <a href="https://github.com/python/peps/blob/master/'
            'pep-0012.rst">https://github.com/python/peps/blob/master/pep-0012.rst</a></div>',
            pep.content.rendered
        )

    @patch('requests.get')
    def test_get_commit_history_info_with_data(self, mocked_gh_request):

        mocked_gh_request.return_value = Mock(ok=True)
        mocked_gh_request.return_value.json.return_value = [
            {
                "commit": {
                    "committer": {
                        "name": "miss-islington",
                        "date": "2020-02-19T04:06:01Z",
                    }
                }
            }
        ]

        info = get_commit_history_info('pep-0012.txt')
        self.assertEqual(
            info,
            '<div>Last modified: <a href="https://github.com/python/peps/commits/master/pep-0012.txt">2020-02-19T04:06:01Z</a></div>'
        )

    @patch('requests.get')
    def test_get_commit_history_info_no_data(self, mocked_gh_request):
        mocked_gh_request.return_value = Mock(ok=True)
        mocked_gh_request.return_value.json.return_value = []

        info = get_commit_history_info('pep-0012.txt')
        self.assertEqual(info, '')

    @patch('requests.get')
    def test_get_page_page_includes_last_modified(self, mocked_gh_request):
        mocked_gh_request.return_value = Mock(ok=True)
        mocked_gh_request.return_value.json.return_value = [
            {
                "commit": {
                    "committer": {
                        "name": "miss-islington",
                        "date": "2020-02-19T04:06:01Z",
                    }
                }
            }
        ]

        pep = get_pep_page(FAKE_PEP_REPO, '0012')
        self.assertIn(
            '<div>Last modified: <a href="https://github.com/python/peps/commits/master/pep-0012.rst">2020-02-19T04:06:01Z</a></div>',
            pep.content.rendered
        )

    def test_invalid_pep_number(self):
        with captured_stdout() as stdout:
            get_pep_page(FAKE_PEP_REPO, '9999999')
        self.assertRegex(
            stdout.getvalue(),
            r"PEP Path '(.*)9999999(.*)' does not exist, skipping"
        )

    def test_add_image_not_found(self):
        with captured_stdout() as stdout:
            add_pep_image(FAKE_PEP_REPO, '0525', '/path/that/does/not/exist')
        self.assertRegex(
            stdout.getvalue(),
            r"Image Path '(.*)/path/that/does/not/exist(.*)' does not exist, skipping"
        )

    @patch('peps.converters.get_commit_history_info')
    def test_html_do_not_prettify(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''

        pep = get_pep_page(FAKE_PEP_REPO, '3001')
        self.assertEqual(
            pep.title,
            'PEP 3001 -- Procedure for reviewing and improving standard library modules'
        )
        self.assertIn(
            '<tr class="field"><th class="field-name">Title:</th>'
            '<td class="field-body">Procedure for reviewing and improving '
            'standard library modules</td>\n</tr>',
            pep.content.rendered
        )

    @patch('peps.converters.get_commit_history_info')
    def test_strip_html_and_body_tags(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''

        pep = get_pep_page(FAKE_PEP_REPO, '0525')
        self.assertNotIn('<html>', pep.content.rendered)
        self.assertNotIn('</html>', pep.content.rendered)
        self.assertNotIn('<body>', pep.content.rendered)
        self.assertNotIn('</body>', pep.content.rendered)
