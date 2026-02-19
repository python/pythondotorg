"""Exceptions for the sponsors app."""


class SponsorWithExistingApplicationError(Exception):
    """Raise when creating a Sponsorship for a Sponsor with pending applications.

    Triggered when user tries to create a new Sponsorship application
    for a Sponsor which already has applications pending to review.
    """


class InvalidStatusError(Exception):
    """Raise when changing Sponsorship status from an invalid current status.

    Triggered when user tries to change the Sponsorship's status
    to a new one but from an invalid current status.
    """


class SponsorshipInvalidDateRangeError(Exception):
    """Raise when approving a sponsorship with an invalid date range.

    Triggered when user tries to approve a sponsorship with a start date
    greater than the end date.
    """
