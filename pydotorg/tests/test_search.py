import random

from django.template import Context, Template
from django.test import SimpleTestCase
from haystack.utils.highlighting import Highlighter as HaystackHighlighter

from pydotorg.search import Highlighter


class HighlighterTests(SimpleTestCase):
    def test_find_window_matches_haystack(self):
        rng = random.Random(1234)  # noqa: S311 - not used for security, just test data
        for max_length in [5, 20, 200]:
            for _ in range(300):
                locations = {word: sorted(rng.sample(range(500), rng.randint(0, 15))) for word in ["py", "thon", "x"]}
                with self.subTest(max_length=max_length, locations=locations):
                    self.assertEqual(
                        Highlighter("q", max_length=max_length).find_window(locations),
                        HaystackHighlighter("q", max_length=max_length).find_window(locations),
                    )

    def test_highlight_many_matches(self):
        template = Template("{% load highlight %}{% highlight text with query max_length 500 %}")
        rendered = template.render(Context({"text": "asdfghjkl " * 20000, "query": "A S D F G H J K L"}))
        self.assertTrue(rendered.startswith('<span class="highlighted">a</span>'))
