"""Validated, database-configured agreement catalogs and pricing definitions."""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

MONTHS_PER_YEAR = 12
PERCENT_SCALE = 100
MAX_NESTING = 32
RESPONSE_TARGET_COUNT = 4
CURRENCY_WHOLE_DIGITS = 16
CURRENCY_DECIMAL_PLACES = 2
CHOICE_PAIR_SIZE = 2

RULE_FIELDS = {
    "fixed": {"amount"},
    "quantity": {"parameter", "unit_amount", "base_amount", "included"},
    "brackets": {"parameter", "bands", "overflow_basis"},
    "choice": {"parameter", "options"},
    "sum": {"components"},
    "unpriced": set(),
}


@dataclass(frozen=True)
class Tier:
    """One service tier with its annual fee and response commitments."""

    key: str
    name: str
    annual_fee: Decimal
    response_targets: tuple[str, str, str, str]
    fair_use: int
    includes: str = ""


@dataclass(frozen=True)
class Service:
    """A service available at every tier or at an explicit subset."""

    key: str
    name: str
    description: str
    tiers: tuple[str, ...] = ()

    def included_at(self, tier_key):
        """Return whether this service is included at the selected tier."""
        return not self.tiers or tier_key in self.tiers


@dataclass(frozen=True)
class Param:
    """One typed add-on input and its optional activation conditions."""

    key: str
    label: str
    kind: str
    choices: tuple[tuple[str, str], ...] = ()
    help_text: str = ""
    minimum: int = 1
    required_when: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AddOn:
    """An additional service with declarative pricing and parameter definitions."""

    key: str
    name: str
    description: str
    price_summary: str
    pricing: dict
    params: tuple[Param, ...] = ()
    included_in_tiers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Discount:
    """A nonstacking tier-fee discount and its associated initial term."""

    key: str
    name: str
    percent: int
    term_months: int
    requires_attestation: bool = False


@dataclass(frozen=True)
class Agreement:
    """An agreement's ordered services, tier choices, and pricing options."""

    slug: str
    title: str
    short_name: str
    tagline: str
    terms_slug: str
    tiers: tuple[Tier, ...]
    services: tuple[Service, ...]
    discounts: tuple[Discount, ...]
    default_tier: str
    addons: tuple[AddOn, ...] = ()

    @property
    def terms(self):
        """Return the published terms identified by this agreement."""
        from apps.agreements.models import Terms

        return Terms.objects.get(slug=self.terms_slug)

    def tier(self, key):
        """Return the named tier or raise a selection validation error."""
        return _lookup(self.tiers, key, "tier")

    def discount(self, key):
        """Return the named discount or raise a selection validation error."""
        return _lookup(self.discounts, key, "discount")

    def addon(self, key):
        """Return the named add-on or raise a selection validation error."""
        return _lookup(self.addons, key, "add-on")

    def services_at(self, tier_key):
        """Return services included at a valid tier."""
        self.tier(tier_key)
        return [service for service in self.services if service.included_at(tier_key)]

    @property
    def service_rows(self):
        """Pair each service with its restricted tier names for display."""
        return [
            (service, " and ".join(t.name for t in self.tiers if t.key in service.tiers) if service.tiers else "")
            for service in self.services
        ]


def _lookup(items, key, label):
    for item in items:
        if item.key == key:
            return item
    message = f"Unknown {label}: {key!r}."
    raise ValidationError(message)


def _error(path, message):
    message = f"{path}: {message}"
    raise ValidationError(message)


def _object(value, path, allowed, required=()):
    if not isinstance(value, dict):
        _error(path, "must be an object.")
    unknown = value.keys() - allowed
    if unknown:
        _error(path, f"unknown field(s): {', '.join(sorted(map(str, unknown)))}.")
    missing = set(required) - value.keys()
    if missing:
        _error(path, f"missing field(s): {', '.join(sorted(missing))}.")
    return value


