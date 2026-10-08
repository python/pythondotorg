"""Site search result highlighter built on Haystack."""

from haystack.utils.highlighting import Highlighter as HaystackHighlighter


class Highlighter(HaystackHighlighter):
    """Haystack highlighter that finds the densest window in linear rather than quadratic time.

    Haystack compares every match offset with every later one, so a query of common
    letters against a long page keeps a worker busy past its timeout.
    """

    def find_window(self, highlight_locations):
        """Return the earliest ``max_length`` window containing the most matches."""
        words_found = sorted(offset for offsets in highlight_locations.values() for offset in offsets)

        if not words_found:
            return 0, self.max_length

        if len(words_found) == 1:
            return words_found[0], words_found[0] + self.max_length

        best_start, best_end = 0, self.max_length
        if words_found[0] > self.max_length:
            best_start, best_end = words_found[0], words_found[0] + self.max_length

        # Slide the window end forward as the start advances; a window only wins
        # if it holds at least two matches and strictly more than any earlier one.
        highest_density = 1
        end = 0
        for count, start in enumerate(words_found[:-1]):
            end = max(end, count + 1)
            while end < len(words_found) and words_found[end] - start < self.max_length:
                end += 1
            density = end - count
            if density > highest_density:
                best_start, best_end = start, start + self.max_length
                highest_density = density

        return best_start, best_end
