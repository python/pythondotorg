class SponsorWithExistingApplicationException(Exception):
    """
    Raised when user tries to create a new Sponsorship application
    for a Sponsor which already has applications pending to review
    """
