class SponsorWithExistingApplicationException(Exception):
    """
    Raised when user tries to create a new Sponsorship application
    for a Sponsor which already has applications pending to review
    """


class InvalidStatusException(Exception):
    """
    Raised when user tries to change the Sponsorship's status
    to a new one but from an invalid current status
    """


class SponsorshipInvalidDateRangeException(Exception):
    """
    Raised when user tries to approve a sponsorship with a start date
    greater than the end date.
    """
