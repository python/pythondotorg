from sponsors import notifications
from sponsors.models import Sponsorship, Contract
from sponsors.pdf import render_contract_to_pdf_file, render_contract_to_docx_file


class BaseUseCaseWithNotifications:
    notifications = []

    def __init__(self, notifications):
        self.notifications = notifications

    def notify(self, **kwargs):
        for notification in self.notifications:
            notification.notify(**kwargs)

    @classmethod
    def build(cls):
        return cls(cls.notifications)


class CreateSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.AppliedSponsorshipNotificationToPSF(),
        notifications.AppliedSponsorshipNotificationToSponsors(),
    ]

    def execute(self, user, sponsor, benefits, package=None, request=None):
        sponsorship = Sponsorship.new(sponsor, benefits, package, submited_by=user)
        self.notify(sponsorship=sponsorship, request=request)
        return sponsorship


class RejectSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.RejectedSponsorshipNotificationToPSF(),
        notifications.RejectedSponsorshipNotificationToSponsors(),
    ]

    def execute(self, sponsorship, request=None):
        sponsorship.reject()
        sponsorship.save()
        self.notify(request=request, sponsorship=sponsorship)
        return sponsorship


class ApproveSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.SponsorshipApprovalLogger(),
    ]

    def execute(self, sponsorship, start_date, end_date, **kwargs):
        sponsorship.approve(start_date, end_date)
        package = kwargs.get("package")
        fee = kwargs.get("sponsorship_fee")
        if package:
            sponsorship.package = package
            sponsorship.level_name = package.name
        if fee:
            sponsorship.sponsorship_fee = fee

        sponsorship.save()
        contract = Contract.new(sponsorship)

        self.notify(
            request=kwargs.get("request"),
            sponsorship=sponsorship,
            contract=contract,
        )

        return sponsorship


class SendContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.ContractNotificationToPSF(),
        # TODO: sponsor's notification will be enabled again once
        # the generate contract file gets approved by PSF Board.
        # After that, the line bellow can be uncommented to enable
        # the desired behavior.
        #notifications.ContractNotificationToSponsors(),
        notifications.SentContractLogger(),
    ]

    def execute(self, contract, **kwargs):
        pdf_file = render_contract_to_pdf_file(contract)
        docx_file = render_contract_to_docx_file(contract)
        contract.set_final_version(pdf_file, docx_file)
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class ExecuteContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.ExecutedContractLogger(),
    ]

    def execute(self, contract, **kwargs):
        contract.execute()
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class ExecuteExistingContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.ExecutedExistingContractLogger(),
    ]

    def execute(self, contract, contract_file, **kwargs):
        contract.signed_document = contract_file
        contract.execute(force=True)
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class NullifyContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.NullifiedContractLogger(),
    ]

    def execute(self, contract, **kwargs):
        contract.nullify()
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class SendSponsorshipNotificationUseCase(BaseUseCaseWithNotifications):
    def execute(self, notification, sponsorships, **kwargs):
        pass
