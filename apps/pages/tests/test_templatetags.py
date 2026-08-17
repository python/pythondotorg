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

    def test_h1_h3_h4_also_processed(self):
        """h1, h3, and h4 headings are also processed."""
        for tag in ("h1", "h3", "h4"):
            html = f"<{tag}>Section Title</{tag}>"
            result = add_heading_anchors(html)
            self.assertIn('id="section-title"', result)
            self.assertIn('href="#section-title"', result)

    def test_h5_is_not_changed(self):
        """h5 headings are left untouched."""
        html = "<h5>Title</h5>"
        result = add_heading_anchors(html)
        self.assertNotIn("id=", result)
        self.assertNotIn("href=", result)

    def test_duplicate_headings_get_unique_ids(self):
        """Duplicate heading text produces unique, numbered ids."""
        html = "<h2>Board Resolution</h2><h2>Board Resolution</h2>"
        result = add_heading_anchors(html)
        self.assertIn('id="board-resolution"', result)
        self.assertIn('id="board-resolution-2"', result)

    def test_heading_with_existing_id_gets_pilcrow_link(self):
        """A heading with an existing id (e.g. from RST/docutils) gets a pilcrow
        link using that id, without the id being changed or duplicated."""
        html = '<h2 id="custom-id">My Section</h2>'
        result = str(add_heading_anchors(html))
        # Original id is preserved and not duplicated.
        self.assertIn('id="custom-id"', result)
        self.assertEqual(result.count('id="'), 1)
        # Pilcrow link is injected using the existing id.
        self.assertIn('href="#custom-id"', result)
        self.assertIn("headerlink", result)

    def test_rst_generated_headings_get_pilcrow_links(self):
        """RST/docutils headings that already carry ids get pilcrow links added."""
        html = (
            '<h2 id="board-resolutions">Board Resolutions</h2>'
            '<h3 id="resolution-1-budget">Resolution 1: Budget</h3>'
        )
        result = str(add_heading_anchors(html))
        self.assertIn('href="#board-resolutions"', result)
        self.assertIn('href="#resolution-1-budget"', result)
        self.assertEqual(result.count("headerlink"), 2)

    def test_filter_is_idempotent(self):
        """Running the filter twice does not add duplicate pilcrow links."""
        html = "<h2>Section</h2>"
        once = str(add_heading_anchors(html))
        twice = str(add_heading_anchors(once))
        self.assertEqual(once, twice)

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
        self.assertIn("¶</a></h2>", result)
