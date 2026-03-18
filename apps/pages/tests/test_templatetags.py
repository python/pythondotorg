"""Tests for apps/pages/templatetags/page_tags.py."""

from django.test import SimpleTestCase

from apps.pages.templatetags.page_tags import add_heading_anchors


class AddHeadingAnchorsFilterTests(SimpleTestCase):
    """Tests for the ``add_heading_anchors`` template filter."""

    def test_h2_gets_id_and_anchor_link(self):
        """An h2 heading receives an id attribute and a pilcrow anchor link."""
        html = "<h2>2023</h2>"
        result = add_heading_anchors(html)
        self.assertIn('id="2023"', result)
        self.assertIn('href="#2023"', result)
        self.assertIn("¶", result)

    def test_h3_and_h4_also_processed(self):
        """h3 and h4 headings are also processed."""
        for tag in ("h3", "h4"):
            html = f"<{tag}>Section Title</{tag}>"
            result = add_heading_anchors(html)
            self.assertIn('id="section-title"', result)
            self.assertIn('href="#section-title"', result)

    def test_h1_and_h5_are_not_changed(self):
        """h1 and h5 headings are left untouched."""
        for tag in ("h1", "h5"):
            html = f"<{tag}>Title</{tag}>"
            result = add_heading_anchors(html)
            self.assertNotIn("id=", result)
            self.assertNotIn("href=", result)

    def test_duplicate_headings_get_unique_ids(self):
        """Duplicate heading text produces unique, numbered ids."""
        html = "<h2>Board Resolution</h2><h2>Board Resolution</h2>"
        result = add_heading_anchors(html)
        self.assertIn('id="board-resolution"', result)
        self.assertIn('id="board-resolution-2"', result)

    def test_heading_with_existing_id_is_unchanged(self):
        """A heading that already has an id attribute is left as-is."""
        html = '<h2 id="custom-id">My Section</h2>'
        result = add_heading_anchors(html)
        self.assertIn('id="custom-id"', result)
        # No extra anchor link should be injected.
        self.assertNotIn("headerlink", result)

    def test_heading_with_nested_html_tags(self):
        """Plain text is extracted from headings that contain nested tags."""
        html = "<h2><em>Nested</em> Heading</h2>"
        result = add_heading_anchors(html)
        self.assertIn('id="nested-heading"', result)

    def test_non_heading_html_is_unchanged(self):
        """Non-heading elements are passed through unmodified."""
        html = "<p>Some paragraph</p><ul><li>Item</li></ul>"
        result = add_heading_anchors(html)
        self.assertEqual(str(result), html)

    def test_empty_string_returns_empty_string(self):
        """Passing an empty string returns an empty string."""
        self.assertEqual(str(add_heading_anchors("")), "")

    def test_heading_with_empty_text_is_unchanged(self):
        """A heading whose text slugifies to an empty string is left alone."""
        html = "<h2>  </h2>"
        result = add_heading_anchors(html)
        self.assertNotIn("id=", result)

    def test_anchor_link_is_inside_heading(self):
        """The pilcrow anchor link appears inside the heading element."""
        html = "<h2>Resolutions 2022</h2>"
        result = str(add_heading_anchors(html))
        # The closing </h2> must come after the anchor link.
        self.assertIn("¶</a></h2>", result)
