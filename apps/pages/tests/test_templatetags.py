from django.test import SimpleTestCase

from apps.pages.templatetags.pages import resolution_anchors


class ResolutionAnchorsTests(SimpleTestCase):
    def test_ids_from_vote_dates(self):
        """Each resolution is keyed by its vote date, numbered in page order when a date repeats."""
        html = (
            "<blockquote>A</blockquote>\n<p>Approved; 9-0-1, 2026-08-12</p>\n"
            "<blockquote>B</blockquote>\n<p>Approved; 9-0-0, 2026-08-12</p>\n"
            "<blockquote>C</blockquote>\n<p>Denied 3-4-0, December 2, 2014</p>\n"
            "<blockquote>D</blockquote>\n<p>Approved, 10-0-0 by IRC vote, 8 June 2015.</p>"
        )
        self.assertHTMLEqual(
            resolution_anchors(html),
            '<blockquote id="2026-08-12">A</blockquote><p>Approved; 9-0-1, <a href="#2026-08-12">2026-08-12</a></p>'
            '<blockquote id="2026-08-12-2">B</blockquote><p>Approved; 9-0-0, <a href="#2026-08-12-2">2026-08-12</a></p>'
            '<blockquote id="2014-12-02">C</blockquote><p>Denied 3-4-0, <a href="#2014-12-02">December 2, 2014</a></p>'
            '<blockquote id="2015-06-08">D</blockquote>'
            '<p>Approved, 10-0-0 by IRC vote, <a href="#2015-06-08">8 June 2015</a>.</p>',
        )

    def test_unmatched_content_unchanged(self):
        """Vote lines without a full date and dated paragraphs that aren't vote lines are left alone."""
        html = (
            "<blockquote>A</blockquote><p>Approved, 10-0-0, May 2010.</p>"
            "<blockquote>B</blockquote><p>Discussed on 2026-08-12</p>"
            "<p>Approved; 9-0-0, 2026-08-12</p>"
            "<blockquote>C</blockquote><p>Approved 5-0-0, Feb 30, 2014</p>"
        )
        self.assertHTMLEqual(resolution_anchors(html), html)
