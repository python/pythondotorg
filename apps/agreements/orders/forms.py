"""Catalog-driven order forms; signature forms are shared with all agreements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.agreements.forms.accounts import account_for_email
from apps.agreements.models import Order, OrderLine
from apps.agreements.orders.pricing import normalize_params

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.forms import BoundField
    from django.http import QueryDict

    from apps.agreements.models import Program
    from apps.agreements.orders.catalog import Agreement, Catalog, Param
    from apps.agreements.orders.pricing import ParamValue
    from apps.users.models import User

MAX_CONTACTS = 5
MAX_ENTITIES = 50
MAX_NAME_LENGTH = 100


def _lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


class OrderForm(forms.ModelForm):
    """Customer details, contacts, discount eligibility, and selected agreements."""

    instance: Order

    agreements = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "Choose at least one service package."},
    )
    discount = forms.ChoiceField(widget=forms.RadioSelect)
    discount_attestation = forms.BooleanField(required=False)

    class Meta:
        """Expose customer fields; configure selection fields from the catalog."""

        model = Order
        fields = (
            "legal_name",
            "jurisdiction",
            "entity_type",
            "address",
            "covered_entities",
            "discount",
            "billing_contact_name",
            "billing_contact_email",
            "notices_contact",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "covered_entities": forms.Textarea(attrs={"rows": 3, "spellcheck": "false"}),
            "notices_contact": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(
        self,
        *args: Any,
        catalog: Catalog,
        agreements: dict[str, Agreement],
        can_link_accounts: bool = False,
        **kwargs: Any,
    ) -> None:
        """Configure available selections, account linkage and contact rows."""
        super().__init__(*args, **kwargs)
        self.catalog = catalog
        cast("forms.MultipleChoiceField", self.fields["agreements"]).choices = [
            (a.slug, a.short_name) for a in agreements.values()
        ]
        cast("forms.ChoiceField", self.fields["discount"]).choices = [(d.key, d.name) for d in catalog.discounts]
        self.fields["covered_entities"].label = catalog.covered_entities_label
        self.fields["covered_entities"].help_text = catalog.covered_entities_help
        self.fields["discount_attestation"].label = catalog.attestation_label
        self.fields["discount_attestation"].help_text = catalog.attestation_help
        order = self.instance
        editing = not order._state.adding  # noqa: SLF001 - Django model state API
        if can_link_accounts:
            account = order.customer_account
            self.fields["customer_account_email"] = forms.EmailField(
                required=False,
                label="Customer's python.org account",
                help_text="Email of the account that may view and sign this order online. "
                "Leave empty to collect the signature outside python.org.",
                initial=account.email if account else "",
            )
        if editing:
            self.initial["agreements"] = [
                line.agreement for line in order.agreement_list if line.agreement in agreements
            ]
            self.fields["discount_attestation"].initial = any(
                discount.key == order.discount and discount.requires_attestation for discount in catalog.discounts
            )
        else:
            self.initial["discount"] = catalog.discounts[0].key
        existing = order.authorized_contacts if editing else []
        for i in range(1, MAX_CONTACTS + 1):
            contact = existing[i - 1] if i <= len(existing) else {}
            self.fields[f"contact_{i}_name"] = forms.CharField(
                required=False, max_length=255, label="Name", initial=contact.get("name")
            )
            self.fields[f"contact_{i}_email"] = forms.EmailField(
                required=False, label="Email", initial=contact.get("email")
            )

    def contact_rows(self) -> list[tuple[BoundField, BoundField]]:
        """Pair each contact's fields for the template."""
        return [(self[f"contact_{i}_name"], self[f"contact_{i}_email"]) for i in range(1, MAX_CONTACTS + 1)]

    def clean_covered_entities(self) -> str:
        """Require a bounded list of covered entities."""
        entities = _lines(self.cleaned_data["covered_entities"])
        if not entities:
            msg = "List at least one covered entity."
            raise ValidationError(msg)
        if len(entities) > MAX_ENTITIES:
            msg = f"List at most {MAX_ENTITIES} covered entities."
            raise ValidationError(msg)
        if any(len(entity) > MAX_NAME_LENGTH for entity in entities):
            msg = f"Enter one name per line; names are at most {MAX_NAME_LENGTH} characters."
            raise ValidationError(msg)
        return "\n".join(entities)

    def _clean_contacts(self) -> list[dict[str, str]]:
        contacts: list[dict[str, str]] = []
        incomplete = False
        for i in range(1, MAX_CONTACTS + 1):
            name = (self.cleaned_data.get(f"contact_{i}_name") or "").strip()
            email = self.cleaned_data.get(f"contact_{i}_email") or ""
            if name and email:
                contacts.append({"name": name, "email": email})
            elif name or email:
                incomplete = True
                missing = f"contact_{i}_email" if name else f"contact_{i}_name"
                self.add_error(missing, "Enter both a name and an email address for this contact.")
        if not contacts and not incomplete:
            self.add_error("contact_1_name", "Add at least one authorized contact.")
        return contacts

    def clean_customer_account_email(self) -> User | None:
        """Resolve the supplied address to one customer account."""
        email = self.cleaned_data["customer_account_email"]
        return account_for_email(email) if email else None

    def clean(self) -> dict[str, Any]:
        """Validate discount eligibility and authorized contacts."""
        cleaned = cast("dict[str, Any]", super().clean())
        discount = cleaned.get("discount")
        if (
            discount
            and self.catalog.discount(discount).requires_attestation
            and not cleaned.get("discount_attestation")
        ):
            self.add_error("discount_attestation", "Confirm eligibility to use the selected discount.")
        cleaned["contacts"] = self._clean_contacts()
        return cleaned


