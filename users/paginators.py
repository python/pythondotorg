from django.core.paginator import Paginator


class UserPaginator(Paginator):

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self._current_page = 1
        self._page_range_size = 10

    def page(self, number):
        page = super().page(number)
        self._current_page = number
        return page

    @property
    def page_range(self):
        if self.num_pages <= self._page_range_size:
            return super().page_range
        return list(range(
            self._current_page,
            min(self._current_page + self._page_range_size + 1, self.num_pages + 1)
        ))
