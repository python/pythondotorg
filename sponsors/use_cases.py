from sponsors.models import Sponsorship


class CreateSponsorshipApplicationUseCase:
    def execute(self, sponsor, benefits, package=None):
        return Sponsorship.new(sponsor, benefits, package)