class AgreementForm(forms.Form):
    """Tier and add-on selections generated from one catalog agreement."""

    tier = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(
        self,
        *args: Any,
        agreement: Agreement,
        line: OrderLine | None = None,
        staff: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create configured fields and identify inactive conditional parameters."""
        cast("Callable[..., None]", super().__init__)(*args, prefix=agreement.slug, **kwargs)
        self.agreement = agreement
        cast("forms.ChoiceField", self.fields["tier"]).choices = [(t.key, t.name) for t in agreement.tiers]
        self.initial["tier"] = line.tier if line else agreement.default_tier
        if staff:
            self.fields["special_terms"] = forms.CharField(
                required=False,
                max_length=2000,
                widget=forms.Textarea(attrs={"rows": 2}),
                help_text="Printed on the Order Form for this agreement. Leave empty for none.",
                initial=line.special_terms if line else "",
            )
        selected = line.addons if line else {}
        tier = self.data.get(self.add_prefix("tier")) if self.is_bound else self.initial["tier"]
        self._inactive_parameters: list[forms.Field] = []
        for addon in agreement.addons:
            chosen = selected.get(addon.key)
            name = f"addon_{addon.key}"
            self.fields[name] = forms.BooleanField(required=False, label=addon.name, initial=chosen is not None)
            active = bool(self.data.get(self.add_prefix(name))) and tier not in addon.included_in_tiers
            for param in addon.params:
                field = self._param_field(param, (chosen or {}).get(param.key))
                if self.is_bound and (
                    not active
                    or not all(
                        self.data.get(self.add_prefix(f"{name}_{key}")) == str(value)
                        for key, value in param.required_when.items()
                    )
                ):
                    self._inactive_parameters.append(field)
                self.fields[f"{name}_{param.key}"] = field

    def full_clean(self) -> None:
        """Ignore inactive values when validating, but keep rendered inputs editable."""
        for field in self._inactive_parameters:
            field.disabled = True
        try:
            super().full_clean()
        finally:
            for field in self._inactive_parameters:
                field.disabled = False

    @staticmethod
    def _param_field(param: Param, initial: ParamValue | None) -> forms.Field:
        field: forms.Field
        if param.kind == "choice":
            field = forms.ChoiceField(choices=param.choices, required=False, initial=initial or param.choices[0][0])
        elif param.kind == "count":
            field = forms.IntegerField(required=False, min_value=param.minimum, initial=initial)
        elif param.kind == "lines":
            field = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 3}),
                initial="\n".join(cast("list[str]", initial) or []),
            )
        else:
            field = forms.CharField(required=False, max_length=200, initial=initial)
        field.label, field.help_text = param.label, param.help_text
        field.widget.attrs["data-param-key"] = param.key
        return field

    def tier_options(self) -> list[dict[str, Any]]:
        """Pair every tier with the services and extras its fee includes."""
        return [
            {
                "tier": tier,
                "services": self.agreement.services_at(tier.key),
                "included_addons": [addon for addon in self.agreement.addons if tier.key in addon.included_in_tiers],
            }
            for tier in self.agreement.tiers
        ]

    def has_included_extras(self) -> bool:
        """Show the comparison row only when a tier includes something extra."""
        return any(tier.includes for tier in self.agreement.tiers) or any(
            addon.included_in_tiers for addon in self.agreement.addons
        )

    def addon_fields(self) -> list[dict[str, Any]]:
        """Pair each add-on with its checkbox and parameter fields."""
        return [
            {
                "addon": addon,
                "checkbox": self[f"addon_{addon.key}"],
                "params": [self[f"addon_{addon.key}_{p.key}"] for p in addon.params],
            }
            for addon in self.agreement.addons
        ]

    def clean(self) -> dict[str, Any]:
        """Reject unknown selections and normalize active add-on parameters."""
        cleaned = cast("dict[str, Any]", super().clean())
        tier = cleaned.get("tier")
        addons: dict[str, dict[str, ParamValue]] = {}
        known = {self.add_prefix(name) for name in self.fields}
        for name in self.data:
            if name.startswith(self.add_prefix("addon_")) and name not in known:
                self.add_error(None, "Unknown additional service or parameter.")
        for addon in self.agreement.addons:
            name = f"addon_{addon.key}"
            if not cleaned.get(name) or tier in addon.included_in_tiers:
                continue
            params = {
                param.key: cleaned.get(f"{name}_{param.key}")
                for param in addon.params
                if not self.fields[f"{name}_{param.key}"].disabled
            }
            if any(f"{name}_{param.key}" in self.errors for param in addon.params):
                continue
            try:
                addons[addon.key] = normalize_params(addon, params)
            except ValidationError as exc:
                self.add_error(name, ValidationError(exc.messages))
        cleaned["addons"] = addons
        return cleaned


class OrderBuilder:
    """An order form and one form for each available agreement."""

    def __init__(
        self,
        data: QueryDict | None = None,
        *,
        program: Program,
        order: Order | None = None,
        staff: bool = False,
        can_link_accounts: bool = False,
    ) -> None:
        """Restrict the builder to the program and any private-order scope."""
        self.order, self.program, self.staff = order, program, staff
        self.can_link_accounts = can_link_accounts
        self.catalog = order.catalog if order else program.catalog
        lines = {line.agreement: line for line in order.agreement_list} if order else {}
        self.agreements = {
            slug: agreement
            for slug, agreement in self.catalog.agreements.items()
            if not order or program.is_public or staff or slug in lines
        }
        self.order_form = OrderForm(
            data,
            instance=order,
            catalog=self.catalog,
            agreements=self.agreements,
            can_link_accounts=can_link_accounts,
        )
        self.agreement_forms = {
            slug: AgreementForm(data, agreement=agreement, line=lines.get(slug), staff=staff)
            for slug, agreement in self.agreements.items()
        }

    @property
    def chosen(self) -> list[str]:
        """Return only available, selected agreement slugs."""
        if self.order_form.is_bound:
            return [
                slug
                for slug in self.agreements
                if slug in cast("QueryDict", self.order_form.data).getlist("agreements")
            ]
        return list(self.order_form.initial.get("agreements", []))

    @property
    def parameter_conditions(self) -> dict[str, dict[str, dict[str, dict[str, ParamValue]]]]:
        """Declarative field visibility rules for the live builder."""
        return {
            slug: {
                addon.key: {param.key: param.required_when for param in addon.params if param.required_when}
                for addon in agreement.addons
            }
            for slug, agreement in self.agreements.items()
        }

    def is_valid(self) -> bool:
        """Validate customer details and every selected agreement."""
        forms_to_check = [self.order_form, *(self.agreement_forms[slug] for slug in self.chosen)]
        return all([form.is_valid() for form in forms_to_check])  # noqa: C419 - collect every form's errors

    @property
    def has_errors(self) -> bool:
        """Report errors from customer details or selected agreements."""
        return bool(self.order_form.errors) or any(self.agreement_forms[slug].errors for slug in self.chosen)

    @transaction.atomic
    def save(self, user: User) -> Order:
        """Persist the draft and selected lines atomically."""
        order = cast("Order", self.order_form.save(commit=False))
        order.program = self.program
        if order.created_by_id is None:
            order.created_by = user
        if self.can_link_accounts:
            order.customer_account = self.order_form.cleaned_data["customer_account_email"]
        elif not self.staff and order._state.adding:  # noqa: SLF001 - Django model state API
            order.customer_account = user
        order.authorized_contacts = self.order_form.cleaned_data["contacts"]
        order.save()
        chosen = self.order_form.cleaned_data["agreements"]
        order.agreements.exclude(agreement__in=chosen).delete()
        for slug in chosen:
            data = self.agreement_forms[slug].cleaned_data
            defaults = {"tier": data["tier"], "addons": data["addons"]}
            if self.staff:
                defaults["special_terms"] = data["special_terms"].strip()
            OrderLine.objects.update_or_create(order=order, agreement=slug, defaults=defaults)
        return order
