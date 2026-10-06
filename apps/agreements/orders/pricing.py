"""Exact fee calculations from validated, declarative catalog rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any, Literal, NoReturn, TypedDict, cast

from django.core.exceptions import ValidationError

from apps.agreements.orders.catalog import MONTHS_PER_YEAR, PERCENT_SCALE, AddOn, Agreement, Param

CENTS = Decimal("0.01")

ParamValue = str | int | list[str]
type FeeKey = Literal[
    "tier_fee", "subtotal", "discount_amount", "total_annual", "term_total", "discount_percent", "term_months"
]


class LineItemSnapshot(TypedDict):
    """Serialized charge retained in an offered order."""

    name: str
    detail: str
    amount: str | None
    display: str
    recurring: bool
    basis: str


class QuoteDisplay(TypedDict):
    """Formatted monetary fields for order presentation."""

    tier_fee: str
    subtotal: str
    discount_amount: str
    total_annual: str
    term_total: str


class QuoteSnapshot(TypedDict):
    """Frozen quote schema stored with each order line."""

    tier_name: str
    tier_fee: str
    items: list[LineItemSnapshot]
    subtotal: str
    discount_name: str
    discount_percent: int
    discount_amount: str
    total_annual: str
    term_months: int
    term_total: str
    display: QuoteDisplay


def _precision(*amounts: Decimal) -> int:
    """Allow exact sums, products, and cent rounding beyond the default context."""
    return max(
        28, sum(len(amount.as_tuple().digits) + abs(cast("int", amount.as_tuple().exponent)) for amount in amounts) + 4
    )


def money(amount: Decimal | str | float) -> str:
    """Format a decimal amount as dollars, omitting whole-dollar cents."""
    amount = Decimal(amount)
    with localcontext() as context:
        context.prec = _precision(amount)
        amount = amount.quantize(CENTS)
    if amount == amount.to_integral():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


def fee_totals(pricing: QuoteSnapshot) -> dict[str, Decimal]:
    """Separate recurring and one-time fees without changing stored first-year totals."""
    first_year = Decimal(pricing["total_annual"])
    amounts = [
        Decimal(item["amount"]) for item in pricing["items"] if item["amount"] is not None and not item["recurring"]
    ]
    with localcontext() as context:
        context.prec = _precision(first_year, *amounts)
        one_time = sum(amounts, Decimal(0))
        return {"annual": first_year - one_time, "one_time": one_time}


@dataclass(frozen=True)
class LineItem:
    """One additional-service charge, or an explicit separately quoted item."""

    name: str
    detail: str
    amount: Decimal | None
    recurring: bool
    basis: str


@dataclass(frozen=True)
class Quote:
    """A complete fee schedule with tier-only discounts and term totals."""

    tier_name: str
    tier_fee: Decimal
    items: tuple[LineItem, ...]
    discount_name: str
    discount_percent: int
    discount_amount: Decimal
    term_months: int

    @property
    def subtotal(self) -> Decimal:
        """Return the tier fee plus every priced additional service."""
        amounts = [self.tier_fee, *(item.amount for item in self.items if item.amount is not None)]
        with localcontext() as context:
            context.prec = _precision(*amounts)
            return sum(amounts, Decimal(0))

    @property
    def total_annual(self) -> Decimal:
        """Return the first year's fees after the tier discount."""
        subtotal = self.subtotal
        with localcontext() as context:
            context.prec = _precision(subtotal, self.discount_amount)
            return subtotal - self.discount_amount

    @property
    def term_years(self) -> int:
        """Return the number of whole years in the initial term."""
        return self.term_months // MONTHS_PER_YEAR

    @property
    def term_total(self) -> Decimal:
        """Repeat recurring charges across the term and charge other items once."""
        priced = [item for item in self.items if item.amount is not None]
        with localcontext() as context:
            context.prec = _precision(
                self.tier_fee,
                self.discount_amount,
                Decimal(self.term_years),
                *(cast("Decimal", item.amount) for item in priced),
            )
            recurring = self.tier_fee - self.discount_amount
            recurring += sum((cast("Decimal", item.amount) for item in priced if item.recurring), Decimal(0))
            one_time = sum((cast("Decimal", item.amount) for item in priced if not item.recurring), Decimal(0))
            return recurring * self.term_years + one_time

    @property
    def unpriced_items(self) -> list[LineItem]:
        """Return selected services whose fees are not determined in advance."""
        return [item for item in self.items if item.amount is None]

    def as_dict(self) -> QuoteSnapshot:
        """Return a JSON-safe fee snapshot for storage and the order builder."""
        return {
            "tier_name": self.tier_name,
            "tier_fee": format(self.tier_fee, "f"),
            "items": [
                {
                    "name": item.name,
                    "detail": item.detail,
                    "amount": None if item.amount is None else format(item.amount, "f"),
                    "display": item.basis if item.amount is None else money(item.amount),
                    "recurring": item.recurring,
                    "basis": item.basis,
                }
                for item in self.items
            ],
            "subtotal": format(self.subtotal, "f"),
            "discount_name": self.discount_name,
            "discount_percent": self.discount_percent,
            "discount_amount": format(self.discount_amount, "f"),
            "total_annual": format(self.total_annual, "f"),
            "term_months": self.term_months,
            "term_total": format(self.term_total, "f"),
            "display": {
                "tier_fee": money(self.tier_fee),
                "subtotal": money(self.subtotal),
                "discount_amount": money(self.discount_amount),
                "total_annual": money(self.total_annual),
                "term_total": money(self.term_total),
            },
        }


