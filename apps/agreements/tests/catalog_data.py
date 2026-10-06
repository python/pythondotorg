"""Fictional catalog data shared by agreement and order behavior tests."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from apps.agreements.models import Program


def _tier(key: str, name: str, fee: str, fair_use: int) -> dict[str, Any]:
    return {
        "key": key,
        "name": name,
        "annual_fee": fee,
        "response_targets": ["1 day", "2 days", "3 days", "4 days"],
        "fair_use": fair_use,
    }


def _fixed(amount: str, recurring: bool = True) -> dict[str, Any]:
    return {"type": "fixed", "amount": amount, "recurring": recurring}


def _quantity(parameter: str, amount: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": "quantity", "parameter": parameter, "unit_amount": amount, "recurring": False, **kwargs}


def _addon(
    key: str, name: str, pricing: dict[str, Any], params: list[dict[str, Any]] | None = None, **kwargs: Any
) -> dict[str, Any]:
    return {
        "key": key,
        "name": name,
        "description": f"Example {name.lower()} service.",
        "price_summary": "See the example fee schedule.",
        "pricing": pricing,
        "params": params or [],
        **kwargs,
    }


CATALOG_DATA: dict[str, Any] = {
    "order_title": "Example service order",
    "order_intro": "Select the example services for your organization.",
    "covered_entities_label": "Covered workspaces",
    "covered_entities_help": "Enter one workspace per line.",
    "attestation_label": "I confirm eligibility for the community discount.",
    "attestation_help": "Available to eligible community groups.",
    "payment": {
        "annual": "Example annual fees are payable in advance.",
        "multi_year": "Example fees for the initial term are payable in advance.",
        "renewal": "Renewal follows the example agreement terms.",
        "other_charges": "Other example charges are invoiced separately.",
    },
    "discounts": [
        {"key": "none", "name": "No discount", "percent": 0, "term_months": 12},
        {"key": "prepaid", "name": "Prepaid term", "percent": 12, "term_months": 36},
        {
            "key": "eligible",
            "name": "Community discount",
            "percent": 25,
            "term_months": 12,
            "requires_attestation": True,
        },
    ],
    "agreements": [
        {
            "slug": "studio",
            "title": "Example Studio Services",
            "short_name": "Studio",
            "tagline": "Example services for a shared studio.",
            "terms_slug": "studio-terms",
            "default_tier": "basic",
            "tiers": [
                _tier("basic", "Basic", "1200", 8),
                _tier("plus", "Plus", "2400", 16),
                _tier("max", "Max", "4800", 32),
            ],
            "services": [
                {"key": "access", "name": "Studio access", "description": "Access to shared studio resources."},
                {
                    "key": "planning",
                    "name": "Studio planning",
                    "description": "Scheduled planning assistance.",
                    "tiers": ["plus", "max"],
                },
            ],
            "addons": [],
        },
        {
            "slug": "workshop",
            "title": "Example Workshop Services",
            "short_name": "Workshop",
            "tagline": "Example services for collaborative workshops.",
            "terms_slug": "workshop-terms",
            "default_tier": "basic",
            "tiers": [
                _tier("basic", "Basic", "1800", 8),
                _tier("plus", "Plus", "3600", 16),
                _tier("max", "Max", "7200", 32),
            ],
            "services": [
                {"key": "materials", "name": "Workshop materials", "description": "Shared example materials."},
                {
                    "key": "planning",
                    "name": "Workshop planning",
                    "description": "Dedicated planning assistance.",
                    "tiers": ["max"],
                },
            ],
            "addons": [
                _addon("kit", "Resource kit", _fixed("135")),
                _addon("advisor", "Workshop advisor", _fixed("210"), included_in_tiers=["max"]),
                _addon(
                    "labels",
                    "Workspace labels",
                    _quantity("names", "7", recurring=True, base_amount="42", included=3),
                    [{"key": "names", "label": "Workspace names", "kind": "lines"}],
                ),
                _addon(
                    "batch",
                    "Batch preparation",
                    {
                        "type": "brackets",
                        "parameter": "units",
                        "recurring": False,
                        "bands": [{"up_to": 8, "amount": "95"}, {"up_to": 30, "amount": "185"}],
                        "overflow_basis": "Quoted separately above 30 units",
                    },
                    [{"key": "units", "label": "Units", "kind": "count"}],
                ),
                _addon(
                    "reports",
                    "Activity summaries",
                    {
                        "type": "choice",
                        "parameter": "mode",
                        "options": {
                            "periodic": _fixed("84"),
                            "single": _quantity("copies", "19"),
                        },
                    },
                    [
                        {
                            "key": "mode",
                            "label": "Delivery",
                            "kind": "choice",
                            "choices": [["periodic", "Periodic"], ["single", "Individual"]],
                        },
                        {"key": "copies", "label": "Copies", "kind": "count", "required_when": {"mode": "single"}},
                    ],
                ),
                _addon(
                    "sessions",
                    "Practice sessions",
                    _quantity("hours", "37.50"),
                    [{"key": "hours", "label": "Hours", "kind": "count"}],
                ),
                _addon(
                    "bundles",
                    "Material bundles",
                    {
                        "type": "sum",
                        "recurring": False,
                        "components": [_quantity("small", "23"), _quantity("large", "61")],
                    },
                    [
                        {"key": "small", "label": "Small bundles", "kind": "count", "minimum": 0},
                        {"key": "large", "label": "Large bundles", "kind": "count", "minimum": 0},
                    ],
                ),
                _addon(
                    "schedule",
                    "Custom schedule",
                    _fixed("315"),
                    [{"key": "window", "label": "Schedule", "kind": "text"}],
                ),
                _addon(
                    "custom",
                    "Custom project",
                    {
                        "type": "unpriced",
                        "recurring": False,
                        "basis": "Quoted separately",
                        "detail": "Scope agreed before work begins",
                    },
                ),
            ],
        },
    ],
}


def make_program(*, is_public: bool = True) -> Program:
    """Create a program and published terms; each caller gets independent JSON data."""
    from apps.agreements.models import Program, Terms, TermsVersion

    definition = deepcopy(CATALOG_DATA)
    for agreement in definition["agreements"]:
        terms, _ = Terms.objects.get_or_create(
            slug=agreement["terms_slug"],
            defaults={"title": agreement["title"], "is_public": is_public},
        )
        if not terms.versions.exists():
            TermsVersion.objects.create(
                terms=terms,
                version="example-1",
                markdown="## Example terms\n\nThese are fictional test terms.\n",
            )
    return Program.objects.create(
        slug="sample-services",
        title="Example Services",
        is_public=is_public,
        definition=definition,
    )
