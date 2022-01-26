from django.contrib.contenttypes.admin import GenericTabularInline
from ordered_model.admin import OrderedModelAdmin
from polymorphic.admin import PolymorphicInlineSupportMixin, StackedPolymorphicInline, PolymorphicParentModelAdmin, \
    PolymorphicChildModelAdmin

from django.db.models import Subquery
from django.template import Context, Template
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import path, reverse, resolve
from django.utils.functional import cached_property
from django.utils.html import mark_safe

from mailing.admin import BaseEmailTemplateAdmin
from sponsors.models import *
from sponsors.models.benefits import RequiredAssetMixin
from sponsors import views_admin
from sponsors.forms import SponsorshipReviewAdminForm, SponsorBenefitAdminInlineForm, RequiredImgAssetConfigurationForm, \
    SponsorshipBenefitAdminForm
from cms.admin import ContentManageableModelAdmin


class AssetsInline(GenericTabularInline):
    model = GenericAsset
    extra = 0
    max_num = 0
    has_delete_permission = lambda self, request, obj: False
    readonly_fields = ["internal_name", "user_submitted_info", "value"]

    def value(self, request, obj=None):
        if not obj or not obj.value:
            return ""
        return obj.value

    value.short_description = "Submitted information"

    def user_submitted_info(self, request, obj=None):
        return bool(self.value(request, obj))

    user_submitted_info.short_description = "Fullfilled data?"
    user_submitted_info.boolean = True


@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = [
        "name",
        "move_up_down_links",
    ]


class BenefitFeatureConfigurationInline(StackedPolymorphicInline):
    class LogoPlacementConfigurationInline(StackedPolymorphicInline.Child):
        model = LogoPlacementConfiguration

    class TieredQuantityConfigurationInline(StackedPolymorphicInline.Child):
        model = TieredQuantityConfiguration

    class EmailTargetableConfigurationInline(StackedPolymorphicInline.Child):
        model = EmailTargetableConfiguration
        readonly_fields = ["display"]

        def display(self, obj):
            return "Enabled"

    class RequiredImgAssetConfigurationInline(StackedPolymorphicInline.Child):
        model = RequiredImgAssetConfiguration
        form = RequiredImgAssetConfigurationForm

    class RequiredTextAssetConfigurationInline(StackedPolymorphicInline.Child):
        model = RequiredTextAssetConfiguration

    model = BenefitFeatureConfiguration
    child_inlines = [
        LogoPlacementConfigurationInline,
        TieredQuantityConfigurationInline,
        EmailTargetableConfigurationInline,
        RequiredImgAssetConfigurationInline,
        RequiredTextAssetConfigurationInline,
    ]


@admin.register(SponsorshipBenefit)
class SponsorshipBenefitAdmin(PolymorphicInlineSupportMixin, OrderedModelAdmin):
    change_form_template = "sponsors/admin/sponsorshipbenefit_change_form.html"
    inlines = [BenefitFeatureConfigurationInline]
    ordering = ("program", "order")
    list_display = [
        "program",
        "short_name",
        "package_only",
        "internal_value",
        "move_up_down_links",
    ]
    list_filter = ["program", "package_only", "packages", "new", "a_la_carte", "unavailable"]
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
                    "packages",
                    "package_only",
                    "new",
                    "unavailable",
                    "a_la_carte",
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
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/update-related-sponsorships",
                self.admin_site.admin_view(self.update_related_sponsorships),
                name="sponsors_sponsorshipbenefit_update_related",
            ),
        ]
        return my_urls + urls

    def update_related_sponsorships(self, *args, **kwargs):
        return views_admin.update_related_sponsorships(self, *args, **kwargs)


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = ["name", "advertise", "move_up_down_links"]
    list_filter = ["advertise"]
    search_fields = ["name"]

    def get_readonly_fields(self, request, obj=None):
        readonly = []
        if obj:
            readonly.append("slug")
        if not request.user.is_superuser:
            readonly.append("logo_dimension")
        return readonly

    def get_prepopulated_fields(self, request, obj=None):
        if not obj:
            return {'slug': ['name']}
        return {}


class SponsorContactInline(admin.TabularInline):
    model = SponsorContact
    raw_id_fields = ["user"]
    extra = 0


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    inlines = [SponsorContactInline, AssetsInline]
    search_fields = ["name"]


