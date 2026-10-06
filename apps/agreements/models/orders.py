"""Database-configured programs and the orders prepared from them."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser
    from django.db.models import QuerySet

    from apps.agreements.models.agreements import Agreement
    from apps.agreements.models.terms import TermsVersion
    from apps.agreements.orders.catalog import Agreement as CatalogAgreement
    from apps.agreements.orders.pricing import FeeKey, Quote, QuoteSnapshot
    from apps.users.models import User

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from apps.agreements.auth import can_prepare, is_administrator
from apps.agreements.models.terms import Terms
from apps.agreements.orders.catalog import Catalog, validate_catalog
from apps.agreements.orders.pricing import build_quote, fee_totals, money


class Program(models.Model):
    """Configure an order builder without putting its commercial content in source control."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Allow anyone to browse this program and signed-in customers to start orders. "
        "Does not publish its terms. Leave unchecked for staff-prepared orders only.",
    )
    definition = models.JSONField(validators=[validate_catalog], help_text="Catalog, pricing rules and document copy.")

    class Meta:
        """List programs by title."""

        ordering = ("title",)

    def __str__(self) -> str:
        """Return the staff-managed program title."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the access-controlled program page."""
        return reverse("agreements:program_detail", kwargs={"slug": self.slug})

    @classmethod
    def visible_to(cls, user: User | AnonymousUser) -> QuerySet[Program]:
        """Return programs the visitor can browse, never implicitly exposing private catalogs."""
        return cls.objects.all() if can_prepare(user) else cls.objects.filter(is_public=True)

    @cached_property
    def catalog(self) -> Catalog:
        """Parse the validated definition once per loaded program."""
        return Catalog(self.definition)

    def clean(self) -> None:
        """Require a valid catalog and existing, versioned terms before accepting configuration."""
        super().clean()
        try:
            catalog = Catalog(self.definition)
        except ValidationError as exc:
            raise ValidationError({"definition": exc.messages}) from exc
        slugs = {item.terms_slug for item in catalog.agreements.values()}
        available = set(Terms.objects.filter(slug__in=slugs, versions__isnull=False).values_list("slug", flat=True))
        missing = sorted(slugs - available)
        if missing:
            raise ValidationError({"definition": f"Publish a terms version first for: {', '.join(missing)}."})
        if self.is_public and Terms.objects.filter(slug__in=slugs, is_public=False).exists():
            raise ValidationError({"is_public": "Make every cited set of terms public before publishing the program."})


