"""Django admin configuration for the sponsors app."""

import contextlib

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.sites.models import Site
from django.db.models import Subquery
from django.forms import ModelForm
from django.template import Context, Template
from django.urls import path, reverse
from django.utils.functional import cached_property
from django.utils.html import mark_safe
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.fields import Field
from ordered_model.admin import OrderedModelAdmin
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicInlineSupportMixin,
    PolymorphicParentModelAdmin,
    StackedPolymorphicInline,
)

from apps.cms.admin import ContentManageableModelAdmin
from apps.mailing.admin import BaseEmailTemplateAdmin
from apps.sponsors import views_admin
from apps.sponsors.forms import (
    CloneApplicationConfigForm,
    RequiredImgAssetConfigurationForm,
    SponsorBenefitAdminInlineForm,
    SponsorshipBenefitAdminForm,
    SponsorshipReviewAdminForm,
)
from apps.sponsors.models import (
    SPONSOR_TEMPLATE_HELP_TEXT,
    BenefitFeature,
    BenefitFeatureConfiguration,
    Contract,
    EmailTargetableConfiguration,
    FileAsset,
    GenericAsset,
    ImgAsset,
    LegalClause,
    LogoPlacementConfiguration,
    ProvidedFileAssetConfiguration,
    ProvidedTextAssetConfiguration,
    RequiredImgAssetConfiguration,
    RequiredResponseAssetConfiguration,
    RequiredTextAssetConfiguration,
    ResponseAsset,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
    TextAsset,
    TieredBenefitConfiguration,
)


def get_url_base_name(model_class):
    """Return the admin URL base name for the given model class."""
    return f"{model_class._meta.app_label}_{model_class._meta.model_name}"  # noqa: SLF001 - Django _meta API access is standard


class AssetsInline(GenericTabularInline):
    """Inline for displaying generic assets in read-only mode."""

    model = GenericAsset
    extra = 0
    max_num = 0

    def has_delete_permission(self, request, obj):
        """Prevent deletion of assets from the inline."""
        return False

    readonly_fields = ["internal_name", "user_submitted_info", "value"]

    @admin.display(description="Submitted information")
    def value(self, obj=None):
        """Return the asset value or empty string if not set."""
        if not obj or not obj.value:
            return ""
        return obj.value

    @admin.display(
        description="Fullfilled data?",
        boolean=True,
    )
    def user_submitted_info(self, obj=None):
        """Return True if the asset has a submitted value."""
        return bool(self.value(obj))


@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    """Admin for managing sponsorship programs with ordering support."""

    ordering = ("order",)
    list_display = [
        "name",
        "move_up_down_links",
    ]


class MultiPartForceForm(ModelForm):
    """ModelForm that always reports as multipart to support file uploads."""

    def is_multipart(self):
        """Return True to force multipart encoding for file upload support."""
        return True