class SponsorBenefitInline(admin.TabularInline):
    model = SponsorBenefit
    form = SponsorBenefitAdminInlineForm
    fields = ["sponsorship_benefit", "benefit_internal_value"]
    extra = 0

    def has_add_permission(self, request, obj=None):
        has_add_permission = super().has_add_permission(request, obj=obj)
        match = request.resolver_match
        if match.url_name == "sponsors_sponsorship_change":
            sponsorship = self.parent_model.objects.get(pk=match.kwargs["object_id"])
            has_add_permission = has_add_permission and sponsorship.open_for_editing
        return has_add_permission

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.open_for_editing:
            return ["sponsorship_benefit", "benefit_internal_value"]
        return []

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.open_for_editing

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsorship_benefit__program", "program")


class TargetableEmailBenefitsFilter(admin.SimpleListFilter):
    title = "targetable email benefits"
    parameter_name = 'email_benefit'

    @cached_property
    def benefits(self):
        qs = EmailTargetableConfiguration.objects.all().values_list("benefit_id", flat=True)
        benefits = SponsorshipBenefit.objects.filter(id__in=Subquery(qs))
        return {str(b.id): b for b in benefits}

    def lookups(self, request, model_admin):
        return [
            (k, b.name) for k, b in self.benefits.items()
        ]

    def queryset(self, request, queryset):
        benefit = self.benefits.get(self.value())
        if not benefit:
            return queryset
        # all sponsors benefit related with such sponsorship benefit
        qs = SponsorBenefit.objects.filter(
            sponsorship_benefit_id=benefit.id).values_list("sponsorship_id", flat=True)
        return queryset.filter(id__in=Subquery(qs))


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    change_form_template = "sponsors/admin/sponsorship_change_form.html"
    form = SponsorshipReviewAdminForm
    inlines = [SponsorBenefitInline, AssetsInline]
    search_fields = ["sponsor__name"]
    list_display = [
        "sponsor",
        "status",
        "package",
        "applied_on",
        "approved_on",
        "start_date",
        "end_date",
    ]
    list_filter = ["status", "package", TargetableEmailBenefitsFilter]
    actions = ["send_notifications"]
    fieldsets = [
        (
            "Sponsorship Data",
            {
                "fields": (
                    "for_modified_package",
                    "sponsor",
                    "status",
                    "package",
                    "sponsorship_fee",
                    "get_estimated_cost",
                    "start_date",
                    "end_date",
                    "get_contract",
                    "level_name",
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
        fieldsets = []
        for title, cfg in super().get_fieldsets(request, obj):
            # disable collapse option in case of sponsorships with customizations
            if title == "User Customizations" and obj:
                if obj.user_customizations["added_by_user"] or obj.user_customizations["removed_by_user"]:
                    cfg["classes"] = []
            fieldsets.append((title, cfg))
        return fieldsets

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsor", "package", "submited_by")

    def send_notifications(self, request, queryset):
        return views_admin.send_sponsorship_notifications_action(self, request, queryset)

    send_notifications.short_description = 'Send notifications to selected'

    def get_readonly_fields(self, request, obj):
        readonly_fields = [
            "for_modified_package",
            "sponsor",
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

        if obj and obj.status != Sponsorship.APPLIED:
            extra = ["start_date", "end_date", "package", "level_name", "sponsorship_fee"]
            readonly_fields.extend(extra)

        return readonly_fields

    def get_estimated_cost(self, obj):
        cost = None
        html = "This sponsorship has not customizations so there's no estimated cost"
        if obj.for_modified_package:
            msg = "This sponsorship has customizations and this cost is a sum of all benefit's internal values from when this sponsorship was created"
            cost = intcomma(obj.estimated_cost)
            html = f"{cost} USD <br/><b>Important: </b> {msg}"
        return mark_safe(html)

    get_estimated_cost.short_description = "Estimated cost"

    def get_contract(self, obj):
        if not obj.contract:
            return "---"
        url = reverse("admin:sponsors_contract_change", args=[obj.contract.pk])
        html = f"<a href='{url}' target='_blank'>{obj.contract}</a>"
        return mark_safe(html)

    get_contract.short_description = "Contract"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/reject",
                # TODO: maybe it would be better to create a specific
                # group or permission to review sponsorship applications
                self.admin_site.admin_view(self.reject_sponsorship_view),
                name="sponsors_sponsorship_reject",
            ),
            path(
                "<int:pk>/approve-existing",
                self.admin_site.admin_view(self.approve_signed_sponsorship_view),
                name="sponsors_sponsorship_approve_existing_contract",
            ),
            path(
                "<int:pk>/approve",
                self.admin_site.admin_view(self.approve_sponsorship_view),
                name="sponsors_sponsorship_approve",
            ),
            path(
                "<int:pk>/enable-edit",
                self.admin_site.admin_view(self.rollback_to_editing_view),
                name="sponsors_sponsorship_rollback_to_edit",
            ),
            path(
                "<int:pk>/list-assets",
                self.admin_site.admin_view(self.list_uploaded_assets_view),
                name="sponsors_sponsorship_list_uploaded_assets",
            ),
        ]
        return my_urls + urls

    def get_sponsor_name(self, obj):
        return obj.sponsor.name

    get_sponsor_name.short_description = "Name"

    def get_sponsor_description(self, obj):
        return obj.sponsor.description

    get_sponsor_description.short_description = "Description"

    def get_sponsor_landing_page_url(self, obj):
        return obj.sponsor.landing_page_url

    get_sponsor_landing_page_url.short_description = "Landing Page URL"

    def get_sponsor_web_logo(self, obj):
        html = "{% load thumbnail %}{% thumbnail sponsor.web_logo '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
        template = Template(html)
        context = Context({'sponsor': obj.sponsor})
        html = template.render(context)
        return mark_safe(html)

    get_sponsor_web_logo.short_description = "Web Logo"

    def get_sponsor_print_logo(self, obj):
        img = obj.sponsor.print_logo
        html = ""
        if img:
            html = "{% load thumbnail %}{% thumbnail img '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
            template = Template(html)
            context = Context({'img': img})
            html = template.render(context)
        return mark_safe(html) if html else "---"

    get_sponsor_print_logo.short_description = "Print Logo"

    def get_sponsor_primary_phone(self, obj):
        return obj.sponsor.primary_phone

    get_sponsor_primary_phone.short_description = "Primary Phone"

    def get_sponsor_mailing_address(self, obj):
        sponsor = obj.sponsor
        city_row = (
            f"{sponsor.city} - {sponsor.get_country_display()} ({sponsor.country})"
        )
        if sponsor.state:
            city_row = f"{sponsor.city} - {sponsor.state} - {sponsor.get_country_display()} ({sponsor.country})"

        mail_row = sponsor.mailing_address_line_1
        if sponsor.mailing_address_line_2:
            mail_row += f" - {sponsor.mailing_address_line_2}"

        html = f"<p>{city_row}</p>"
        html += f"<p>{mail_row}</p>"
        html += f"<p>{sponsor.postal_code}</p>"
        return mark_safe(html)

    get_sponsor_mailing_address.short_description = "Mailing/Billing Address"

    def get_sponsor_contacts(self, obj):
        html = ""
        contacts = obj.sponsor.contacts.all()
        primary = [c for c in contacts if c.primary]
        not_primary = [c for c in contacts if not c.primary]
        if primary:
            html = "<b>Primary contacts</b><ul>"
            html += "".join(
                [f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in primary]
            )
            html += "</ul>"
        if not_primary:
            html += "<b>Other contacts</b><ul>"
            html += "".join(
                [f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in not_primary]
            )
            html += "</ul>"
        return mark_safe(html)

    get_sponsor_contacts.short_description = "Contacts"

    def get_custom_benefits_added_by_user(self, obj):
        benefits = obj.user_customizations["added_by_user"]
        if not benefits:
            return "---"

        html = "".join(
            [f"<p>{b}</p>" for b in benefits]
        )
        return mark_safe(html)

    get_custom_benefits_added_by_user.short_description = "Added by User"

    def get_custom_benefits_removed_by_user(self, obj):
        benefits = obj.user_customizations["removed_by_user"]
        if not benefits:
            return "---"

        html = "".join(
            [f"<p>{b}</p>" for b in benefits]
        )
        return mark_safe(html)

    get_custom_benefits_removed_by_user.short_description = "Removed by User"

    def rollback_to_editing_view(self, request, pk):
        return views_admin.rollback_to_editing_view(self, request, pk)

    def reject_sponsorship_view(self, request, pk):
        return views_admin.reject_sponsorship_view(self, request, pk)

    def approve_sponsorship_view(self, request, pk):
        return views_admin.approve_sponsorship_view(self, request, pk)

    def approve_signed_sponsorship_view(self, request, pk):
        return views_admin.approve_signed_sponsorship_view(self, request, pk)

    def list_uploaded_assets_view(self, request, pk):
        return views_admin.list_uploaded_assets(self, request, pk)


@admin.register(LegalClause)
class LegalClauseModelAdmin(OrderedModelAdmin):
    list_display = ["internal_name"]


@admin.register(Contract)
class ContractModelAdmin(admin.ModelAdmin):
    change_form_template = "sponsors/admin/contract_change_form.html"
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
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsorship__sponsor")

    def get_revision(self, obj):
        return obj.revision if obj.is_draft else "Final"

    get_revision.short_description = "Revision"

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

    def document_link(self, obj):
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

    document_link.short_description = "Contract document"

    def get_sponsorship_url(self, obj):
        if not obj.sponsorship:
            return "---"
        url = reverse("admin:sponsors_sponsorship_change", args=[obj.sponsorship.pk])
        html = f"<a href='{url}' target='_blank'>{obj.sponsorship}</a>"
        return mark_safe(html)

    get_sponsorship_url.short_description = "Sponsorship"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/preview",
                self.admin_site.admin_view(self.preview_contract_view),
                name="sponsors_contract_preview",
            ),
            path(
                "<int:pk>/send",
                self.admin_site.admin_view(self.send_contract_view),
                name="sponsors_contract_send",
            ),
            path(
                "<int:pk>/execute",
                self.admin_site.admin_view(self.execute_contract_view),
                name="sponsors_contract_execute",
            ),
            path(
                "<int:pk>/nullify",
                self.admin_site.admin_view(self.nullify_contract_view),
                name="sponsors_contract_nullify",
            ),
        ]
        return my_urls + urls

    def preview_contract_view(self, request, pk):
        return views_admin.preview_contract_view(self, request, pk)

    def send_contract_view(self, request, pk):
        return views_admin.send_contract_view(self, request, pk)

    def execute_contract_view(self, request, pk):
        return views_admin.execute_contract_view(self, request, pk)

    def nullify_contract_view(self, request, pk):
        return views_admin.nullify_contract_view(self, request, pk)


@admin.register(SponsorEmailNotificationTemplate)
class SponsorEmailNotificationTemplateAdmin(BaseEmailTemplateAdmin):
    pass


class AssetTypeListFilter(admin.SimpleListFilter):
    title = "Asset Type"
    parameter_name = 'type'

    @property
    def assets_types_mapping(self):
        return {asset_type.__name__: asset_type for asset_type in GenericAsset.all_asset_types()}

    def lookups(self, request, model_admin):
        return [(k, v._meta.verbose_name_plural) for k, v in self.assets_types_mapping.items()]

    def queryset(self, request, queryset):
        asset_type = self.assets_types_mapping.get(self.value())
        if not asset_type:
            return queryset
        return queryset.instance_of(asset_type)


class AssociatedBenefitListFilter(admin.SimpleListFilter):
    title = "From Benefit Which Requires Asset"
    parameter_name = 'from_benefit'

    @property
    def benefits_with_assets(self):
        qs = BenefitFeature.objects.required_assets().values_list("sponsor_benefit__sponsorship_benefit",
                                                                  flat=True).distinct()
        benefits = SponsorshipBenefit.objects.filter(id__in=Subquery(qs))
        return {str(b.id): b for b in benefits}

    def lookups(self, request, model_admin):
        return [(k, b.name) for k, b in self.benefits_with_assets.items()]

    def queryset(self, request, queryset):
        benefit = self.benefits_with_assets.get(self.value())
        if not benefit:
            return queryset
        internal_names = [
            cfg.internal_name
            for cfg in benefit.features_config.all()
            if hasattr(cfg, "internal_name")
        ]
        return queryset.filter(internal_name__in=internal_names)


@admin.register(GenericAsset)
class GenericAssetModelADmin(PolymorphicParentModelAdmin):
    list_display = ["id", "internal_name", "get_value", "content_object"]
    list_filter = [AssetTypeListFilter, AssociatedBenefitListFilter]

    def get_child_models(self, *args, **kwargs):
        return GenericAsset.all_asset_types()

    def get_queryset(self, *args, **kwargs):
        classes = self.get_child_models(*args, **kwargs)
        return self.model.objects.prefetch_related("content_object").instance_of(*classes)

    def get_value(self, obj):
        html = obj.value
        if obj.value and getattr(obj.value, "url", None):
            html = f"<a href='{obj.value.url}' target='_blank'>{obj.value}</a>"
        return mark_safe(html)

    get_value.short_description = "Value"

    def has_delete_permission(self, *args, **kwargs):
        return False


class GenericAssetChildModelAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all GenericAsset child models """
    base_model = GenericAsset
    readonly_fields = ["uuid", "content_type", "object_id", "content_object", "internal_name"]


@admin.register(TextAsset)
class TextAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = TextAsset


@admin.register(ImgAsset)
class TextAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = ImgAsset
