"""Compose an Order Form from its program configuration and frozen selections."""

from django.core.exceptions import ValidationError
from num2words import num2words

from apps.agreements.documents import (
    EFFECTIVE_DATE,
    PROVIDER_PREAMBLE,
    SIGNATURES,
    amounts_table,
    final_markdown,
    md,
    preview_markdown,
    table,
)
from apps.agreements.orders.pricing import fee_totals, money

ONE_YEAR = 12


def _months(n):
    return f"{num2words(n).capitalize()} ({n}) months"


def _contact(name, email):
    return f"{md(name)} ({md(email)})"


def _customer_section(order):
    address = ", ".join(part.strip() for part in order.address.splitlines() if part.strip())
    contacts = "; ".join(_contact(c["name"], c["email"]) for c in order.authorized_contacts)
    notices = md(order.notices_contact) if order.notices_contact.strip() else "The principal place of business above."
    return table(
        ("Customer", ""),
        [
            ("Legal name", f"**{md(order.legal_name)}**"),
            ("Organized as", f"A {md(order.jurisdiction)} {md(order.entity_type)}"),
            ("Principal place of business", md(address)),
            (md(order.catalog.covered_entities_label), ", ".join(md(entity) for entity in order.organization_list)),
            ("Authorized contacts", contacts),
            ("Billing contact", _contact(order.billing_contact_name, order.billing_contact_email)),
            ("Notices contact", notices),
        ],
    )


def _term_section(order):
    first = order.agreement_list[0].pricing_snapshot
    payment = order.catalog.payment
    invoicing = payment["annual"] if first["term_months"] <= ONE_YEAR else payment["multi_year"]
    discount = (
        f"{md(first['discount_name'])} ({first['discount_percent']}%), applied to Service Tier fees only."
        if first["discount_percent"]
        else "None."
    )
    return table(
        ("Term and payment", ""),
        [
            ("Effective Date", EFFECTIVE_DATE),
            ("Initial Term", f"{_months(first['term_months'])}."),
            ("Renewal", md(payment["renewal"])),
            ("Discount", discount),
            ("Invoicing", md(invoicing)),
            ("Other charges", md(payment["other_charges"])),
        ],
    )


def _fee_rows(pricing):
    rows = [(f"Service Tier fee: {md(pricing['tier_name'])}", f"{md(pricing['display']['tier_fee'])} per year")]
    for item in pricing["items"]:
        label = md(item["name"]) + (f" — {md(item['detail'])}" if item["detail"] else "")
        amount = md(item["basis"]) if item["amount"] is None else f"{md(item['display'])} {md(item['basis'])}"
        rows.append((f"Additional service: {label}", amount))
    if pricing["discount_percent"]:
        rows.append((md(pricing["discount_name"]), f"less {md(pricing['display']['discount_amount'])}"))
    totals = fee_totals(pricing)
    rows.append(("**Annual fees**", f"**{money(totals['annual'])}**"))
    if totals["one_time"]:
        rows.append(("One-time fees", money(totals["one_time"])))
    if pricing["term_months"] > ONE_YEAR or any(not item["recurring"] for item in pricing["items"]):
        rows.append((f"Initial Term total ({pricing['term_months']} months)", md(pricing["display"]["term_total"])))
    return rows


def _parameter_rows(line):
    rows = []
    for addon in line.agreement_obj.addons:
        selected = line.addons.get(addon.key)
        if selected is None:
            continue
        for param in addon.params:
            if param.key not in selected:
                continue
            value = selected[param.key]
            if param.kind == "choice":
                value = dict(param.choices).get(value, value)
            elif param.kind == "lines":
                value = "; ".join(value)
            rows.append((f"{md(addon.name)} — {md(param.label)}", md(str(value))))
    return rows


def _agreement_section(line):
    agreement, terms = line.agreement_obj, line.cited_terms
    tier = agreement.tier(line.tier)
    targets = "; ".join(
        f"{severity}: {md(target)}"
        for severity, target in zip(("P1", "P2", "P3", "P4"), tier.response_targets, strict=True)
    )
    rows = [
        ("Service Tier", f"**{md(tier.name)}**"),
        ("Response time targets", targets),
        ("Fair-use threshold", f"{tier.fair_use} requests per year"),
        ("Included services", "; ".join(md(service.name) for service in agreement.services_at(line.tier)) or "None."),
        *_parameter_rows(line),
        ("Special terms", md(line.special_terms.strip()) if line.special_terms.strip() else "None."),
    ]
    return [
        f"## {md(agreement.short_name)}",
        "",
        f"Terms: **{md(terms.terms.title)}**, version {md(terms.version)}, published at <{terms.permanent_url}>.",
        "",
        *table((md(agreement.short_name), ""), rows),
        *amounts_table(("Fees", ""), _fee_rows(line.pricing_snapshot)),
    ]


def _total_section(order):
    rows = [(md(line.agreement_obj.short_name), money(line.fee_totals["annual"])) for line in order.agreement_list]
    rows.append(("**Total annual fees**", f"**{money(order.fee_totals['annual'])}**"))
    if order.fee_totals["one_time"]:
        rows.append(("Total one-time fees", money(order.fee_totals["one_time"])))
    if order.term_months > ONE_YEAR or any(
        not item["recurring"] for line in order.agreement_list for item in line.pricing_snapshot["items"]
    ):
        rows.append((f"Total for the Initial Term ({order.term_months} months)", md(order.term_total_display)))
    return ["## Order total", "", *amounts_table(("Agreement", "Fees"), rows)]


def compose_order_form_markdown(order):
    """Return the document to hash and freeze, with date and signature placeholders."""
    lines = order.agreement_list
    if not lines:
        msg = "Choose at least one agreement before preparing the Order Form."
        raise ValidationError(msg)
    header = [f"# {md(order.catalog.order_title)}", ""]
    if any(line.cited_terms.terms.under_review for line in lines):
        header += ["**DRAFT — For Attorney Review**", ""]
    header += [f"*Reference {order.reference}*", ""]
    agreements = " and ".join(md(line.agreement_obj.title) for line in lines)
    intro = (
        f"This Order Form is entered into between {PROVIDER_PREAMBLE}, and the Customer named below. "
        f"It orders {agreements}, under the terms cited for each agreement below."
    )
    parts = [*header, md(order.catalog.order_intro), "", intro, "", *_customer_section(order), *_term_section(order)]
    for line in lines:
        parts += _agreement_section(line)
    if len(lines) > 1:
        parts += _total_section(order)
    parts += [
        "## Signatures",
        "",
        "Each Party signs this Order Form, and so enters into each agreement ordered on it, as of the "
        "Effective Date: the date of the last signature below.",
        "",
        SIGNATURES,
        "",
    ]
    return "\n".join(parts)


def order_form_markdown(order):
    """Use the offered document after freezing, otherwise compose a draft preview."""
    if order.agreement:
        return final_markdown(order.agreement)
    return preview_markdown(compose_order_form_markdown(order), order.legal_name)