class BenefitFeatureConfigurationInline(StackedPolymorphicInline):
    """Polymorphic inline for managing benefit feature configurations."""

    form = MultiPartForceForm

    class LogoPlacementConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for logo placement configuration."""

        model = LogoPlacementConfiguration

    class TieredBenefitConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for tiered benefit configuration."""

        model = TieredBenefitConfiguration

    class EmailTargetableConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for email targetable configuration."""

        model = EmailTargetableConfiguration
        readonly_fields = ["display"]

        def display(self, obj):
            """Return the enabled status label."""
            return "Enabled"

    class RequiredImgAssetConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for required image asset configuration."""

        model = RequiredImgAssetConfiguration
        form = RequiredImgAssetConfigurationForm

    class RequiredTextAssetConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for required text asset configuration."""

        model = RequiredTextAssetConfiguration

    class RequiredResponseAssetConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for required response asset configuration."""

        model = RequiredResponseAssetConfiguration

    class ProvidedTextAssetConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for provided text asset configuration."""

        model = ProvidedTextAssetConfiguration

    class ProvidedFileAssetConfigurationInline(StackedPolymorphicInline.Child):
        """Inline for provided file asset configuration."""

        model = ProvidedFileAssetConfiguration

    model = BenefitFeatureConfiguration
    child_inlines = [
        LogoPlacementConfigurationInline,
        TieredBenefitConfigurationInline,
        EmailTargetableConfigurationInline,
        RequiredImgAssetConfigurationInline,
        RequiredTextAssetConfigurationInline,
        RequiredResponseAssetConfigurationInline,
        ProvidedTextAssetConfigurationInline,
        ProvidedFileAssetConfigurationInline,
    ]


@admin.register(SponsorshipBenefit)
class SponsorshipBenefitAdmin(PolymorphicInlineSupportMixin, OrderedModelAdmin):
    """Admin for managing sponsorship benefits with polymorphic feature configurations."""

    change_form_template = "sponsors/admin/sponsorshipbenefit_change_form.html"
    inlines = [BenefitFeatureConfigurationInline]
    ordering = ("-year", "program", "order")
    list_display = [
        "program",
        "year",
        "short_name",
        "package_only",
        "internal_value",
        "unavailable",
        "move_up_down_links",
    ]
    list_filter = ["program", "year", "package_only", "packages", "new", "standalone", "unavailable"]
    search_fields = ["name"]
    form = SponsorshipBenefitAdminForm

    fieldsets = [
        (
            "Public",
            {
                "fields": (
                    "name",
                    "description",
                    "program",
                    "year",
                    "packages",
                    "package_only",
                    "new",
                    "unavailable",
                    "standalone",
                ),
            },
        ),
        (
            "Internal",
            {
                "fields": (
                    "internal_description",
                    "internal_value",
                    "capacity",
                    "soft_capacity",
                    "legal_clauses",
                    "conflicts",
                )
            },
        ),
    ]

    def get_urls(self):
        """Register custom URL for updating related sponsorships."""
        urls = super().get_urls()
        base_name = get_url_base_name(self.model)
        my_urls = [
            path(
                "<int:pk>/update-related-sponsorships",
                self.admin_site.admin_view(self.update_related_sponsorships),
                name=f"{base_name}_update_related",
            ),
        ]
        return my_urls + urls

    def update_related_sponsorships(self, *args, **kwargs):
        """Delegate to the update_related_sponsorships admin view."""
        return views_admin.update_related_sponsorships(self, *args, **kwargs)


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(OrderedModelAdmin):
    """Admin for managing sponsorship packages with ordering and revenue split display."""

    ordering = (
        "-year",
        "order",
    )
    list_display = ["name", "year", "advertise", "allow_a_la_carte", "get_benefit_split", "move_up_down_links"]
    list_filter = ["advertise", "year", "allow_a_la_carte"]
    search_fields = ["name"]

    def get_readonly_fields(self, request, obj=None):
        """Return readonly fields based on object state and user permissions."""
        readonly = ["get_benefit_split"]
        if obj:
            readonly.append("slug")
        if not request.user.is_superuser:
            readonly.append("logo_dimension")
        return readonly

    def get_prepopulated_fields(self, request, obj=None):
        """Prepopulate slug from name only when creating new packages."""
        if not obj:
            return {"slug": ["name"]}
        return {}

    @admin.display(description="Revenue split")
    def get_benefit_split(self, obj: SponsorshipPackage) -> str:
        """Render a stacked bar chart showing the revenue split across programs."""
        colors = [
            "#ffde57",  # Python Gold
            "#4584b6",  # Python Blue
            "#646464",  # Python Grey
        ]
        split = obj.get_default_revenue_split()
        # rotate colors through our available palette
        if len(split) > len(colors):
            colors = colors * (1 + (len(split) // len(colors)))
        # build some span elements to show the percentages and have the program name in the title (to show on hover)
        widths, spans = [], []
        for i, (name, pct) in enumerate(split):
            pct_str = f"{pct:.0f}%"
            widths.append(pct_str)
            spans.append(f"<span title='{name}' style='background-color:{colors[i]}'>{pct_str}</span>")
        # define a style that will show our span elements like a single horizontal stacked bar chart
        style = f"color:#fff;text-align:center;cursor:pointer;display:grid;grid-template-columns:{' '.join(widths)}"
        # wrap it all up and put a bow on it
        html = f"<div style='{style}'>{''.join(spans)}</div>"
        return mark_safe(html)


class SponsorContactInline(admin.TabularInline):
    """Inline for managing sponsor contacts."""

    model = SponsorContact
    raw_id_fields = ["user"]
    extra = 0


class SponsorshipsInline(admin.TabularInline):
    """Read-only inline for displaying sponsorships on the sponsor admin page."""

    model = Sponsorship
    fields = ["link", "status", "year", "applied_on", "start_date", "end_date"]
    readonly_fields = ["link", "status", "year", "applied_on", "start_date", "end_date"]
    can_delete = False
    extra = 0

    @admin.display(description="ID")
    def link(self, obj):
        """Return a link to the sponsorship change page."""
        url = reverse("admin:sponsors_sponsorship_change", args=[obj.id])
        return mark_safe(f"<a href={url}>{obj.id}</a>")


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    """Admin for managing sponsors with contacts, sponsorships, and assets inlines."""

    inlines = [SponsorContactInline, SponsorshipsInline, AssetsInline]
    search_fields = ["name"]


class SponsorBenefitInline(admin.TabularInline):
    """Inline for managing individual sponsor benefits within a sponsorship."""

    model = SponsorBenefit
    form = SponsorBenefitAdminInlineForm
    fields = ["sponsorship_benefit", "benefit_internal_value"]
    extra = 0

    def has_add_permission(self, request, obj=None):
        """Allow adding benefits only when the sponsorship is open for editing."""
        has_add_permission = super().has_add_permission(request, obj=obj)
        match = request.resolver_match
        if match.url_name == "sponsors_sponsorship_change":
            sponsorship = self.parent_model.objects.get(pk=match.kwargs["object_id"])
            has_add_permission = has_add_permission and sponsorship.open_for_editing
        return has_add_permission

    def get_readonly_fields(self, request, obj=None):
        """Make benefit fields readonly when the sponsorship is not open for editing."""
        if obj and not obj.open_for_editing:
            return ["sponsorship_benefit", "benefit_internal_value"]
        return []

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only when the sponsorship is open for editing."""
        if not obj:
            return True
        return obj.open_for_editing

    def get_queryset(self, request):
        """Filter benefits to only those matching the sponsorship's year."""
        # filters the available benefits by the benefits for the year of the sponsorship
        match = request.resolver_match
        sponsorship = self.parent_model.objects.get(pk=match.kwargs["object_id"])
        year = sponsorship.year

        return super().get_queryset(request).filter(sponsorship_benefit__year=year)


