"""Exact fee calculations from validated, declarative catalog rules."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from django.core.exceptions import ValidationError

from apps.agreements.orders.catalog import MONTHS_PER_YEAR, PERCENT_SCALE

CENTS = Decimal("0.01")


def _precision(*amounts):
    """Allow exact sums, products, and cent rounding beyond the default context."""
    return max(28, sum(len(amount.as_tuple().digits) + abs(amount.as_tuple().exponent) for amount in amounts) + 4)


def money(amount):
    """Format a decimal amount as dollars, omitting whole-dollar cents."""
    amount = Decimal(amount)
    with localcontext() as context:
        context.prec = _precision(amount)
        amount = amount.quantize(CENTS)
    if amount == amount.to_integral():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


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
    def subtotal(self):
        """Return the tier fee plus every priced additional service."""
        amounts = [self.tier_fee, *(item.amount for item in self.items if item.amount is not None)]
        with localcontext() as context:
            context.prec = _precision(*amounts)
            return sum(amounts, Decimal(0))

    @property
    def total_annual(self):
        """Return the first year's fees after the tier discount."""
        subtotal = self.subtotal
        with localcontext() as context:
            context.prec = _precision(subtotal, self.discount_amount)
            return subtotal - self.discount_amount

    @property
    def term_years(self):
        """Return the number of whole years in the initial term."""
        return self.term_months // MONTHS_PER_YEAR

    @property
    def term_total(self):
        """Repeat recurring charges across the term and charge other items once."""
        priced = [item for item in self.items if item.amount is not None]
        with localcontext() as context:
            context.prec = _precision(
                self.tier_fee, self.discount_amount, Decimal(self.term_years), *(item.amount for item in priced)
            )
            recurring = self.tier_fee - self.discount_amount
            recurring += sum((item.amount for item in priced if item.recurring), Decimal(0))
            one_time = sum((item.amount for item in priced if not item.recurring), Decimal(0))
            return recurring * self.term_years + one_time

    @property
    def unpriced_items(self):
        """Return selected services whose fees are not determined in advance."""
        return [item for item in self.items if item.amount is None]

    def as_dict(self):
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


def _invalid(message):
    raise ValidationError(message)


def _quantity(params, key):
    value = params[key]
    return len(value) if isinstance(value, list) else value


def _validate_sum_quantities(rule, params):
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


def _clean_count(value, param, addon):
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


def _clean_lines(value, param, addon):
    if isinstance(value, str):
        value = value.splitlines()
    if not isinstance(value, list) or any(not isinstance(line, str) for line in value):
        _invalid(f"{addon.name}: {param.label} must contain one text value per line.")
    value = [line.strip() for line in value if line.strip()]
    if not value:
        _invalid(f"{addon.name}: {param.label} is required.")
    return value


def _clean_value(value, param, addon):
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


def normalize_params(addon, params):
    """Validate selected parameters and omit those whose conditions do not apply."""
    if not isinstance(params, dict):
        _invalid(f"{addon.name}: parameters must be an object.")
    by_key = {param.key: param for param in addon.params}
    unknown = params.keys() - by_key.keys()
    if unknown:
        _invalid(f"{addon.name}: unknown parameter(s): {', '.join(sorted(map(str, unknown)))}.")
    cleaned = {}
    visited = set()

    def clean(key):
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


def _price_rule(rule, params):
    kind = rule["type"]
    if kind == "choice":
        return _price_rule(rule["options"][params[rule["parameter"]]], params)
    recurring = rule.get("recurring", True)
    basis = rule.get("basis") or ("per year" if recurring else "one-time")
    detail = rule.get("detail", "")
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
                context.prec = _precision(*amounts)
                amount = sum(amounts, Decimal(0))
        if not detail:
            detail = "; ".join(component[3] for component in components if component[3])
    else:
        amount = None
        basis = rule.get("basis") or "Quoted separately"
    return amount, recurring, basis, detail


def _price_addon(addon, params, tier_key):
    params = normalize_params(addon, params)
    amount, recurring, basis, detail = _price_rule(addon.pricing, params)
    selections = []
    for param in addon.params:
        if param.key not in params:
            continue
        value = params[param.key]
        if param.kind == "choice":
            value = dict(param.choices)[value]
        elif param.kind == "lines":
            value = ", ".join(value)
        selections.append(f"{param.label}: {value}")
    if tier_key in addon.included_in_tiers:
        amount, basis, detail = Decimal(0), "included", "Included at this service tier"
    detail = "; ".join(part for part in (detail, *selections) if part)
    return LineItem(addon.name, detail, amount, recurring, basis)


def build_quote(agreement, tier_key, discount_key, addons=None):
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
