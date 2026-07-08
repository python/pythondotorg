from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.pages.search_indexes import PageIndex


class PageSearchIndexTests(SimpleTestCase):
    def test_prepare_description_falls_back_to_plain_text_content(self):
        obj = SimpleNamespace(
            description="",
            content=SimpleNamespace(rendered="<p>Data &amp; AI role <script>alert(1)</script></p>"),
        )

        self.assertEqual(PageIndex().prepare_description(obj), "Data & AI role alert(1)")

    def test_prepare_description_keeps_existing_description(self):
        obj = SimpleNamespace(description="Kept &amp; raw", content=None)

        self.assertEqual(PageIndex().prepare_description(obj), "Kept &amp; raw")
