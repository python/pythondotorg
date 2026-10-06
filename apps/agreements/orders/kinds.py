"""Offer configured orders through the shared signing workflow."""

from copy import deepcopy

from django.core.exceptions import ValidationError

from apps.agreements.models import Order, Program
from apps.agreements.orders.documents import compose_order_form_markdown
from apps.agreements.registry import Kind, register


@register
class OrderKind(Kind):
    """Freeze configuration and fees for a customer's selected agreements."""

    slug = "order"
    name = "Order Form"
    model = Order

    def details(self, subject):
        """Use the configured document title and the customer's signatory account."""
        return {
            "title": subject.catalog.order_title,
            "counterparty_name": subject.legal_name,
            "counterparty_account": subject.customer_account,
        }

    def cited_terms_versions(self, subject):
        """Use exactly the terms versions resolved while composing this offer."""
        return [line.cited_terms for line in subject.agreement_list]

    def freeze(self, subject):
        """Pin the catalog and all fee schedules before generating the signed document."""
        program = Program.objects.select_for_update().get(pk=subject.program_id)
        subject.catalog_snapshot = deepcopy(program.definition)
        subject.program_title_snapshot = program.title
        subject.__dict__.pop("catalog", None)
        subject.save(update_fields=["catalog_snapshot", "program_title_snapshot"])
        lines = subject.agreement_list
        if not lines:
            msg = "Choose at least one agreement before offering this order."
            raise ValidationError(msg)
        for line in lines:
            if line.agreement not in subject.catalog.agreements:
                msg = "The available selections changed. Edit this draft before offering it."
                raise ValidationError(msg)
            if line.cited_terms is None:
                msg = "Publish a terms version for every selected agreement before offering this order."
                raise ValidationError(msg)
            line.pricing = line.quote().as_dict()
            line.save(update_fields=["pricing"])

    def release(self, subject):
        """Use current configuration again after withdrawing an unsigned offer."""
        subject.agreements.update(pricing={})
        subject.catalog_snapshot = {}
        subject.program_title_snapshot = ""
        subject.save(update_fields=["catalog_snapshot", "program_title_snapshot"])

    def compose(self, subject):
        """Compose the order from its selected agreements."""
        return compose_order_form_markdown(subject)

    def can_view(self, user, agreement):
        """Use the order's group and linked-customer access rules."""
        order = self.subject(agreement)
        return order is not None and order.can_view(user)
