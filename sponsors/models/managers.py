from django.db import IntegrityError
from django.db.models import Count
from ordered_model.models import OrderedModelManager, OrderedModelQuerySet
from django.db.models import Q, Subquery
from django.db.models.query import QuerySet
from django.utils import timezone
from polymorphic.query import PolymorphicQuerySet


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

    def active_on_date(self, ref_date):
        return self.filter(start_date__lte=ref_date, end_date__gte=ref_date)

    def enabled(self):
        """Sponsorship which are finalized and enabled"""
        today = timezone.now().date()
        return self.finalized().active_on_date(today).exclude(overlapped_by__isnull=False)

    def with_logo_placement(self, logo_place=None, publisher=None):
        from sponsors.models import LogoPlacement, SponsorBenefit
        feature_qs = LogoPlacement.objects.all()
        if logo_place:
            feature_qs = feature_qs.filter(logo_place=logo_place)
        if publisher:
            feature_qs = feature_qs.filter(publisher=publisher)
        benefit_qs = SponsorBenefit.objects.filter(id__in=Subquery(feature_qs.values_list('sponsor_benefit_id', flat=True)))
        return self.filter(id__in=Subquery(benefit_qs.values_list('sponsorship_id', flat=True)))

    def includes_benefit_feature(self, feature_model):
        from sponsors.models import SponsorBenefit
        feature_qs = feature_model.objects.all()
        benefit_qs = SponsorBenefit.objects.filter(id__in=Subquery(feature_qs.values_list('sponsor_benefit_id', flat=True)))
        return self.filter(id__in=Subquery(benefit_qs.values_list('sponsorship_id', flat=True)))


class SponsorshipCurrentYearQuerySet(QuerySet):

    def delete(self):
        raise IntegrityError("Singleton object cannot be delete. Try updating it instead.")


class SponsorContactQuerySet(QuerySet):
    def get_primary_contact(self, sponsor):
        contact = self.filter(sponsor=sponsor, primary=True).first()
        if not contact:
            raise self.model.DoesNotExist()
        return contact

    def filter_by_contact_types(self, primary=False, administrative=False, accounting=False, manager=False):
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
    def with_conflicts(self):
        return self.exclude(conflicts__isnull=True)

    def without_conflicts(self):
        return self.filter(conflicts__isnull=True)

    def a_la_carte(self):
        return self.annotate(num_packages=Count("packages")).filter(num_packages=0, standalone=False).exclude(unavailable=True)

    def standalone(self):
        return self.filter(standalone=True).exclude(unavailable=True)

    def with_packages(self):
        return (
            self.annotate(num_packages=Count("packages"))
            .exclude(Q(num_packages=0) | Q(standalone=True))
            .exclude(unavailable=True)
            .order_by("-num_packages", "order")
        )

    def from_year(self, year):
        return self.filter(year=year).exclude(unavailable=True)

    def from_current_year(self):
        from sponsors.models import SponsorshipCurrentYear
        current_year = SponsorshipCurrentYear.get_year()
        return self.from_year(current_year)


class SponsorshipPackageQuerySet(OrderedModelQuerySet):
    def list_advertisables(self):
        return self.filter(advertise=True)

    def from_year(self, year):
        return self.filter(year=year)

    def from_current_year(self):
        from sponsors.models import SponsorshipCurrentYear
        current_year = SponsorshipCurrentYear.get_year()
        return self.from_year(current_year)


class BenefitFeatureQuerySet(PolymorphicQuerySet):

    def delete(self):
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()
        else:
            return super().delete()

    def from_sponsorship(self, sponsorship):
        return self.filter(sponsor_benefit__sponsorship=sponsorship).select_related("sponsor_benefit__sponsorship")

    def required_assets(self):
        from sponsors.models.benefits import RequiredAssetMixin
        required_assets_classes = RequiredAssetMixin.__subclasses__()
        return self.instance_of(*required_assets_classes).select_related("sponsor_benefit__sponsorship")

    def provided_assets(self):
        from sponsors.models.benefits import ProvidedAssetMixin
        provided_assets_classes = ProvidedAssetMixin.__subclasses__()
        return self.instance_of(*provided_assets_classes).select_related("sponsor_benefit__sponsorship")


class BenefitFeatureConfigurationQuerySet(PolymorphicQuerySet):

    def delete(self):
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()
        else:
            return super().delete()


class GenericAssetQuerySet(PolymorphicQuerySet):

    def all_assets(self):
        from sponsors.models import GenericAsset
        classes = GenericAsset.all_asset_types()
        return self.select_related("content_type").instance_of(*classes)
