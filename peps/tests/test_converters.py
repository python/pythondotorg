import os
import filecmp
import shutil

from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import captured_stdout
from django.conf import settings

from peps.converters import get_pep0_page, get_pep_page, add_pep_image, pep_url

from . import FAKE_PEP_REPO


class PEPConverterTests(TestCase):

    def test_source_link(self):
        pep = get_pep_page(FAKE_PEP_REPO, '0525')
        self.assertEqual(pep.title, 'PEP 525 -- Asynchronous Generators')
        self.assertIn(
            'Source: <a href="https://github.com/python/peps/blob/master/'
            'pep-0525.txt">https://github.com/python/peps/blob/master/pep-0525.txt</a>',
            pep.content.rendered
        )

    def test_source_link_rst(self):
        pep = get_pep_page(FAKE_PEP_REPO, '0012')
        self.assertEqual(pep.title, 'PEP 12 -- Sample reStructuredText PEP Template')
        self.assertIn(
            'Source: <a href="https://github.com/python/peps/blob/master/'
            'pep-0012.rst">https://github.com/python/peps/blob/master/pep-0012.rst</a>',
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

    def test_add_image_update(self):
        """Test that image modifications are adopted. """
        pep = '3001'
        pep_img_name = 'pep-3001-1.png'
        pep_img_path_src = os.path.join(FAKE_PEP_REPO, pep_img_name)
        pep_img_path_src_backup = pep_img_path_src + ".backup"
        pep_img_path_dst = os.path.join(
                settings.MEDIA_ROOT, pep_url(pep), pep_img_name)

        # We need to remove a prior uploaded file to fix an inconsistency
        # between db and filesystem.
        # TODO: This should be dealt with in page.model or converters module
        if os.path.exists(pep_img_path_dst):
            os.remove(pep_img_path_dst)

        # Create a pep page and "upload" a file
        get_pep_page(FAKE_PEP_REPO, pep)
        image = add_pep_image(FAKE_PEP_REPO, pep, pep_img_name)

        # The source and destination files should be the same
        self.assertTrue(filecmp.cmp(pep_img_path_src, pep_img_path_dst))

        # Create a backup, modify the source file and "re-upload"
        shutil.copyfile(pep_img_path_src, pep_img_path_src_backup)
        with open(pep_img_path_src, "ab") as f:
            f.write(b"TEST")
        image = add_pep_image(FAKE_PEP_REPO, pep, pep_img_name)

        # Again, modified src and re-uploaded dst files should be the same
        self.assertTrue(filecmp.cmp(pep_img_path_src, pep_img_path_dst))

        # Restore source file
        shutil.move(pep_img_path_src_backup, pep_img_path_src)


    def test_html_do_not_prettify(self):
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

    def test_strip_html_and_body_tags(self):
        pep = get_pep_page(FAKE_PEP_REPO, '0525')
        self.assertNotIn('<html>', pep.content.rendered)
        self.assertNotIn('</html>', pep.content.rendered)
        self.assertNotIn('<body>', pep.content.rendered)
        self.assertNotIn('</body>', pep.content.rendered)
