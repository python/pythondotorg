from sponsors.models import Sponsorship
from sponsors import notifications


class CreateSponsorshipApplicationUseCase:
    def __init__(self, notifications):
        self.notifications = notifications

    def execute(self, user, sponsor, benefits, package=None):
        sponsorship = Sponsorship.new(sponsor, benefits, package)

        for notification in self.notifications:
            notification.notify(user=user, sponsorship=sponsorship)

        return sponsorship

    @classmethod
    def build(cls):
        uc_notifications = [
            notifications.AppliedSponsorshipNotificationToPSF(),
            notifications.AppliedSponsorshipNotificationToSponsors(),
        ]
        return cls(uc_notifications)
