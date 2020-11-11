from sponsors.models import Sponsorship


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
        notifications = []  # TODO: add notifications
        return cls(notifications)
