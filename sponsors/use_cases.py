"""Use case classes orchestrating sponsorship business logic with notifications."""

from django.db import transaction

from sponsors import notifications
from sponsors.contracts import render_contract_to_docx_file, render_contract_to_pdf_file
from sponsors.models import (
    Contract,
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipPackage,
)


class BaseUseCaseWithNotifications:
    """Base class providing notification dispatch for use case implementations."""

    notifications = []

    def __init__(self, notifications):
        """Initialize with a list of notification handlers."""
        self.notifications = notifications

    def notify(self, **kwargs):
        """Send all registered notifications with the given keyword arguments."""
        for notification in self.notifications:
            notification.notify(**kwargs)

    @classmethod
    def build(cls):
        """Construct the use case with its default notification list."""
        return cls(cls.notifications)


class CreateSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    """Create a new sponsorship application and notify stakeholders."""

    notifications = [
        notifications.AppliedSponsorshipNotificationToPSF(),
        notifications.AppliedSponsorshipNotificationToSponsors(),
    ]

    def execute(self, user, sponsor, benefits, package=None, request=None):
        """Create the sponsorship and send application notifications."""
        sponsorship = Sponsorship.new(sponsor, benefits, package, submited_by=user)
        self.notify(sponsorship=sponsorship, request=request)
        return sponsorship


class RejectSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    """Reject a sponsorship application and notify stakeholders."""

    notifications = [
        notifications.RejectedSponsorshipNotificationToPSF(),
        notifications.RejectedSponsorshipNotificationToSponsors(),
    ]

    def execute(self, sponsorship, request=None):
        """Reject the sponsorship and send rejection notifications."""
        sponsorship.reject()
        sponsorship.save()
        self.notify(request=request, sponsorship=sponsorship)
        return sponsorship


class ApproveSponsorshipApplicationUseCase(BaseUseCaseWithNotifications):
    """Approve a sponsorship application, create a contract, and log the approval."""

    notifications = [
        notifications.SponsorshipApprovalLogger(),
    ]

    def execute(self, sponsorship, start_date, end_date, **kwargs):
        """Approve the sponsorship, set dates and fees, and create a contract."""
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
    """Generate and send a finalized contract to the sponsor."""

    notifications = [
        notifications.ContractNotificationToPSF(),
        notifications.SentContractLogger(),
    ]

    def execute(self, contract, **kwargs):
        """Render the contract as PDF/DOCX, finalize it, and notify PSF."""
        pdf_file = render_contract_to_pdf_file(contract)
        docx_file = render_contract_to_docx_file(contract)
        contract.set_final_version(pdf_file, docx_file)
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class ExecuteExistingContractUseCase(BaseUseCaseWithNotifications):
    """Execute a contract with an already-signed document file."""

    notifications = [
        notifications.ExecutedExistingContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]
    force_execute = True

    def execute(self, contract, contract_file, **kwargs):
        """Attach the signed document, execute the contract, and handle overlaps."""
        contract.signed_document = contract_file
        contract.execute(force=self.force_execute)
        overlapping_sponsorship = (
            Sponsorship.objects.filter(
                sponsor=contract.sponsorship.sponsor,
            )
            .exclude(id=contract.sponsorship.id)
            .enabled()
            .active_on_date(contract.sponsorship.start_date)
        )
        overlapping_sponsorship.update(overlapped_by=contract.sponsorship)
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class ExecuteContractUseCase(ExecuteExistingContractUseCase):
    """Execute a contract that was previously sent for signature."""

    notifications = [
        notifications.ExecutedContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]
    force_execute = False


class NullifyContractUseCase(BaseUseCaseWithNotifications):
    """Nullify a contract and refresh the sponsorships cache."""

    notifications = [
        notifications.NullifiedContractLogger(),
        notifications.RefreshSponsorshipsCache(),
    ]

    def execute(self, contract, **kwargs):
        """Nullify the contract and send notifications."""
        contract.nullify()
        self.notify(
            request=kwargs.get("request"),
            contract=contract,
        )


class SendSponsorshipNotificationUseCase(BaseUseCaseWithNotifications):
    """Send custom email notifications to selected sponsorships."""

    notifications = [
        notifications.SendSponsorNotificationLogger(),
    ]

    def execute(self, notification: SponsorEmailNotificationTemplate, sponsorships, contact_types, **kwargs):
        """Send the notification email to each sponsorship's matching contacts."""
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
    """Clone sponsorship packages and benefits from one year to another."""

    notifications = [
        notifications.ClonedResourcesLogger(),
    ]

    @transaction.atomic
    def execute(self, clone_from_year, target_year, **kwargs):
        """Clone all packages and benefits from the source year to the target year."""
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