def _invalid(message: str) -> NoReturn:
    raise ValidationError(message)


def _quantity(params: dict[str, ParamValue], key: str) -> int:
    value = params[key]
    return len(value) if isinstance(value, list) else cast("int", value)


def _validate_sum_quantities(rule: dict[str, Any], params: dict[str, ParamValue]) -> list[int]:
    """Require a positive quantity in each sum, even when its price is zero."""
    kind = rule["type"]
    if kind in {"quantity", "brackets"}:
        return [_quantity(params, rule["parameter"])]
    if kind == "choice":
        return _validate_sum_quantities(rule["options"][params[rule["parameter"]]], params)
    if kind == "sum":
        counts = [count for child in rule["components"] for count in _validate_sum_quantities(child, params)]
        if counts and not any(counts):
            _invalid("Select at least one item for the additional service.")
        return counts
    return []


def _clean_count(value: object, param: Param, addon: AddOn) -> int:
    if value is None or value == "":
        if param.minimum == 0:
            return 0
        _invalid(f"{addon.name}: {param.label} is required.")
    if not isinstance(value, int) or isinstance(value, bool):
        if not isinstance(value, str):
            _invalid(f"{addon.name}: {param.label} must be a whole number.")
        try:
            value = int(value)
        except ValueError:
            message = f"{addon.name}: {param.label} must be a whole number."
            raise ValidationError(message) from None
    if value < param.minimum:
        _invalid(f"{addon.name}: {param.label} must be at least {param.minimum}.")
    return value


def _clean_lines(value: object, param: Param, addon: AddOn) -> list[str]:
    if isinstance(value, str):
        value = value.splitlines()
    if not isinstance(value, list) or any(not isinstance(line, str) for line in value):
        _invalid(f"{addon.name}: {param.label} must contain one text value per line.")
    value = [line.strip() for line in value if line.strip()]
    if not value:
        _invalid(f"{addon.name}: {param.label} is required.")
    return value


def _clean_value(value: object, param: Param, addon: AddOn) -> ParamValue:
    if param.kind == "count":
        return _clean_count(value, param, addon)
    if param.kind == "lines":
        return _clean_lines(value, param, addon)
    if param.kind == "choice":
        if not isinstance(value, str) or value not in dict(param.choices):
            _invalid(f"{addon.name}: select a valid {param.label}.")
        return value
    if not isinstance(value, str) or not value.strip():
        _invalid(f"{addon.name}: {param.label} is required.")
    return value.strip()