class TargetableEmailBenefitsFilter(admin.SimpleListFilter):
    """Filter sponsorships by email-targetable benefits for the current year."""

    title = "targetable email benefits"
    parameter_name = "email_benefit"

    @cached_property
    def benefits(self):
        """Return a dict mapping benefit IDs to email-targetable benefits."""
        qs = EmailTargetableConfiguration.objects.all().values_list("benefit_id", flat=True)
        benefits = SponsorshipBenefit.objects.filter(id__in=Subquery(qs), year=SponsorshipCurrentYear.get_year())
        return {str(b.id): b for b in benefits}

    def lookups(self, request, model_admin):
        """Return filter choices as benefit ID and name pairs."""
        return [(k, b.name) for k, b in self.benefits.items()]

    def queryset(self, request, queryset):
        """Filter sponsorships to those having the selected email-targetable benefit."""
        benefit = self.benefits.get(self.value())
        if not benefit:
            return queryset
        # all sponsors benefit related with such sponsorship benefit
        qs = SponsorBenefit.objects.filter(sponsorship_benefit_id=benefit.id).values_list("sponsorship_id", flat=True)
        return queryset.filter(id__in=Subquery(qs))


class SponsorshipStatusListFilter(admin.SimpleListFilter):
    """Filter sponsorships by status, excluding rejected by default."""

    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        """Return sponsorship status choices."""
        return Sponsorship.STATUS_CHOICES

    def queryset(self, request, queryset):
        """Filter by status or exclude rejected sponsorships when no filter is selected."""
        status = self.value()
        # exclude rejected ones by default
        if not status:
            return queryset.exclude(status=Sponsorship.REJECTED)
        return queryset.filter(status=status)

    def choices(self, changelist):
        """Replace the default 'All' label with a descriptive status label."""
        choices = list(super().choices(changelist))
        # replaces django default "All" text by a custom text
        choices[0]["display"] = "Applied / Approved / Finalized"
        return choices


