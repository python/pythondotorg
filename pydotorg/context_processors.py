from django.conf import settings
from django.urls import resolve, Resolver404, reverse


def site_info(request):
    return {'SITE_INFO': settings.SITE_VARIABLES}


def url_name(request):
    try:
        match = resolve(request.path)
    except Resolver404:
        return {}
    else:
        namespace, url_name_ = match.namespace, match.url_name
        if namespace:
            url_name_ = f"{namespace}:{url_name_}"
        return {'URL_NAMESPACE': namespace, 'URL_NAME': url_name_}


def get_host_with_scheme(request):
    return {
        'GET_HOST_WITH_SCHEME': request.build_absolute_uri('/').rstrip('/'),
    }


def blog_url(request):
    return {
        'BLOG_URL': settings.PYTHON_BLOG_URL,
    }


def user_nav_bar_links(request):
    nav = {}
    if request.user.is_authenticated:
        user = request.user
        sponsorship_url = None
        if user.sponsorships.exists():
            sponsorship_url = reverse("users:user_sponsorships_dashboard")

        # if the section has a urls key, the section buttion will work as a drop-down menu
        # if the section has only a url key, the button will be a link instead
        nav = {
            "account": {
                "label": "Your Account",
                "urls": [
                    {"url": reverse("users:user_detail", args=[user.username]), "label": "View profile"},
                    {"url": reverse("users:user_profile_edit"), "label": "Edit profile"},
                    {"url": reverse("account_change_password"), "label": "Change password"},
                ],
            },
            "psf_membership": {
                "label": "Membership",
                "urls": [
                    {"url": reverse("users:user_nominations_view"), "label": "Nominations"},
                ],
            },
            "sponsorships": {
                "label": "Sponsorships Dashboard",
                "url": sponsorship_url
            }
        }

        if request.user.has_membership:
            nav["psf_membership"]['urls'].append({
                "url": reverse("users:user_membership_edit"),
                "label": "Edit PSF Basic membership"
            })
        else:
            nav["psf_membership"]['urls'].append({
                "url": reverse("users:user_membership_create"),
                "label": "Become a PSF Basic member"
            })

    return {"USER_NAV_BAR": nav}
