"""QuerySet classes for the sponsors app models."""

from django.db import IntegrityError
from django.db.models import Count, Q, Subquery
from django.db.models.query import QuerySet
from django.utils import timezone
from ordered_model.models import OrderedModelQuerySet
from polymorphic.query import PolymorphicQuerySet


class SponsorshipQuerySet(QuerySet):
    """Custom queryset for filtering and querying Sponsorship objects."""

    def in_progress(self):
        """Return sponsorships with applied or approved status."""
        status = [self.model.APPLIED, self.model.APPROVED]
        return self.filter(status__in=status)

    def approved(self):
        """Return sponsorships with approved status."""
        return self.filter(status=self.model.APPROVED)

    def visible_to(self, user):
        """Return sponsorships visible to the given user based on contact or submission."""
        contacts = user.sponsorcontact_set.values_list("sponsor_id", flat=True)
        status = [self.model.APPLIED, self.model.APPROVED, self.model.FINALIZED]
        return self.filter(
            Q(submited_by=user) | Q(sponsor_id__in=Subquery(contacts)),
            status__in=status,
        ).select_related("sponsor")

    def finalized(self):
        """Return sponsorships with finalized status."""
        return self.filter(status=self.model.FINALIZED)

    def active_on_date(self, ref_date):
        """Return sponsorships active on the given date."""
        return self.filter(start_date__lte=ref_date, end_date__gte=ref_date)

    def enabled(self):
        """Return sponsorships that are finalized, active today, and not overlapped."""
        today = timezone.now().date()
        return self.finalized().active_on_date(today).exclude(overlapped_by__isnull=False)

    def with_logo_placement(self, logo_place=None, publisher=None):
        """Return sponsorships that have logo placements matching the given filters."""
        from sponsors.models import LogoPlacement, SponsorBenefit

        feature_qs = LogoPlacement.objects.all()
        if logo_place:
            feature_qs = feature_qs.filter(logo_place=logo_place)
        if publisher:
            feature_qs = feature_qs.filter(publisher=publisher)
        benefit_qs = SponsorBenefit.objects.filter(
            id__in=Subquery(feature_qs.values_list("sponsor_benefit_id", flat=True))
        )
        return self.filter(id__in=Subquery(benefit_qs.values_list("sponsorship_id", flat=True)))

    def includes_benefit_feature(self, feature_model):
        """Return sponsorships that include the given benefit feature type."""
        from sponsors.models import SponsorBenefit

        feature_qs = feature_model.objects.all()
        benefit_qs = SponsorBenefit.objects.filter(
            id__in=Subquery(feature_qs.values_list("sponsor_benefit_id", flat=True))
        )
        return self.filter(id__in=Subquery(benefit_qs.values_list("sponsorship_id", flat=True)))


class SponsorshipCurrentYearQuerySet(QuerySet):
    """QuerySet for the singleton SponsorshipCurrentYear model."""

    def delete(self):
        """Prevent deletion of the singleton current year record."""
        msg = "Singleton object cannot be delete. Try updating it instead."
        raise IntegrityError(msg)


class SponsorContactQuerySet(QuerySet):
    """QuerySet for filtering sponsor contacts by type and role."""

    def get_primary_contact(self, sponsor):
        """Return the primary contact for the given sponsor or raise DoesNotExist."""
        contact = self.filter(sponsor=sponsor, primary=True).first()
        if not contact:
            raise self.model.DoesNotExist
        return contact

    def filter_by_contact_types(self, primary=False, administrative=False, accounting=False, manager=False):
        """Filter contacts by one or more contact type flags."""
        if not any([primary, administrative, accounting, manager]):
            return self.none()

        query = Q()
        if primary:
            query |= Q(primary=True)
        if administrative:
            query |= Q(administrative=True)
        if accounting:
            query |= Q(accounting=True)
        if manager:
            query |= Q(manager=True)

        return self.filter(query)


class SponsorshipBenefitQuerySet(OrderedModelQuerySet):
    """QuerySet for filtering sponsorship benefits by availability and packaging."""

    def with_conflicts(self):
        """Return benefits that have conflicts with other benefits."""
        return self.exclude(conflicts__isnull=True)

    def without_conflicts(self):
        """Return benefits that have no conflicts."""
        return self.filter(conflicts__isnull=True)

    def a_la_carte(self):
        """Return available benefits not assigned to any package and not standalone."""
        return (
            self.annotate(num_packages=Count("packages"))
            .filter(num_packages=0, standalone=False)
            .exclude(unavailable=True)
        )

    def standalone(self):
        """Return available standalone benefits."""
        return self.filter(standalone=True).exclude(unavailable=True)

    def with_packages(self):
        """Return available benefits that belong to at least one package."""
        return (
            self.annotate(num_packages=Count("packages"))
            .exclude(Q(num_packages=0) | Q(standalone=True))
            .exclude(unavailable=True)
            .order_by("-num_packages", "order")
        )

    def from_year(self, year):
        """Return available benefits for the given year."""
        return self.filter(year=year).exclude(unavailable=True)

    def from_current_year(self):
        """Return available benefits for the current sponsorship year."""
        from sponsors.models import SponsorshipCurrentYear

        current_year = SponsorshipCurrentYear.get_year()
        return self.from_year(current_year)


class SponsorshipPackageQuerySet(OrderedModelQuerySet):
    """QuerySet for filtering sponsorship packages."""

    def list_advertisables(self):
        """Return packages that are marked for advertising."""
        return self.filter(advertise=True)

    def from_year(self, year):
        """Return packages for the given year."""
        return self.filter(year=year)

    def from_current_year(self):
        """Return packages for the current sponsorship year."""
        from sponsors.models import SponsorshipCurrentYear

        current_year = SponsorshipCurrentYear.get_year()
        return self.from_year(current_year)


class BenefitFeatureQuerySet(PolymorphicQuerySet):
    """QuerySet for polymorphic benefit feature models."""

    def delete(self):
        """Delete using non-polymorphic queryset to avoid polymorphic deletion issues."""
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()
        return super().delete()

    def from_sponsorship(self, sponsorship):
        """Return benefit features belonging to the given sponsorship."""
        return self.filter(sponsor_benefit__sponsorship=sponsorship).select_related("sponsor_benefit__sponsorship")

    def required_assets(self):
        """Return benefit features that require asset uploads from sponsors."""
        from sponsors.models.benefits import RequiredAssetMixin

        required_assets_classes = RequiredAssetMixin.__subclasses__()
        return self.instance_of(*required_assets_classes).select_related("sponsor_benefit__sponsorship")

    def provided_assets(self):
        """Return benefit features that provide assets to sponsors."""
        from sponsors.models.benefits import ProvidedAssetMixin

        provided_assets_classes = ProvidedAssetMixin.__subclasses__()
        return self.instance_of(*provided_assets_classes).select_related("sponsor_benefit__sponsorship")


class BenefitFeatureConfigurationQuerySet(PolymorphicQuerySet):
    """QuerySet for polymorphic benefit feature configuration models."""

    def delete(self):
        """Delete using non-polymorphic queryset to avoid polymorphic deletion issues."""
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()
        return super().delete()


class GenericAssetQuerySet(PolymorphicQuerySet):
    """QuerySet for polymorphic generic asset models."""

    def all_assets(self):
        """Return all assets resolved to their concrete subclass types."""
        from sponsors.models import GenericAsset

        classes = GenericAsset.all_asset_types()
        return self.select_related("content_type").instance_of(*classes)
