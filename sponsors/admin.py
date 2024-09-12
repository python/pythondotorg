from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from ordered_model.admin import OrderedModelAdmin
from polymorphic.admin import PolymorphicInlineSupportMixin, StackedPolymorphicInline, PolymorphicParentModelAdmin, \
    PolymorphicChildModelAdmin

from django.db.models import Subquery
from django.template import Context, Template
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.forms import ModelForm
from django.urls import path, reverse, resolve
from django.utils.functional import cached_property
from django.utils.html import mark_safe

from import_export import resources
from import_export.fields import Field
from import_export.admin import ImportExportActionModelAdmin

from mailing.admin import BaseEmailTemplateAdmin
from sponsors.models import *
from sponsors.models.benefits import RequiredAssetMixin
from sponsors import views_admin
from sponsors.forms import SponsorshipReviewAdminForm, SponsorBenefitAdminInlineForm, RequiredImgAssetConfigurationForm, \
    SponsorshipBenefitAdminForm, CloneApplicationConfigForm
from cms.admin import ContentManageableModelAdmin


def get_url_base_name(Model):
    return f"{Model._meta.app_label}_{Model._meta.model_name}"


class AssetsInline(GenericTabularInline):
    model = GenericAsset
    extra = 0
    max_num = 0
    has_delete_permission = lambda self, request, obj: False
    readonly_fields = ["internal_name", "user_submitted_info", "value"]

    @admin.display(
        description="Submitted information"
    )
    def value(self, obj=None):
        if not obj or not obj.value:
            return ""
        return obj.value


    @admin.display(
        description="Fullfilled data?",
        boolean=True,
    )
    def user_submitted_info(self, obj=None):
        return bool(self.value(obj))



@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = [
        "name",
        "move_up_down_links",
    ]


class MultiPartForceForm(ModelForm):
    def is_multipart(self):
        return True


class BenefitFeatureConfigurationInline(StackedPolymorphicInline):
    form = MultiPartForceForm

    class LogoPlacementConfigurationInline(StackedPolymorphicInline.Child):
        model = LogoPlacementConfiguration

    class TieredBenefitConfigurationInline(StackedPolymorphicInline.Child):
        model = TieredBenefitConfiguration

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

    class RequiredResponseAssetConfigurationInline(StackedPolymorphicInline.Child):
        model = RequiredResponseAssetConfiguration

    class ProvidedTextAssetConfigurationInline(StackedPolymorphicInline.Child):
        model = ProvidedTextAssetConfiguration

    class ProvidedFileAssetConfigurationInline(StackedPolymorphicInline.Child):
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
        return views_admin.update_related_sponsorships(self, *args, **kwargs)


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(OrderedModelAdmin):
    ordering = ("-year", "order",)
    list_display = ["name", "year", "advertise", "allow_a_la_carte", "get_benefit_split", "move_up_down_links"]
    list_filter = ["advertise", "year", "allow_a_la_carte"]
    search_fields = ["name"]

    def get_readonly_fields(self, request, obj=None):
        readonly = ["get_benefit_split"]
        if obj:
            readonly.append("slug")
        if not request.user.is_superuser:
            readonly.append("logo_dimension")
        return readonly

    def get_prepopulated_fields(self, request, obj=None):
        if not obj:
            return {'slug': ['name']}
        return {}

    def get_benefit_split(self, obj: SponsorshipPackage) -> str:
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
        style = f'color:#fff;text-align:center;cursor:pointer;display:grid;grid-template-columns:{" ".join(widths)}'
        # wrap it all up and put a bow on it
        html = f"<div style='{style}'>{''.join(spans)}</div>"
        return mark_safe(html)

    get_benefit_split.short_description = "Revenue split"


class SponsorContactInline(admin.TabularInline):
    model = SponsorContact
    raw_id_fields = ["user"]
    extra = 0


