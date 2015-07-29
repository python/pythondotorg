import waffle

from django.http import Http404


class FlagMixin(object):
    """
    Mixin to turn on/off views by a django-waffle flag. Return 404 if the flag
    is not active for the user.
    """

    flag = None

    def get_flag(self):
        return self.flag

    def dispatch(self, request, *args, **kwargs):
        if waffle.flag_is_active(request, self.get_flag()):
            return super().dispatch(request, *args, **kwargs)
        else:
            raise Http404()
