"""Cookie utilities for storing sponsorship benefit selections."""

import json

BENEFITS_COOKIE_NAME = "sponsorship_selected_benefits"


def get_sponsorship_selected_benefits(request):
    """Retrieve selected sponsorship benefits from the request cookie."""
    sponsorship_selected_benefits = request.COOKIES.get(BENEFITS_COOKIE_NAME)
    if sponsorship_selected_benefits:
        try:
            return json.loads(sponsorship_selected_benefits)
        except json.JSONDecodeError:
            pass
    return {}


def set_sponsorship_selected_benefits(response, data):
    """Store selected sponsorship benefits as a JSON cookie on the response."""
    max_age = 60 * 60 * 24  # one day
    response.set_cookie(BENEFITS_COOKIE_NAME, json.dumps(data), max_age=max_age)


def delete_sponsorship_selected_benefits(response):
    """Remove the sponsorship benefits cookie from the response."""
    response.delete_cookie(BENEFITS_COOKIE_NAME)