def normalize_params(addon: AddOn, params: object) -> dict[str, ParamValue]:
    """Validate selected parameters and omit those whose conditions do not apply."""
    if not isinstance(params, dict):
        _invalid(f"{addon.name}: parameters must be an object.")
    by_key = {param.key: param for param in addon.params}
    unknown = params.keys() - by_key.keys()
    if unknown:
        _invalid(f"{addon.name}: unknown parameter(s): {', '.join(sorted(map(str, unknown)))}.")
    cleaned: dict[str, ParamValue] = {}
    visited: set[str] = set()

    def clean(key: str) -> None:
        if key in visited:
            return
        param = by_key[key]
        for dependency in param.required_when:
            clean(dependency)
        visited.add(key)
        if any(cleaned.get(dependency) != value for dependency, value in param.required_when.items()):
            return
        cleaned[key] = _clean_value(params.get(key), param, addon)

    for param in addon.params:
        clean(param.key)
    _validate_sum_quantities(addon.pricing, cleaned)
    return cleaned


def _price_rule(rule: dict[str, Any], params: dict[str, ParamValue]) -> tuple[Decimal | None, bool, str, str]:
    kind = rule["type"]
    if kind == "choice":
        return _price_rule(rule["options"][params[rule["parameter"]]], params)
    recurring = rule.get("recurring", True)
    basis = rule.get("basis") or ("per year" if recurring else "one-time")
    detail = rule.get("detail", "")
    amount: Decimal | None
    count: Decimal | int
    if kind == "fixed":
        amount = Decimal(rule["amount"])
    elif kind == "quantity":
        count = Decimal(max(0, _quantity(params, rule["parameter"]) - rule.get("included", 0)))
        unit = Decimal(rule["unit_amount"])
        base = Decimal(rule.get("base_amount", "0"))
        with localcontext() as context:
            context.prec = _precision(count, unit, base)
            amount = base + count * unit
    elif kind == "brackets":
        count = _quantity(params, rule["parameter"])
        amount = next((Decimal(band["amount"]) for band in rule["bands"] if count <= band["up_to"]), None)
        if amount is None:
            basis = rule["overflow_basis"]
    elif kind == "sum":
        components = [_price_rule(component, params) for component in rule["components"]]
        amounts = [component[0] for component in components]
        if any(amount is None for amount in amounts):
            amount = None
        else:
            with localcontext() as context:
                context.prec = _precision(*cast("list[Decimal]", amounts))
                amount = sum(cast("list[Decimal]", amounts), Decimal(0))
        if not detail:
            detail = "; ".join(component[3] for component in components if component[3])
    else:
        amount = None
        basis = rule.get("basis") or "Quoted separately"
    return amount, recurring, basis, detail


def _price_addon(addon: AddOn, params: object, tier_key: str) -> LineItem:
    params = normalize_params(addon, params)
    amount, recurring, basis, detail = _price_rule(addon.pricing, params)
    selections = []
    for param in addon.params:
        if param.key not in params:
            continue
        value = params[param.key]
        if param.kind == "choice":
            value = dict(param.choices)[cast("str", value)]
        elif param.kind == "lines":
            value = ", ".join(cast("list[str]", value))
        selections.append(f"{param.label}: {value}")
    if tier_key in addon.included_in_tiers:
        amount, basis, detail = Decimal(0), "included", "Included at this service tier"
    detail = "; ".join(part for part in (detail, *selections) if part)
    return LineItem(addon.name, detail, amount, recurring, basis)


def build_quote(agreement: Agreement, tier_key: str, discount_key: str, addons: object = None) -> Quote:
    """Price all selections in catalog order; discounts affect only the tier fee."""
    tier = agreement.tier(tier_key)
    discount = agreement.discount(discount_key)
    selected = {} if addons is None else addons
    if not isinstance(selected, dict):
        _invalid("Selected additional services must be an object.")
    known = {addon.key for addon in agreement.addons}
    unknown = selected.keys() - known
    if unknown:
        _invalid(f"Unknown additional service(s): {', '.join(sorted(map(str, unknown)))}.")
    items = tuple(
        _price_addon(addon, selected[addon.key], tier_key) for addon in agreement.addons if addon.key in selected
    )
    with localcontext() as context:
        context.prec = _precision(tier.annual_fee)
        discount_amount = (tier.annual_fee * discount.percent / PERCENT_SCALE).quantize(CENTS)
    return Quote(
        tier_name=tier.name,
        tier_fee=tier.annual_fee,
        items=items,
        discount_name=discount.name,
        discount_percent=discount.percent,
        discount_amount=discount_amount,
        term_months=discount.term_months,
    )
