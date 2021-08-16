from django.db.models import Count
from ordered_model.models import OrderedModelManager
from django.db.models import Q, Subquery
from django.db.models.query import QuerySet
from django.utils import timezone

from .enums import PublisherChoices


class SponsorshipQuerySet(QuerySet):
    def in_progress(self):
        status = [self.model.APPLIED, self.model.APPROVED]
        return self.filter(status__in=status)

    def approved(self):
        return self.filter(status=self.model.APPROVED)

    def visible_to(self, user):
        contacts = user.sponsorcontact_set.values_list('sponsor_id', flat=True)
        status = [self.model.APPLIED, self.model.APPROVED, self.model.FINALIZED]
        return self.filter(
            Q(submited_by=user) | Q(sponsor_id__in=Subquery(contacts)),
            status__in=status,
        ).select_related('sponsor')

    def finalized(self):
        return self.filter(status=self.model.FINALIZED)

    def enabled(self):
        """Sponsorship which are finalized and enabled"""
        today = timezone.now().date()
        qs = self.finalized()
        return qs.filter(start_date__lte=today, end_date__gte=today)

    def with_logo_placement(self, logo_place=None, publisher=None):
        from sponsors.models import LogoPlacement, SponsorBenefit
        feature_qs = LogoPlacement.objects.all()
        if logo_place:
            feature_qs = feature_qs.filter(logo_place=logo_place)
        if publisher:
            feature_qs = feature_qs.filter(publisher=publisher)
        benefit_qs = SponsorBenefit.objects.filter(id__in=Subquery(feature_qs.values_list('sponsor_benefit_id', flat=True)))
        return self.filter(id__in=Subquery(benefit_qs.values_list('sponsorship_id', flat=True)))


class SponsorContactQuerySet(QuerySet):
    def get_primary_contact(self, sponsor):
        contact = self.filter(sponsor=sponsor, primary=True).first()
        if not contact:
            raise self.model.DoesNotExist()
        return contact


class SponsorshipBenefitManager(OrderedModelManager):
    def with_conflicts(self):
        return self.exclude(conflicts__isnull=True)

    def without_conflicts(self):
        return self.filter(conflicts__isnull=True)

    def add_ons(self):
        return self.annotate(num_packages=Count("packages")).filter(num_packages=0)

    def with_packages(self):
        return (
            self.annotate(num_packages=Count("packages"))
            .exclude(num_packages=0)
            .order_by("-num_packages", "order")
        )