class SponsorshipsInline(admin.TabularInline):
    model = Sponsorship
    fields = ["link", "status", "year", "applied_on", "start_date", "end_date"]
    readonly_fields = ["link", "status", "year", "applied_on", "start_date", "end_date"]
    can_delete = False
    extra = 0

    @admin.display(
        description="ID"
    )
    def link(self, obj):
        url = reverse("admin:sponsors_sponsorship_change", args=[obj.id])
        return mark_safe(f"<a href={url}>{obj.id}</a>")


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    inlines = [SponsorContactInline, SponsorshipsInline, AssetsInline]
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

    def get_queryset(self, request):
        #filters the available benefits by the benefits for the year of the sponsorship
        match = request.resolver_match
        sponsorship = self.parent_model.objects.get(pk=match.kwargs["object_id"])
        year = sponsorship.year

        return super().get_queryset(request).filter(sponsorship_benefit__year=year)


class TargetableEmailBenefitsFilter(admin.SimpleListFilter):
    title = "targetable email benefits"
    parameter_name = 'email_benefit'

    @cached_property
    def benefits(self):
        qs = EmailTargetableConfiguration.objects.all().values_list("benefit_id", flat=True)
        benefits = SponsorshipBenefit.objects.filter(id__in=Subquery(qs), year=SponsorshipCurrentYear.get_year())
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


class SponsorshipStatusListFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return Sponsorship.STATUS_CHOICES

    def queryset(self, request, queryset):
        status = self.value()
        # exclude rejected ones by default
        if not status:
            return queryset.exclude(status=Sponsorship.REJECTED)
        return queryset.filter(status=status)

    def choices(self, changelist):
        choices = list(super().choices(changelist))
        # replaces django default "All" text by a custom text
        choices[0]['display'] = "Applied / Approved / Finalized"
        return choices


