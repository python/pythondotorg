from django.db import transaction

from sponsors import notifications
from sponsors.models import Sponsorship, Contract, SponsorContact, SponsorEmailNotificationTemplate, SponsorshipBenefit, \
    SponsorshipPackage
from sponsors.contracts import render_contract_to_pdf_file, render_contract_to_docx_file


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
        renewal = kwargs.get("renewal", False)
        if package:
            sponsorship.package = package
            sponsorship.level_name = package.name
        if fee:
            sponsorship.sponsorship_fee = fee
        if renewal:
            sponsorship.renewal = True

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


class ExecuteExistingContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.ExecutedExistingContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]
    force_execute = True

    def execute(self, contract, contract_file, **kwargs):
        contract.signed_document = contract_file
        contract.execute(force=self.force_execute)
        overlapping_sponsorship = Sponsorship.objects.filter(
            sponsor=contract.sponsorship.sponsor,
        ).exclude(
            id=contract.sponsorship.id
        ).enabled().active_on_date(contract.sponsorship.start_date)
        overlapping_sponsorship.update(overlapped_by=contract.sponsorship)
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class ExecuteContractUseCase(ExecuteExistingContractUseCase):
    notifications = [
        notifications.ExecutedContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]
    force_execute = False


class NullifyContractUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.NullifiedContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]

    def execute(self, contract, **kwargs):
        contract.nullify()
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class SendSponsorshipNotificationUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.SendSponsorNotificationLogger(),
    ]

    def execute(self, notification: SponsorEmailNotificationTemplate, sponsorships, contact_types, **kwargs):
        msg_kwargs = {
            "to_primary": SponsorContact.PRIMARY_CONTACT in contact_types,
            "to_administrative": SponsorContact.ADMINISTRATIVE_CONTACT in contact_types,
            "to_accounting": SponsorContact.ACCOUTING_CONTACT in contact_types,
            "to_manager": SponsorContact.MANAGER_CONTACT in contact_types,
        }

        for sponsorship in sponsorships:
            email = notification.get_email_message(sponsorship, **msg_kwargs)
            if not email:
                continue
            email.send()

            self.notify(
                notification=notification,
                sponsorship=sponsorship,
                contact_types=contact_types,
                request=kwargs.get("request"),
            )


class CloneSponsorshipYearUseCase(BaseUseCaseWithNotifications):
    notifications = [
        notifications.ClonedResourcesLogger(),
    ]

    @transaction.atomic
    def execute(self, clone_from_year, target_year, **kwargs):
        created_resources = []
        with transaction.atomic():
            source_packages = SponsorshipPackage.objects.from_year(clone_from_year)
            for package in source_packages:
                resource, created = package.clone(target_year)
                if created:
                    created_resources.append(resource)

        with transaction.atomic():
            source_benefits = SponsorshipBenefit.objects.from_year(clone_from_year)
            for benefit in source_benefits:
                resource, created = benefit.clone(target_year)
                if created:
                    created_resources.append(resource)

        with transaction.atomic():
            for resource in created_resources:
                self.notify(
                    request=kwargs.get("request"),
                    resource=resource,
                    from_year=clone_from_year,
                )

        return created_resources
