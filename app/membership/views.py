from django.views.generic import TemplateView

from app.pydotorg.mixins import FlagMixin

# NOTE: Many aspects of 'membership' such as adjusting a user profile, signup,
#       etc are handled in the users app


class Membership(FlagMixin, TemplateView):
    """ Main membership landing page """
    flag = 'psf_membership'
    template_name = 'membership.html'