class SponsorshipResource(resources.ModelResource):
    """Import/export resource for exporting sponsorship data."""

    sponsor_name = Field(attribute="sponsor__name", column_name="Company Name")
    contact_name = Field(column_name="Contact Name(s)")
    contact_email = Field(column_name="Contact Email(s)")
    contact_phone = Field(column_name="Contact phone number")
    contact_type = Field(column_name="Contact Type(s)")
    start_date = Field(attribute="start_date", column_name="Start Date")
    end_date = Field(attribute="end_date", column_name="End Date")
    web_logo = Field(column_name="Logo")
    landing_page_url = Field(attribute="sponsor__landing_page_url", column_name="Webpage link")
    level = Field(attribute="package__name", column_name="Sponsorship Level")
    cost = Field(attribute="sponsorship_fee", column_name="Sponsorship Cost")
    admin_url = Field(attribute="admin_url", column_name="Admin Link")

    class Meta:
        """Meta configuration for SponsorshipResource."""

        model = Sponsorship
        fields = (
            "sponsor_name",
            "contact_name",
            "contact_email",
            "contact_phone",
            "contact_type",
            "start_date",
            "end_date",
            "web_logo",
            "landing_page_url",
            "level",
            "cost",
            "admin_url",
        )
        export_order = (
            "sponsor_name",
            "contact_name",
            "contact_email",
            "contact_phone",
            "contact_type",
            "start_date",
            "end_date",
            "web_logo",
            "landing_page_url",
            "level",
            "cost",
            "admin_url",
        )

    def get_sponsorship_url(self, sponsorship):
        """Return the full admin URL for the given sponsorship."""
        domain = Site.objects.get_current().domain
        url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.id])
        return f"https://{domain}{url}"

    def dehydrate_web_logo(self, sponsorship):
        """Return the sponsor's web logo URL for export."""
        return sponsorship.sponsor.web_logo.url

    def dehydrate_contact_type(self, sponsorship):
        """Return newline-separated contact types for export."""
        return "\n".join([contact.type for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_name(self, sponsorship):
        """Return newline-separated contact names for export."""
        return "\n".join([contact.name for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_email(self, sponsorship):
        """Return newline-separated contact emails for export."""
        return "\n".join([contact.email for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_phone(self, sponsorship):
        """Return newline-separated contact phone numbers for export."""
        return "\n".join([contact.phone for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_admin_url(self, sponsorship):
        """Return the admin URL for the sponsorship for export."""
        return self.get_sponsorship_url(sponsorship)


@admin.register(Sponsorship)
class SponsorshipAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    """Admin for managing sponsorships with approval workflow and contract handling."""

    change_form_template = "sponsors/admin/sponsorship_change_form.html"
    form = SponsorshipReviewAdminForm
    inlines = [SponsorBenefitInline, AssetsInline]
    search_fields = ["sponsor__name"]
    list_display = [
        "sponsor",
        "status",
        "package",
        "year",
        "applied_on",
        "approved_on",
        "start_date",
        "end_date",
    ]
    list_filter = [SponsorshipStatusListFilter, "package", "year", TargetableEmailBenefitsFilter]
    actions = ["send_notifications"]
    resource_class = SponsorshipResource
    fieldsets = [
        (
            "Sponsorship Data",
            {
                "fields": (
                    "for_modified_package",
                    "sponsor_link",
                    "status",
                    "package",
                    "sponsorship_fee",
                    "year",
                    "get_estimated_cost",
                    "start_date",
                    "end_date",
                    "get_contract",
                    "level_name",
                    "renewal",
                    "overlapped_by",
                ),
            },
        ),
        (
            "Sponsor Detailed Information",
            {
                "fields": (
                    "get_sponsor_name",
                    "get_sponsor_description",
                    "get_sponsor_landing_page_url",
                    "get_sponsor_web_logo",
                    "get_sponsor_print_logo",
                    "get_sponsor_primary_phone",
                    "get_sponsor_mailing_address",
                    "get_sponsor_contacts",
                ),
            },
        ),
        (
            "User Customizations",
            {
                "fields": (
                    "get_custom_benefits_added_by_user",
                    "get_custom_benefits_removed_by_user",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            "Events dates",
            {
                "fields": (
                    "applied_on",
                    "approved_on",
                    "rejected_on",
                    "finalized_on",
                ),
                "classes": ["collapse"],
            },
        ),
    ]

    def get_fieldsets(self, request, obj=None):
        """Expand the User Customizations section when customizations exist."""
        fieldsets = []
        for title, cfg in super().get_fieldsets(request, obj):
            # disable collapse option in case of sponsorships with customizations
            if (
                title == "User Customizations"
                and obj
                and (obj.user_customizations["added_by_user"] or obj.user_customizations["removed_by_user"])
            ):
                cfg["classes"] = []
            fieldsets.append((title, cfg))
        return fieldsets

    def get_queryset(self, *args, **kwargs):
        """Optimize queryset with select_related for sponsor, package, and submitter."""
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsor", "package", "submited_by")

    @admin.action(description="Send notifications to selected")
    def send_notifications(self, request, queryset):
        """Delegate to the send_sponsorship_notifications_action admin view."""
        return views_admin.send_sponsorship_notifications_action(self, request, queryset)

    def get_readonly_fields(self, request, obj):
        """Return readonly fields based on sponsorship editing state and year."""
        readonly_fields = [
            "for_modified_package",
            "sponsor_link",
            "status",
            "applied_on",
            "rejected_on",
            "approved_on",
            "finalized_on",
            "level_name",
            "get_estimated_cost",
            "get_sponsor_name",
            "get_sponsor_description",
            "get_sponsor_landing_page_url",
            "get_sponsor_web_logo",
            "get_sponsor_print_logo",
            "get_sponsor_primary_phone",
            "get_sponsor_mailing_address",
            "get_sponsor_contacts",
            "get_contract",
            "get_added_by_user",
            "get_custom_benefits_added_by_user",
            "get_custom_benefits_removed_by_user",
        ]

        if obj and not obj.open_for_editing:
            extra = ["start_date", "end_date", "package", "level_name", "sponsorship_fee"]
            readonly_fields.extend(extra)

        if obj.year:
            readonly_fields.append("year")

        return readonly_fields

    @admin.display(description="Sponsor")
    def sponsor_link(self, obj):
        """Return an HTML link to the sponsor's admin change page."""
        url = reverse("admin:sponsors_sponsor_change", args=[obj.sponsor.id])
        return mark_safe(f"<a href={url}>{obj.sponsor.name}</a>")

    @admin.display(description="Estimated cost")
    def get_estimated_cost(self, obj):
        """Return the estimated cost HTML for customized sponsorships."""
        cost = None
        html = "This sponsorship has not customizations so there's no estimated cost"
        if obj.for_modified_package:
            msg = "This sponsorship has customizations and this cost is a sum of all benefit's internal values from when this sponsorship was created"
            cost = intcomma(obj.estimated_cost)
            html = f"{cost} USD <br/><b>Important: </b> {msg}"
        return mark_safe(html)

    @admin.display(description="Contract")
    def get_contract(self, obj):
        """Return an HTML link to the contract or a placeholder."""
        if not obj.contract:
            return "---"
        url = reverse("admin:sponsors_contract_change", args=[obj.contract.pk])
        html = f"<a href='{url}' target='_blank'>{obj.contract}</a>"
        return mark_safe(html)

    def get_urls(self):
        """Register custom admin URLs for sponsorship workflow actions."""
        urls = super().get_urls()
        base_name = get_url_base_name(self.model)
        my_urls = [
            path(
                "<int:pk>/reject",
                # TODO: maybe it would be better to create a specific
                # group or permission to review sponsorship applications
                self.admin_site.admin_view(self.reject_sponsorship_view),
                name=f"{base_name}_reject",
            ),
            path(
                "<int:pk>/approve-existing",
                self.admin_site.admin_view(self.approve_signed_sponsorship_view),
                name=f"{base_name}_approve_existing_contract",
            ),
            path(
                "<int:pk>/approve",
                self.admin_site.admin_view(self.approve_sponsorship_view),
                name=f"{base_name}_approve",
            ),
            path(
                "<int:pk>/enable-edit",
                self.admin_site.admin_view(self.rollback_to_editing_view),
                name=f"{base_name}_rollback_to_edit",
            ),
            path(
                "<int:pk>/list-assets",
                self.admin_site.admin_view(self.list_uploaded_assets_view),
                name=f"{base_name}_list_uploaded_assets",
            ),
            path(
                "<int:pk>/unlock",
                self.admin_site.admin_view(self.unlock_view),
                name=f"{base_name}_unlock",
            ),
            path(
                "<int:pk>/lock",
                self.admin_site.admin_view(self.lock_view),
                name=f"{base_name}_lock",
            ),
        ]
        return my_urls + urls

    @admin.display(description="Name")
    def get_sponsor_name(self, obj):
        """Return the sponsor's name."""
        return obj.sponsor.name

    @admin.display(description="Description")
    def get_sponsor_description(self, obj):
        """Return the sponsor's description."""
        return obj.sponsor.description

    @admin.display(description="Landing Page URL")
    def get_sponsor_landing_page_url(self, obj):
        """Return the sponsor's landing page URL."""
        return obj.sponsor.landing_page_url

    @admin.display(description="Web Logo")
    def get_sponsor_web_logo(self, obj):
        """Render and return the sponsor's web logo as a thumbnail image."""
        html = "{% load thumbnail %}{% thumbnail sponsor.web_logo '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
        template = Template(html)
        context = Context({"sponsor": obj.sponsor})
        html = template.render(context)
        return mark_safe(html)

    @admin.display(description="Print Logo")
    def get_sponsor_print_logo(self, obj):
        """Render and return the sponsor's print logo as a thumbnail image."""
        img = obj.sponsor.print_logo
        html = ""
        if img:
            html = "{% load thumbnail %}{% thumbnail img '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
            template = Template(html)
            context = Context({"img": img})
            html = template.render(context)
        return mark_safe(html) if html else "---"

    @admin.display(description="Primary Phone")
    def get_sponsor_primary_phone(self, obj):
        """Return the sponsor's primary phone number."""
        return obj.sponsor.primary_phone

    @admin.display(description="Mailing/Billing Address")
    def get_sponsor_mailing_address(self, obj):
        """Return the sponsor's formatted mailing address as HTML."""
        sponsor = obj.sponsor
        city_row = f"{sponsor.city} - {sponsor.get_country_display()} ({sponsor.country})"
        if sponsor.state:
            city_row = f"{sponsor.city} - {sponsor.state} - {sponsor.get_country_display()} ({sponsor.country})"

        mail_row = sponsor.mailing_address_line_1
        if sponsor.mailing_address_line_2:
            mail_row += f" - {sponsor.mailing_address_line_2}"

        html = f"<p>{city_row}</p>"
        html += f"<p>{mail_row}</p>"
        html += f"<p>{sponsor.postal_code}</p>"
        return mark_safe(html)

    @admin.display(description="Contacts")
    def get_sponsor_contacts(self, obj):
        """Return the sponsor's contacts formatted as an HTML list."""
        html = ""
        contacts = obj.sponsor.contacts.all()
        primary = [c for c in contacts if c.primary]
        not_primary = [c for c in contacts if not c.primary]
        if primary:
            html = "<b>Primary contacts</b><ul>"
            html += "".join([f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in primary])
            html += "</ul>"
        if not_primary:
            html += "<b>Other contacts</b><ul>"
            html += "".join([f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in not_primary])
            html += "</ul>"
        return mark_safe(html)

    @admin.display(description="Added by User")
    def get_custom_benefits_added_by_user(self, obj):
        """Return benefits added by the user as HTML paragraphs."""
        benefits = obj.user_customizations["added_by_user"]
        if not benefits:
            return "---"

        html = "".join([f"<p>{b}</p>" for b in benefits])
        return mark_safe(html)

    @admin.display(description="Removed by User")
    def get_custom_benefits_removed_by_user(self, obj):
        """Return benefits removed by the user as HTML paragraphs."""
        benefits = obj.user_customizations["removed_by_user"]
        if not benefits:
            return "---"

        html = "".join([f"<p>{b}</p>" for b in benefits])
        return mark_safe(html)

    def rollback_to_editing_view(self, request, pk):
        """Delegate to the rollback_to_editing admin view."""
        return views_admin.rollback_to_editing_view(self, request, pk)

    def reject_sponsorship_view(self, request, pk):
        """Delegate to the reject_sponsorship admin view."""
        return views_admin.reject_sponsorship_view(self, request, pk)

    def approve_sponsorship_view(self, request, pk):
        """Delegate to the approve_sponsorship admin view."""
        return views_admin.approve_sponsorship_view(self, request, pk)

    def approve_signed_sponsorship_view(self, request, pk):
        """Delegate to the approve_signed_sponsorship admin view."""
        return views_admin.approve_signed_sponsorship_view(self, request, pk)

    def list_uploaded_assets_view(self, request, pk):
        """Delegate to the list_uploaded_assets admin view."""
        return views_admin.list_uploaded_assets(self, request, pk)

    def unlock_view(self, request, pk):
        """Delegate to the unlock admin view."""
        return views_admin.unlock_view(self, request, pk)

    def lock_view(self, request, pk):
        """Delegate to the lock admin view."""
        return views_admin.lock_view(self, request, pk)


@admin.register(SponsorshipCurrentYear)
class SponsorshipCurrentYearAdmin(admin.ModelAdmin):
    """Admin for managing the current sponsorship year and cloning configurations."""

    list_display = ["year", "links", "other_years"]
    change_list_template = "sponsors/admin/sponsors_sponsorshipcurrentyear_changelist.html"

    def has_add_permission(self, *args, **kwargs):
        """Prevent adding new current year records."""
        return False

    def has_delete_permission(self, *args, **kwargs):
        """Prevent deleting the current year record."""
        return False

    def get_urls(self):
        """Register the clone configuration URL."""
        urls = super().get_urls()
        base_name = get_url_base_name(self.model)
        my_urls = [
            path(
                "clone-year-config",
                self.admin_site.admin_view(self.clone_application_config),
                name=f"{base_name}_clone",
            ),
        ]
        return my_urls + urls

    @admin.display(description="Links")
    def links(self, obj):
        """Return HTML links to application preview and benefit/package lists."""
        application_url = reverse("select_sponsorship_application_benefits")
        benefits_url = reverse("admin:sponsors_sponsorshipbenefit_changelist")
        preview_label = "View sponsorship application"
        year = obj.year
        html = "<ul>"
        preview_querystring = f"config_year={year}"
        preview_url = f"{application_url}?{preview_querystring}"
        filter_querystring = f"year={year}"
        year_benefits_url = f"{benefits_url}?{filter_querystring}"
        year_packages_url = f"{benefits_url}?{filter_querystring}"

        html += f"<li><a target='_blank' href='{year_packages_url}'>List packages</a>"
        html += f"<li><a target='_blank' href='{year_benefits_url}'>List benefits</a>"
        html += f"<li><a target='_blank' href='{preview_url}'>{preview_label}</a>"
        html += "</ul>"
        return mark_safe(html)

    @admin.display(description="Other configured years")
    def other_years(self, obj):
        """Return HTML links for all configured years except the current one."""
        clone_form = CloneApplicationConfigForm()
        configured_years = clone_form.configured_years
        with contextlib.suppress(ValueError):
            configured_years.remove(obj.year)
        if not configured_years:
            return "---"

        application_url = reverse("select_sponsorship_application_benefits")
        benefits_url = reverse("admin:sponsors_sponsorshipbenefit_changelist")
        preview_label = "View sponsorship application form for this year"
        html = "<ul>"
        for year in configured_years:
            preview_querystring = f"config_year={year}"
            preview_url = f"{application_url}?{preview_querystring}"
            filter_querystring = f"year={year}"
            year_benefits_url = f"{benefits_url}?{filter_querystring}"
            year_packages_url = f"{benefits_url}?{filter_querystring}"

            html += f"<li><b>{year}</b>:"
            html += "<ul>"
            html += f"<li><a target='_blank' href='{year_packages_url}'>List packages</a>"
            html += f"<li><a target='_blank' href='{year_benefits_url}'>List benefits</a>"
            html += f"<li><a target='_blank' href='{preview_url}'>{preview_label}</a>"
            html += "</ul></li>"
        html += "</ul>"
        return mark_safe(html)

    def clone_application_config(self, request):
        """Delegate to the clone_application_config admin view."""
        return views_admin.clone_application_config(self, request)


@admin.register(LegalClause)
class LegalClauseModelAdmin(OrderedModelAdmin):
    """Admin for managing legal clauses with ordering support."""

    list_display = ["internal_name"]


@admin.register(Contract)
class ContractModelAdmin(admin.ModelAdmin):
    """Admin for managing sponsorship contracts with workflow actions."""

    change_form_template = "sponsors/admin/contract_change_form.html"
    list_filter = ["sponsorship__year"]
    list_display = [
        "id",
        "sponsorship",
        "created_on",
        "last_update",
        "status",
        "get_revision",
        "document_link",
    ]

    def get_queryset(self, *args, **kwargs):
        """Optimize queryset with select_related for sponsorship and sponsor."""
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsorship__sponsor")

    @admin.display(description="Revision")
    def get_revision(self, obj):
        """Return the revision number or 'Final' for non-draft contracts."""
        return obj.revision if obj.is_draft else "Final"

    fieldsets = [
        (
            "Info",
            {
                "fields": ("get_sponsorship_url", "status", "revision"),
            },
        ),
        (
            "Editable",
            {
                "fields": (
                    "sponsor_info",
                    "sponsor_contact",
                    "benefits_list",
                    "legal_clauses",
                ),
            },
        ),
        (
            "Files",
            {
                "fields": (
                    "document",
                    "document_docx",
                    "signed_document",
                )
            },
        ),
        (
            "Activities log",
            {
                "fields": (
                    "created_on",
                    "last_update",
                    "sent_on",
                ),
                "classes": ["collapse"],
            },
        ),
    ]

    def get_readonly_fields(self, request, obj):
        """Return readonly fields, making contract content readonly after finalization."""
        readonly_fields = [
            "status",
            "created_on",
            "last_update",
            "sent_on",
            "sponsorship",
            "revision",
            "document",
            "document_docx",
            "signed_document",
            "get_sponsorship_url",
        ]

        if obj and not obj.is_draft:
            extra = [
                "sponsor_info",
                "sponsor_contact",
                "benefits_list",
                "legal_clauses",
            ]
            readonly_fields.extend(extra)

        return readonly_fields

    @admin.display(description="Contract document")
    def document_link(self, obj):
        """Return an HTML link to preview, download, or view the contract document."""
        html, url, msg = "---", "", ""

        if obj.is_draft:
            url = obj.preview_url
            msg = "Preview document"
        elif obj.document:
            url = obj.document.url
            msg = "Download Contract"
        elif obj.signed_document:
            url = obj.signed_document.url
            msg = "Download Signed Contract"

        if url and msg:
            html = f'<a href="{url}" target="_blank">{msg}</a>'
        return mark_safe(html)

    @admin.display(description="Sponsorship")
    def get_sponsorship_url(self, obj):
        """Return an HTML link to the related sponsorship's admin page."""
        if not obj.sponsorship:
            return "---"
        url = reverse("admin:sponsors_sponsorship_change", args=[obj.sponsorship.pk])
        html = f"<a href='{url}' target='_blank'>{obj.sponsorship}</a>"
        return mark_safe(html)

    def get_urls(self):
        """Register custom admin URLs for contract workflow actions."""
        urls = super().get_urls()
        base_name = get_url_base_name(self.model)
        my_urls = [
            path(
                "<int:pk>/preview",
                self.admin_site.admin_view(self.preview_contract_view),
                name=f"{base_name}_preview",
            ),
            path(
                "<int:pk>/send",
                self.admin_site.admin_view(self.send_contract_view),
                name=f"{base_name}_send",
            ),
            path(
                "<int:pk>/execute",
                self.admin_site.admin_view(self.execute_contract_view),
                name=f"{base_name}_execute",
            ),
            path(
                "<int:pk>/nullify",
                self.admin_site.admin_view(self.nullify_contract_view),
                name=f"{base_name}_nullify",
            ),
        ]
        return my_urls + urls

    def preview_contract_view(self, request, pk):
        """Delegate to the preview_contract admin view."""
        return views_admin.preview_contract_view(self, request, pk)

    def send_contract_view(self, request, pk):
        """Delegate to the send_contract admin view."""
        return views_admin.send_contract_view(self, request, pk)

    def execute_contract_view(self, request, pk):
        """Delegate to the execute_contract admin view."""
        return views_admin.execute_contract_view(self, request, pk)

    def nullify_contract_view(self, request, pk):
        """Delegate to the nullify_contract admin view."""
        return views_admin.nullify_contract_view(self, request, pk)


@admin.register(SponsorEmailNotificationTemplate)
class SponsorEmailNotificationTemplateAdmin(BaseEmailTemplateAdmin):
    """Admin for managing sponsor email notification templates."""

    def get_form(self, request, obj=None, **kwargs):
        """Add sponsor-specific help text to the content field."""
        help_texts = {
            "content": SPONSOR_TEMPLATE_HELP_TEXT,
        }
        kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)


class AssetTypeListFilter(admin.SimpleListFilter):
    """Filter assets by their polymorphic type."""

    title = "Asset Type"
    parameter_name = "type"

    @property
    def assets_types_mapping(self):
        """Return a mapping of asset type names to their model classes."""
        return {asset_type.__name__: asset_type for asset_type in GenericAsset.all_asset_types()}

    def lookups(self, request, model_admin):
        """Return filter choices as asset type name and verbose name pairs."""
        return [(k, v._meta.verbose_name_plural) for k, v in self.assets_types_mapping.items()]  # noqa: SLF001 - Django _meta API access

    def queryset(self, request, queryset):
        """Filter the queryset to only include assets of the selected type."""
        asset_type = self.assets_types_mapping.get(self.value())
        if not asset_type:
            return queryset
        return queryset.instance_of(asset_type)


class AssociatedBenefitListFilter(admin.SimpleListFilter):
    """Filter assets by the benefit that requires them."""

    title = "From Benefit Which Requires Asset"
    parameter_name = "from_benefit"

    @property
    def benefits_with_assets(self):
        """Return a mapping of benefit IDs to benefits that have required assets."""
        qs = (
            BenefitFeature.objects.required_assets()
            .values_list("sponsor_benefit__sponsorship_benefit", flat=True)
            .distinct()
        )
        benefits = SponsorshipBenefit.objects.filter(id__in=Subquery(qs))
        return {str(b.id): b for b in benefits}

    def lookups(self, request, model_admin):
        """Return filter choices as benefit ID and name/year pairs."""
        return [(k, f"{b.name} ({b.year})") for k, b in self.benefits_with_assets.items()]

    def queryset(self, request, queryset):
        """Filter assets to those with internal names matching the selected benefit."""
        benefit = self.benefits_with_assets.get(self.value())
        if not benefit:
            return queryset
        internal_names = [cfg.internal_name for cfg in benefit.features_config.all() if hasattr(cfg, "internal_name")]
        return queryset.filter(internal_name__in=internal_names)


class AssetContentTypeFilter(admin.SimpleListFilter):
    """Filter assets by their related object type (Sponsor or Sponsorship)."""

    title = "Related Object"
    parameter_name = "content_type"

    def lookups(self, request, model_admin):
        """Return filter choices for Sponsor and Sponsorship content types."""
        qs = ContentType.objects.filter(model__in=["sponsorship", "sponsor"])
        return [(c_type.pk, c_type.model.title()) for c_type in qs]

    def queryset(self, request, queryset):
        """Filter assets by the selected content type."""
        value = self.value()
        if not value:
            return queryset
        return queryset.filter(content_type=value)


class AssetWithOrWithoutValueFilter(admin.SimpleListFilter):
    """Filter assets by whether they have a value or not."""

    title = "Value"
    parameter_name = "value"

    def lookups(self, request, model_admin):
        """Return filter choices for with/without value."""
        return [
            ("with-value", "With value"),
            ("no-value", "Without value"),
        ]

    def queryset(self, request, queryset):
        """Filter assets to those with or without a value."""
        value = self.value()
        if not value:
            return queryset
        with_value_id = [asset.pk for asset in queryset if asset.value]
        if value == "with-value":
            return queryset.filter(pk__in=with_value_id)
        return queryset.exclude(pk__in=with_value_id)


@admin.register(GenericAsset)
class GenericAssetModelAdmin(PolymorphicParentModelAdmin):
    """Admin for viewing and exporting all generic asset types."""

    list_display = ["id", "internal_name", "get_value", "content_type", "get_related_object"]
    list_filter = [
        AssetContentTypeFilter,
        AssetTypeListFilter,
        AssetWithOrWithoutValueFilter,
        AssociatedBenefitListFilter,
    ]
    actions = ["export_assets_as_zipfile"]

    def get_child_models(self, *args, **kwargs):
        """Return all concrete GenericAsset subclasses."""
        return GenericAsset.all_asset_types()

    def get_queryset(self, *args, **kwargs):
        """Return all assets resolved to their concrete types."""
        return GenericAsset.objects.all_assets()

    def get_actions(self, request):
        """Remove the default delete action from the actions list."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_add_permission(self, *args, **kwargs):
        """Prevent adding assets directly through the admin."""
        return False

    @cached_property
    def all_sponsors(self):
        """Return a cached dict of all sponsors keyed by ID."""
        qs = Sponsor.objects.all()
        return {sp.id: sp for sp in qs}

    @cached_property
    def all_sponsorships(self):
        """Return a cached dict of all sponsorships keyed by ID."""
        qs = Sponsorship.objects.all().select_related("package", "sponsor")
        return {sp.id: sp for sp in qs}

    @admin.display(description="Value")
    def get_value(self, obj):
        """Return the asset value, linking to the file URL if applicable."""
        html = obj.value
        if obj.value and getattr(obj.value, "url", None):
            html = f"<a href='{obj.value.url}' target='_blank'>{obj.value}</a>"
        return mark_safe(html)

    @admin.display(description="Associated with")
    def get_related_object(self, obj):
        """Return the content_object as a URL with cached property optimization.

        Perform better than direct content_object access because
        of sponsors and sponsorship cached properties.
        """
        content_object = None
        if obj.from_sponsorship:
            content_object = self.all_sponsorships[obj.object_id]
        elif obj.from_sponsor:
            content_object = self.all_sponsors[obj.object_id]

        if not content_object:  # safety belt
            return obj.content_object

        html = f"<a href='{content_object.admin_url}' target='_blank'>{content_object}</a>"
        return mark_safe(html)

    @admin.action(description="Export selected")
    def export_assets_as_zipfile(self, request, queryset):
        """Delegate to the export_assets_as_zipfile admin view."""
        return views_admin.export_assets_as_zipfile(self, request, queryset)


class GenericAssetChildModelAdmin(PolymorphicChildModelAdmin):
    """Base admin class for all GenericAsset child models."""

    base_model = GenericAsset
    readonly_fields = ["uuid", "content_type", "object_id", "content_object", "internal_name"]


@admin.register(TextAsset)
class TextAssetModelAdmin(GenericAssetChildModelAdmin):
    """Admin for text asset instances."""

    base_model = TextAsset


@admin.register(ImgAsset)
class ImgAssetModelAdmin(GenericAssetChildModelAdmin):
    """Admin for image asset instances."""

    base_model = ImgAsset


@admin.register(FileAsset)
class FileAssetModelAdmin(GenericAssetChildModelAdmin):
    """Admin for file asset instances."""

    base_model = FileAsset


@admin.register(ResponseAsset)
class ResponseAssetModelAdmin(GenericAssetChildModelAdmin):
    """Admin for response asset instances."""

    base_model = ResponseAsset