def _list(value, path, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        _error(path, "must be a nonempty list." if nonempty else "must be a list.")
    return value


def _text(value, path, blank=False):
    if not isinstance(value, str) or (not blank and not value.strip()):
        _error(path, "must be text." if blank else "must be nonempty text.")
    return value


def _key(value, path):
    _text(value, path)
    if not re.fullmatch(r"[-a-zA-Z0-9_]+", value):
        _error(path, "must contain only letters, numbers, hyphens, and underscores.")
    return value


def _integer(value, path, minimum=0):
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        _error(path, f"must be an integer of at least {minimum}.")
    return value


def _boolean(value, path):
    if not isinstance(value, bool):
        _error(path, "must be true or false.")
    return value


def _decimal(value, path):
    if not isinstance(value, str):
        _error(path, "must be a decimal string.")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        _error(path, "must be a finite, nonnegative decimal amount.")
    if not amount.is_finite() or amount < 0:
        _error(path, "must be a finite, nonnegative decimal amount.")
    # Monetary arithmetic and cent rounding must remain exact in Decimal's context.
    if amount.adjusted() >= CURRENCY_WHOLE_DIGITS or amount.as_tuple().exponent < -CURRENCY_DECIMAL_PLACES:
        _error(path, "must have at most 16 whole-number digits and two decimal places.")
    return amount


def _unique(records, path, key="key", nonempty=False):
    seen = set()
    for index, record in enumerate(_list(records, path, nonempty)):
        here = f"{path}[{index}]"
        if not isinstance(record, dict):
            _error(here, "must be an object.")
        name = _key(record.get(key), f"{here}.{key}")
        if name in seen:
            _error(here, f"duplicate {key}: {name}.")
        seen.add(name)
        yield record, here


def _tier_refs(value, path, tier_keys):
    refs = _list(value, path)
    seen = set()
    for ref in refs:
        _key(ref, path)
        if ref not in tier_keys:
            _error(path, f"unknown tier: {ref}.")
        if ref in seen:
            _error(path, f"duplicate tier: {ref}.")
        seen.add(ref)
    return tuple(refs)


def _param(row, path):
    _object(
        row,
        path,
        {"key", "label", "kind", "choices", "help_text", "minimum", "required_when"},
        {"key", "label", "kind"},
    )
    kind = _text(row["kind"], f"{path}.kind")
    if kind not in {"choice", "count", "text", "lines"}:
        _error(f"{path}.kind", "must be choice, count, text, or lines.")
    choices = []
    for choice in _list(row.get("choices", []), f"{path}.choices", nonempty=kind == "choice"):
        if not isinstance(choice, list) or len(choice) != CHOICE_PAIR_SIZE:
            _error(f"{path}.choices", "each choice must be a [value, label] pair.")
        value = _text(choice[0], f"{path}.choices.value")
        label = _text(choice[1], f"{path}.choices.label")
        if any(existing[0] == value for existing in choices):
            _error(f"{path}.choices", f"duplicate choice: {value}.")
        choices.append((value, label))
    if choices and kind != "choice":
        _error(path, "choices are only valid for choice parameters.")
    condition = row.get("required_when", {})
    if not isinstance(condition, dict):
        _error(f"{path}.required_when", "must be an object of parameter values.")
    return Param(
        key=row["key"],
        label=_text(row["label"], f"{path}.label"),
        kind=kind,
        choices=tuple(choices),
        help_text=_text(row.get("help_text", ""), f"{path}.help_text", blank=True),
        minimum=_integer(row.get("minimum", 1), f"{path}.minimum"),
        required_when=condition,
    )


def _param_conditions(param, params, path):
    for key, value in param.required_when.items():
        if not isinstance(key, str) or key not in params:
            _error(path, f"unknown parameter: {key!r}.")
        other = params[key]
        if other.kind == "choice":
            if not isinstance(value, str) or value not in dict(other.choices):
                _error(path, f"invalid choice for {key}.")
        elif other.kind == "count":
            _integer(value, path, other.minimum)
        elif other.kind == "text":
            _text(value, path)
        else:
            for line in _list(value, path, nonempty=True):
                _text(line, path)


def _params(records, path):
    result = tuple(_param(row, here) for row, here in _unique(records, path))
    by_key = {param.key: param for param in result}
    for param in result:
        _param_conditions(param, by_key, f"{path}.{param.key}.required_when")
    visited = set()

    def visit(key, pending):
        if key in pending:
            _error(path, "required_when dependencies must not form a cycle.")
        if len(pending) > MAX_NESTING:
            _error(path, f"required_when dependencies may nest at most {MAX_NESTING} levels.")
        if key not in visited:
            for dependency in by_key[key].required_when:
                visit(dependency, pending | {key})
            visited.add(key)

    for key in by_key:
        visit(key, set())
    return result


def _rule_shape(rule, path, depth):
    if depth > MAX_NESTING:
        _error(path, f"pricing rules may nest at most {MAX_NESTING} levels.")
    if not isinstance(rule, dict):
        _error(path, "must be a pricing rule object.")
    kind = _text(rule.get("type"), f"{path}.type")
    if kind not in RULE_FIELDS:
        _error(path, f"unknown pricing rule type: {kind}.")
    common = {"type"} if kind == "choice" else {"type", "recurring", "basis", "detail"}
    required = RULE_FIELDS[kind] - {"base_amount", "included"}
    _object(rule, path, common | RULE_FIELDS[kind], required | {"type"})
    return kind


def _rule_parameter(rule, params, path, conditions):
    parameter = _key(rule["parameter"], f"{path}.parameter")
    if parameter not in params:
        _error(path, f"unknown parameter: {parameter}.")
    param = params[parameter]
    kinds = {"choice"} if rule["type"] == "choice" else {"count", "lines"}
    if param.kind not in kinds:
        _error(path, f"{rule['type']} cannot use a {param.kind} parameter.")
    if any(conditions.get(key) != value for key, value in param.required_when.items()):
        _error(path, f"parameter {parameter} is not guaranteed to be active in this pricing branch.")


def _leaf_rule(rule, path):
    kind = rule["type"]
    if kind == "fixed":
        _decimal(rule["amount"], f"{path}.amount")
    elif kind == "quantity":
        _decimal(rule["unit_amount"], f"{path}.unit_amount")
        _decimal(rule.get("base_amount", "0"), f"{path}.base_amount")
        _integer(rule.get("included", 0), f"{path}.included")
    elif kind == "brackets":
        previous = -1
        for index, band in enumerate(_list(rule["bands"], f"{path}.bands", nonempty=True)):
            here = f"{path}.bands[{index}]"
            _object(band, here, {"up_to", "amount"}, {"up_to", "amount"})
            threshold = _integer(band["up_to"], f"{here}.up_to")
            if threshold <= previous:
                _error(here, "bracket limits must be strictly increasing.")
            previous = threshold
            _decimal(band["amount"], f"{here}.amount")
        _text(rule["overflow_basis"], f"{path}.overflow_basis")


def _choice_rule(rule, params, path, conditions, depth):
    parameter = rule["parameter"]
    options = rule["options"]
    if not isinstance(options, dict) or options.keys() != dict(params[parameter].choices).keys():
        _error(f"{path}.options", "must contain exactly the parameter's choice values.")
    recurrences = set()
    for value, branch in options.items():
        recurrences.update(
            _rule(branch, params, f"{path}.options.{value}", {**conditions, parameter: value}, depth + 1)
        )
    return recurrences


def _rule(rule, params, path, conditions=None, depth=0):
    kind = _rule_shape(rule, path, depth)
    conditions = conditions or {}
    if kind in {"quantity", "brackets", "choice"}:
        _rule_parameter(rule, params, path, conditions)
    if kind == "choice":
        return _choice_rule(rule, params, path, conditions, depth)
    recurring = _boolean(rule.get("recurring", True), f"{path}.recurring")
    _text(rule.get("basis", ""), f"{path}.basis", blank=True)
    _text(rule.get("detail", ""), f"{path}.detail", blank=True)
    if kind == "sum":
        for index, component in enumerate(_list(rule["components"], f"{path}.components", nonempty=True)):
            recurrences = _rule(component, params, f"{path}.components[{index}]", conditions, depth + 1)
            if recurrences != {recurring}:
                _error(path, "summed components must have the same recurrence; use separate add-ons otherwise.")
    else:
        _leaf_rule(rule, path)
    return {recurring}


def _discount(row, path):
    _object(
        row,
        path,
        {"key", "name", "percent", "term_months", "requires_attestation"},
        {"key", "name", "percent", "term_months"},
    )
    percent = _integer(row["percent"], f"{path}.percent")
    if percent > PERCENT_SCALE:
        _error(f"{path}.percent", f"must be between 0 and {PERCENT_SCALE}.")
    months = _integer(row["term_months"], f"{path}.term_months", MONTHS_PER_YEAR)
    if months % MONTHS_PER_YEAR:
        _error(f"{path}.term_months", f"must be a positive multiple of {MONTHS_PER_YEAR}.")
    return Discount(
        key=row["key"],
        name=_text(row["name"], f"{path}.name"),
        percent=percent,
        term_months=months,
        requires_attestation=_boolean(row.get("requires_attestation", False), f"{path}.requires_attestation"),
    )


def _tier(row, path):
    _object(
        row,
        path,
        {"key", "name", "annual_fee", "response_targets", "fair_use", "includes"},
        {"key", "name", "annual_fee", "response_targets", "fair_use"},
    )
    targets = _list(row["response_targets"], f"{path}.response_targets")
    if len(targets) != RESPONSE_TARGET_COUNT:
        _error(f"{path}.response_targets", "must contain exactly four response targets.")
    return Tier(
        key=row["key"],
        name=_text(row["name"], f"{path}.name"),
        annual_fee=_decimal(row["annual_fee"], f"{path}.annual_fee"),
        response_targets=tuple(_text(target, f"{path}.response_targets") for target in targets),
        fair_use=_integer(row["fair_use"], f"{path}.fair_use"),
        includes=_text(row.get("includes", ""), f"{path}.includes", blank=True),
    )


def _service(row, path, tier_keys):
    _object(row, path, {"key", "name", "description", "tiers"}, {"key", "name", "description"})
    return Service(
        key=row["key"],
        name=_text(row["name"], f"{path}.name"),
        description=_text(row["description"], f"{path}.description", blank=True),
        tiers=_tier_refs(row.get("tiers", []), f"{path}.tiers", tier_keys),
    )


def _addon(row, path, tier_keys):
    _object(
        row,
        path,
        {"key", "name", "description", "price_summary", "params", "included_in_tiers", "pricing"},
        {"key", "name", "description", "price_summary", "pricing"},
    )
    params = _params(row.get("params", []), f"{path}.params")
    _rule(row["pricing"], {param.key: param for param in params}, f"{path}.pricing")
    return AddOn(
        key=row["key"],
        name=_text(row["name"], f"{path}.name"),
        description=_text(row["description"], f"{path}.description", blank=True),
        price_summary=_text(row["price_summary"], f"{path}.price_summary", blank=True),
        params=params,
        pricing=row["pricing"],
        included_in_tiers=_tier_refs(row.get("included_in_tiers", []), f"{path}.included_in_tiers", tier_keys),
    )


def _agreement(row, path, discounts):
    _object(
        row,
        path,
        {"slug", "title", "short_name", "tagline", "terms_slug", "default_tier", "tiers", "services", "addons"},
        {"slug", "title", "terms_slug", "tiers"},
    )
    tiers = tuple(_tier(tier, here) for tier, here in _unique(row["tiers"], f"{path}.tiers", nonempty=True))
    tier_keys = {tier.key for tier in tiers}
    default_tier = _key(row.get("default_tier", tiers[0].key), f"{path}.default_tier")
    if default_tier not in tier_keys:
        _error(f"{path}.default_tier", f"unknown tier: {default_tier}.")
    services = tuple(
        _service(service, here, tier_keys) for service, here in _unique(row.get("services", []), f"{path}.services")
    )
    addons = tuple(_addon(addon, here, tier_keys) for addon, here in _unique(row.get("addons", []), f"{path}.addons"))
    title = _text(row["title"], f"{path}.title")
    return Agreement(
        slug=row["slug"],
        title=title,
        short_name=_text(row.get("short_name", title), f"{path}.short_name"),
        tagline=_text(row.get("tagline", ""), f"{path}.tagline", blank=True),
        terms_slug=_key(row["terms_slug"], f"{path}.terms_slug"),
        tiers=tiers,
        services=services,
        discounts=discounts,
        addons=addons,
        default_tier=default_tier,
    )


class Catalog:
    """Parse a definition once, preserving its agreement, tier, and add-on ordering."""

    METADATA = {
        "order_title": "Service order",
        "order_intro": "Select the services for this order.",
        "covered_entities_label": "Covered entities",
        "covered_entities_help": "Enter one entity per line.",
        "attestation_label": "I confirm eligibility for the selected discount.",
        "attestation_help": "Confirm that the customer qualifies for this discount.",
    }
    PAYMENT = {
        "annual": "Annual fees are payable in advance.",
        "multi_year": "Fees for the initial term are payable in advance.",
        "renewal": "Renewal is subject to the applicable agreement terms.",
        "other_charges": "Other charges are payable under the applicable agreement terms.",
    }

    def __init__(self, definition):
        """Validate and parse a JSON-compatible program definition."""
        _object(
            definition,
            "catalog",
            {"agreements", "discounts", "payment"} | self.METADATA.keys(),
            {"agreements", "discounts"},
        )
        for key, default in self.METADATA.items():
            setattr(self, key, _text(definition.get(key, default), f"catalog.{key}", blank=True))
        payment = _object(definition.get("payment", {}), "catalog.payment", self.PAYMENT.keys())
        self.payment = {
            key: _text(payment.get(key, default), f"catalog.payment.{key}", blank=True)
            for key, default in self.PAYMENT.items()
        }
        self.discounts = tuple(
            _discount(row, path) for row, path in _unique(definition["discounts"], "catalog.discounts", nonempty=True)
        )
        self.agreements = {
            row["slug"]: _agreement(row, path, self.discounts)
            for row, path in _unique(definition["agreements"], "catalog.agreements", "slug", nonempty=True)
        }

    def discount(self, key):
        """Return the named shared discount or raise a validation error."""
        return _lookup(self.discounts, key, "discount")


def validate_catalog(value):
    """Validate a Django JSONField value and report malformed definitions."""
    Catalog(value)