class Order(models.Model):
    """One customer's selections and the frozen configuration behind their Order Form."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="orders")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders_created")
    customer_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="agreement_orders",
        help_text="The python.org account that may view the order and sign it online.",
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    legal_name = models.CharField("legal name", max_length=255)
    jurisdiction = models.CharField("state or country of organization", max_length=100)
    entity_type = models.CharField(max_length=100, help_text="For example: corporation or limited liability company.")
    address = models.TextField("principal place of business")
    covered_entities = models.TextField("covered entities", help_text="One name per line.")
    discount = models.CharField(max_length=64, default="none")
    authorized_contacts = models.JSONField(default=list)
    billing_contact_name = models.CharField(max_length=255)
    billing_contact_email = models.EmailField()
    notices_contact = models.TextField(blank=True, help_text="Only if different from the principal place of business.")
    agreement = models.OneToOneField(
        "agreements.Agreement", on_delete=models.PROTECT, null=True, blank=True, related_name="order"
    )
    catalog_snapshot = models.JSONField(default=dict, blank=True, editable=False)
    program_title_snapshot = models.CharField(max_length=255, blank=True, editable=False)

    class Meta:
        """List newest orders first."""

        ordering = ("-created",)

    def __str__(self) -> str:
        """Return the customer for listings."""
        return self.legal_name

    def get_absolute_url(self) -> str:
        """Return the customer's order page."""
        return reverse("agreements:order_detail", kwargs={"pk": self.pk})

    @property
    def configuration(self) -> dict[str, Any]:
        """Read offered configuration from the snapshot, not a later catalog revision."""
        return self.catalog_snapshot or self.program.definition

    @cached_property
    def catalog(self) -> Catalog:
        """Parse the configuration used by this order."""
        return Catalog(self.configuration)

    @property
    def program_title(self) -> str:
        """Keep the program's name stable once offered."""
        return self.program_title_snapshot or self.program.title

    @property
    def reference(self) -> str:
        """Return a short reference suitable for quoting."""
        return str(self.pk).split("-")[0].upper()

    @property
    def status(self) -> str:
        """Use the agreement status after offering; otherwise the order is a draft."""
        return self.agreement.status if self.agreement else "draft"

    @cached_property
    def agreement_list(self) -> list[OrderLine]:
        """Return selections in configured order, independent of database JSON ordering."""
        positions = {slug: index for index, slug in enumerate(self.catalog.agreements)}
        lines = list(self.agreements.all())
        for line in lines:
            line.order = self
        return sorted(lines, key=lambda line: positions.get(line.agreement, len(positions)))

    @property
    def is_editable(self) -> bool:
        """Allow selection changes only while the order is a draft."""
        return self.agreement_id is None

    def is_customer(self, user: User | AnonymousUser) -> bool:
        """Check whether the visitor is the linked customer account."""
        return self.customer_account_id is not None and self.customer_account_id == user.pk

    def can_view(self, user: User | AnonymousUser) -> bool:
        """Restrict orders to agreement preparers and their linked customer."""
        return user.is_authenticated and (can_prepare(user) or self.is_customer(user))

    def can_edit(self, user: User | AnonymousUser) -> bool:
        """Allow an authorized viewer to change a draft."""
        return self.is_editable and self.can_view(user)

    def can_offer(self, user: User | AnonymousUser) -> bool:
        """Allow only administrators or the linked customer to offer a draft."""
        return self.is_editable and user.is_authenticated and (is_administrator(user) or self.is_customer(user))

    @property
    def organization_list(self) -> list[str]:
        """Return the covered entity names."""
        return [line.strip() for line in self.covered_entities.splitlines() if line.strip()]

    @property
    def term_months(self) -> int:
        """Return the selected term from the order's configuration."""
        return self.catalog.discount(self.discount).term_months

    def total(self, key: FeeKey) -> Decimal:
        """Sum annual or term totals across the selected agreements."""
        return sum((line.pricing_value(key) for line in self.agreement_list), Decimal(0))

    @cached_property
    def fee_totals(self) -> dict[str, Decimal]:
        """Separate annual and one-time fees across current or frozen selections."""
        totals = {"annual": Decimal(0), "one_time": Decimal(0)}
        for line in self.agreement_list:
            for key, amount in line.fee_totals.items():
                totals[key] += amount
        return totals

    @property
    def term_total_display(self) -> str:
        """Format the combined initial-term fees."""
        return money(self.total("term_total"))


class OrderLine(models.Model):
    """One selected agreement and the fees fixed when the Order Form is offered."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="agreements")
    agreement = models.SlugField(max_length=64)
    tier = models.CharField(max_length=64)
    addons = models.JSONField(default=dict, blank=True)
    special_terms = models.TextField(blank=True, help_text="Set by staff only; leave empty for none.")
    pricing = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        """Allow one selection of each agreement per order."""

        constraints = (models.UniqueConstraint(fields=("order", "agreement"), name="one_order_line_per_agreement"),)

    def __str__(self) -> str:
        """Return the customer and selection."""
        return f"{self.order.legal_name}: {self.agreement}"

    @cached_property
    def agreement_obj(self) -> CatalogAgreement:
        """Return this agreement's configured definition."""
        return self.order.catalog.agreements[self.agreement]

    @property
    def tier_name(self) -> str:
        """Return the selected tier's name."""
        return self.agreement_obj.tier(self.tier).name

    @cached_property
    def cited_terms(self) -> TermsVersion | None:
        """Return the fixed version after offering or the current draft candidate."""
        if self.order.agreement_id:
            return (
                cast("Agreement", self.order.agreement)
                .terms_versions.select_related("terms")
                .get(terms__slug=self.agreement_obj.terms_slug)
            )
        return self.agreement_obj.terms.current_version

    def quote(self) -> Quote:
        """Calculate fees from this order's catalog."""
        return build_quote(self.agreement_obj, self.tier, self.order.discount, self.addons)

    @property
    def pricing_snapshot(self) -> QuoteSnapshot:
        """Return frozen fees after offering or the current draft's quote."""
        return self.pricing or self.quote().as_dict()

    @cached_property
    def fee_totals(self) -> dict[str, Decimal]:
        """Read recurring fees separately from one-time charges in any snapshot."""
        return fee_totals(self.pricing_snapshot)

    def pricing_value(self, key: FeeKey) -> Decimal:
        """Read a numeric fee total."""
        return Decimal(self.pricing_snapshot[key])
