class SponsorWithExistingApplicationException(Exception):
    """
    Raised when user tries to create a new Sponsorship application
    for a Sponsor which already has applications pending to review
    """


class SponsorshipInvalidStatusException(Exception):
    """
    Raised when user tries to change the Sponsorship's status
    to a new one but from an invalid current status
    """