class SponsorshipResource(resources.ModelResource):

    sponsor_name = Field(attribute='sponsor__name', column_name='Company Name')
    contact_name = Field(column_name='Contact Name(s)')
    contact_email = Field(column_name='Contact Email(s)')
    contact_phone = Field(column_name='Contact phone number')
    contact_type = Field(column_name='Contact Type(s)')
    start_date = Field(attribute='start_date', column_name='Start Date')
    end_date = Field(attribute='end_date', column_name='End Date')
    web_logo = Field(column_name='Logo')
    landing_page_url = Field(attribute='sponsor__landing_page_url', column_name='Webpage link')
    level = Field(attribute='package__name', column_name='Sponsorship Level')
    cost = Field(attribute='sponsorship_fee', column_name='Sponsorship Cost')
    admin_url = Field(attribute='admin_url', column_name='Admin Link')

    class Meta:
        model = Sponsorship
        fields = (
            'sponsor_name',
            'contact_name',
            'contact_email',
            'contact_phone',
            'contact_type',
            'start_date',
            'end_date',
            'web_logo',
            'landing_page_url',
            'level',
            'cost',
            'admin_url',
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
        domain = Site.objects.get_current().domain
        url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.id])
        return f'https://{domain}{url}'

    def dehydrate_web_logo(self, sponsorship):
        return sponsorship.sponsor.web_logo.url

    def dehydrate_contact_type(self, sponsorship):
        return "\n".join([contact.type for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_name(self, sponsorship):
        return "\n".join([contact.name for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_email(self, sponsorship):
        return "\n".join([contact.email for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_contact_phone(self, sponsorship):
        return "\n".join([contact.phone for contact in sponsorship.sponsor.contacts.all()])

    def dehydrate_admin_url(self, sponsorship):
        return self.get_sponsorship_url(sponsorship)


@admin.register(Sponsorship)
class SponsorshipAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
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

    @admin.action(
        description='Send notifications to selected'
    )
    def send_notifications(self, request, queryset):
        return views_admin.send_sponsorship_notifications_action(self, request, queryset)


    def get_readonly_fields(self, request, obj):
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

    @admin.display(
        description="Sponsor"
    )
    def sponsor_link(self, obj):
        url = reverse("admin:sponsors_sponsor_change", args=[obj.sponsor.id])
        return mark_safe(f"<a href={url}>{obj.sponsor.name}</a>")

    @admin.display(
        description="Estimated cost"
    )
    def get_estimated_cost(self, obj):
        cost = None
        html = "This sponsorship has not customizations so there's no estimated cost"
        if obj.for_modified_package:
            msg = "This sponsorship has customizations and this cost is a sum of all benefit's internal values from when this sponsorship was created"
            cost = intcomma(obj.estimated_cost)
            html = f"{cost} USD <br/><b>Important: </b> {msg}"
        return mark_safe(html)


    @admin.display(
        description="Contract"
    )
    def get_contract(self, obj):
        if not obj.contract:
            return "---"
        url = reverse("admin:sponsors_contract_change", args=[obj.contract.pk])
        html = f"<a href='{url}' target='_blank'>{obj.contract}</a>"
        return mark_safe(html)


    def get_urls(self):
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

    @admin.display(
        description="Name"
    )
    def get_sponsor_name(self, obj):
        return obj.sponsor.name


    @admin.display(
        description="Description"
    )
    def get_sponsor_description(self, obj):
        return obj.sponsor.description


    @admin.display(
        description="Landing Page URL"
    )
    def get_sponsor_landing_page_url(self, obj):
        return obj.sponsor.landing_page_url


    @admin.display(
        description="Web Logo"
    )
    def get_sponsor_web_logo(self, obj):
        html = "{% load thumbnail %}{% thumbnail sponsor.web_logo '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
        template = Template(html)
        context = Context({'sponsor': obj.sponsor})
        html = template.render(context)
        return mark_safe(html)


    @admin.display(
        description="Print Logo"
    )
    def get_sponsor_print_logo(self, obj):
        img = obj.sponsor.print_logo
        html = ""
        if img:
            html = "{% load thumbnail %}{% thumbnail img '150x150' format='PNG' quality=100 as im %}<img src='{{ im.url}}'/>{% endthumbnail %}"
            template = Template(html)
            context = Context({'img': img})
            html = template.render(context)
        return mark_safe(html) if html else "---"


    @admin.display(
        description="Primary Phone"
    )
    def get_sponsor_primary_phone(self, obj):
        return obj.sponsor.primary_phone


    @admin.display(
        description="Mailing/Billing Address"
    )
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


    @admin.display(
        description="Contacts"
    )
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


    @admin.display(
        description="Added by User"
    )
    def get_custom_benefits_added_by_user(self, obj):
        benefits = obj.user_customizations["added_by_user"]
        if not benefits:
            return "---"

        html = "".join(
            [f"<p>{b}</p>" for b in benefits]
        )
        return mark_safe(html)


    @admin.display(
        description="Removed by User"
    )
    def get_custom_benefits_removed_by_user(self, obj):
        benefits = obj.user_customizations["removed_by_user"]
        if not benefits:
            return "---"

        html = "".join(
            [f"<p>{b}</p>" for b in benefits]
        )
        return mark_safe(html)


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

    def unlock_view(self, request, pk):
        return views_admin.unlock_view(self, request, pk)

    def lock_view(self, request, pk):
        return views_admin.lock_view(self, request, pk)


@admin.register(SponsorshipCurrentYear)
class SponsorshipCurrentYearAdmin(admin.ModelAdmin):
    list_display = ["year", "links", "other_years"]
    change_list_template = "sponsors/admin/sponsors_sponsorshipcurrentyear_changelist.html"

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def get_urls(self):
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

    @admin.display(
        description="Links"
    )
    def links(self, obj):
        clone_form = CloneApplicationConfigForm()
        configured_years = clone_form.configured_years

        application_url = reverse("select_sponsorship_application_benefits")
        benefits_url = reverse("admin:sponsors_sponsorshipbenefit_changelist")
        packages_url = reverse("admin:sponsors_sponsorshippackage_changelist")
        preview_label = 'View sponsorship application'
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

    @admin.display(
        description="Other configured years"
    )
    def other_years(self, obj):
        clone_form = CloneApplicationConfigForm()
        configured_years = clone_form.configured_years
        try:
            configured_years.remove(obj.year)
        except ValueError:
            pass
        if not configured_years:
            return "---"

        application_url = reverse("select_sponsorship_application_benefits")
        benefits_url = reverse("admin:sponsors_sponsorshipbenefit_changelist")
        packages_url = reverse("admin:sponsors_sponsorshippackage_changelist")
        preview_label = 'View sponsorship application form for this year'
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
        return views_admin.clone_application_config(self, request)

@admin.register(LegalClause)
class LegalClauseModelAdmin(OrderedModelAdmin):
    list_display = ["internal_name"]


@admin.register(Contract)
class ContractModelAdmin(admin.ModelAdmin):
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
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsorship__sponsor")

    @admin.display(
        description="Revision"
    )
    def get_revision(self, obj):
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

    @admin.display(
        description="Contract document"
    )
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


    @admin.display(
        description="Sponsorship"
    )
    def get_sponsorship_url(self, obj):
        if not obj.sponsorship:
            return "---"
        url = reverse("admin:sponsors_sponsorship_change", args=[obj.sponsorship.pk])
        html = f"<a href='{url}' target='_blank'>{obj.sponsorship}</a>"
        return mark_safe(html)


    def get_urls(self):
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
        return views_admin.preview_contract_view(self, request, pk)

    def send_contract_view(self, request, pk):
        return views_admin.send_contract_view(self, request, pk)

    def execute_contract_view(self, request, pk):
        return views_admin.execute_contract_view(self, request, pk)

    def nullify_contract_view(self, request, pk):
        return views_admin.nullify_contract_view(self, request, pk)


@admin.register(SponsorEmailNotificationTemplate)
class SponsorEmailNotificationTemplateAdmin(BaseEmailTemplateAdmin):

    def get_form(self, request, obj=None, **kwargs):
        help_texts = {
            "content": SPONSOR_TEMPLATE_HELP_TEXT,
        }
        kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)


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
        return [(k, f"{b.name} ({b.year})") for k, b in self.benefits_with_assets.items()]

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


class AssetContentTypeFilter(admin.SimpleListFilter):
    title = "Related Object"
    parameter_name = 'content_type'

    def lookups(self, request, model_admin):
        qs = ContentType.objects.filter(model__in=["sponsorship", "sponsor"])
        return [(c_type.pk, c_type.model.title()) for c_type in qs]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        return queryset.filter(content_type=value)


class AssetWithOrWithoutValueFilter(admin.SimpleListFilter):
    title = "Value"
    parameter_name = "value"

    def lookups(self, request, model_admin):
        return [
            ("with-value", "With value"),
            ("no-value", "Without value"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        with_value_id = [asset.pk for asset in queryset if asset.value]
        if value == "with-value":
            return queryset.filter(pk__in=with_value_id)
        else:
            return queryset.exclude(pk__in=with_value_id)


@admin.register(GenericAsset)
class GenericAssetModelAdmin(PolymorphicParentModelAdmin):
    list_display = ["id", "internal_name", "get_value", "content_type", "get_related_object"]
    list_filter = [AssetContentTypeFilter, AssetTypeListFilter, AssetWithOrWithoutValueFilter,
                   AssociatedBenefitListFilter]
    actions = ["export_assets_as_zipfile"]

    def get_child_models(self, *args, **kwargs):
        return GenericAsset.all_asset_types()

    def get_queryset(self, *args, **kwargs):
        return GenericAsset.objects.all_assets()

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_add_permission(self, *args, **kwargs):
        return False

    @cached_property
    def all_sponsors(self):
        qs = Sponsor.objects.all()
        return {sp.id: sp for sp in qs}

    @cached_property
    def all_sponsorships(self):
        qs = Sponsorship.objects.all().select_related("package", "sponsor")
        return {sp.id: sp for sp in qs}

    @admin.display(
        description="Value"
    )
    def get_value(self, obj):
        html = obj.value
        if obj.value and getattr(obj.value, "url", None):
            html = f"<a href='{obj.value.url}' target='_blank'>{obj.value}</a>"
        return mark_safe(html)


    @admin.display(
        description="Associated with"
    )
    def get_related_object(self, obj):
        """
        Returns the content_object as an URL and performs better because
        of sponsors and sponsorship cached properties
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


    @admin.action(
        description="Export selected"
    )
    def export_assets_as_zipfile(self, request, queryset):
        return views_admin.export_assets_as_zipfile(self, request, queryset)


class GenericAssetChildModelAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all GenericAsset child models """
    base_model = GenericAsset
    readonly_fields = ["uuid", "content_type", "object_id", "content_object", "internal_name"]


@admin.register(TextAsset)
class TextAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = TextAsset


@admin.register(ImgAsset)
class ImgAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = ImgAsset


@admin.register(FileAsset)
class ImgAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = FileAsset


@admin.register(ResponseAsset)
class ResponseAssetModelAdmin(GenericAssetChildModelAdmin):
    base_model = ResponseAsset
