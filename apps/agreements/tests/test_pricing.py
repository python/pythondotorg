from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.agreements.orders.catalog import Catalog, validate_catalog
from apps.agreements.orders.pricing import Quote, build_quote, normalize_params
from apps.agreements.tests.catalog_data import CATALOG_DATA


class QuoteTests(SimpleTestCase):
    def setUp(self) -> None:
        self.catalog = Catalog(deepcopy(CATALOG_DATA))
        self.agreement = self.catalog.agreements["workshop"]

    def quote(self, addons: object = None, tier: str = "basic", discount: str = "none") -> Quote:
        return build_quote(self.agreement, tier, discount, addons)

    def test_discount_applies_to_tier_fee_not_additional_services(self) -> None:
        quote = self.quote({"kit": {}, "sessions": {"hours": 2}}, discount="eligible")
        self.assertEqual(quote.discount_amount, Decimal(450))
        self.assertEqual(quote.total_annual, Decimal(1560))

    def test_prepaid_term_repeats_recurring_fees_but_not_one_time_fees(self) -> None:
        quote = self.quote({"kit": {}, "sessions": {"hours": 1}}, tier="plus", discount="prepaid")
        self.assertEqual(quote.term_months, 36)
        self.assertEqual(quote.term_total, Decimal("9946.50"))

    def test_choice_branch_controls_recurrence(self) -> None:
        periodic = self.quote({"reports": {"mode": "periodic"}}, discount="prepaid")
        single = self.quote({"reports": {"mode": "single", "copies": 2}}, discount="prepaid")
        self.assertTrue(periodic.items[0].recurring)
        self.assertFalse(single.items[0].recurring)
        self.assertEqual(periodic.term_total, Decimal(5004))
        self.assertEqual(single.term_total, Decimal(4790))

    def test_included_addon_is_free_only_at_configured_tier(self) -> None:
        included = self.quote({"advisor": {}}, tier="max")
        paid = self.quote({"advisor": {}})
        self.assertEqual(included.items[0].amount, Decimal(0))
        self.assertEqual(included.total_annual, Decimal(7200))
        self.assertEqual(paid.total_annual, Decimal(2010))

    def test_line_quantity_charges_only_above_included_count(self) -> None:
        included = self.quote({"labels": {"names": ["one", "two", "three"]}})
        extra = self.quote({"labels": {"names": "one\n two\n\nthree\nfour\n"}})
        self.assertEqual(included.items[0].amount, Decimal(42))
        self.assertEqual(extra.items[0].amount, Decimal(49))
        self.assertIn("one, two, three, four", extra.items[0].detail)

    def test_bracket_boundaries_and_unpriced_overflow(self) -> None:
        for units, amount in ((8, "95"), (9, "185"), (30, "185"), (31, None)):
            with self.subTest(units=units):
                quote = self.quote({"batch": {"units": units}})
                self.assertEqual(quote.items[0].amount, Decimal(amount) if amount is not None else None)
                if amount is None:
                    self.assertEqual(quote.total_annual, Decimal(1800))
                    self.assertEqual(quote.as_dict()["items"][0]["display"], "Quoted separately above 30 units")

    def test_unpriced_services_are_explicit_and_excluded_from_totals(self) -> None:
        quote = self.quote({"custom": {}})
        self.assertEqual(quote.total_annual, Decimal(1800))
        self.assertEqual([item.name for item in quote.unpriced_items], ["Custom project"])
        self.assertIsNone(quote.as_dict()["items"][0]["amount"])
        self.assertEqual(quote.as_dict()["items"][0]["display"], "Quoted separately")

    def test_line_items_follow_catalog_order_not_selection_order(self) -> None:
        quote = self.quote({"custom": {}, "kit": {}})
        self.assertEqual([item.name for item in quote.items], ["Resource kit", "Custom project"])

    def test_agreement_without_addons_uses_same_discount_rules(self) -> None:
        quote = build_quote(self.catalog.agreements["studio"], "max", "prepaid")
        self.assertEqual(quote.total_annual, Decimal(4224))
        self.assertEqual(quote.term_total, Decimal(12672))

    def test_discount_rounds_to_cents_without_rounding_addon_prices(self) -> None:
        definition = deepcopy(CATALOG_DATA)
        definition["agreements"][1]["tiers"][0]["annual_fee"] = "99.99"
        agreement = Catalog(definition).agreements["workshop"]
        quote = build_quote(agreement, "basic", "eligible", {"sessions": {"hours": 3}})
        self.assertEqual(quote.discount_amount, Decimal("25.00"))
        self.assertEqual(quote.total_annual, Decimal("187.49"))
        self.assertEqual(quote.as_dict()["display"]["total_annual"], "$187.49")

    def test_active_conditional_parameter_is_required(self) -> None:
        with self.assertRaises(ValidationError):
            self.quote({"reports": {"mode": "single"}})
        quote = self.quote({"reports": {"mode": "single", "copies": "3"}})
        self.assertEqual(quote.items[0].amount, Decimal(57))

    def test_inactive_conditional_parameter_is_ignored_and_not_rendered(self) -> None:
        params = {"mode": "periodic", "copies": {"invalid": "ignored"}}
        cleaned = normalize_params(self.agreement.addon("reports"), params)
        quote = self.quote({"reports": params})
        self.assertEqual(cleaned, {"mode": "periodic"})
        self.assertEqual(quote.items[0].amount, Decimal(84))
        self.assertNotIn("Copies", quote.items[0].detail)

    def test_optional_counts_require_a_positive_combined_selection(self) -> None:
        for params in ({}, {"small": 0, "large": 0}):
            with self.subTest(params=params), self.assertRaises(ValidationError):
                self.quote({"bundles": params})
        quote = self.quote({"bundles": {"small": 2, "large": 3}})
        self.assertEqual(quote.items[0].amount, Decimal(229))
        self.assertEqual(self.quote({"bundles": {"large": 1}}).items[0].amount, Decimal(61))

    def test_zero_priced_quantity_still_counts_as_a_selection(self) -> None:
        definition = deepcopy(CATALOG_DATA)
        addon = next(addon for addon in definition["agreements"][1]["addons"] if addon["key"] == "bundles")
        addon["pricing"]["components"][0]["unit_amount"] = "0"
        quote = build_quote(Catalog(definition).agreements["workshop"], "basic", "none", {"bundles": {"small": 1}})
        self.assertEqual(quote.items[0].amount, Decimal(0))

    def test_missing_invalid_and_below_minimum_counts_are_rejected(self) -> None:
        for value in (None, "not a number", 0, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.quote({"sessions": {"hours": value}})

    def test_choice_values_must_be_declared(self) -> None:
        value: object
        for value in (None, "unexpected", []):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.quote({"reports": {"mode": value}})

    def test_empty_or_nontext_line_inputs_do_not_price_as_zero(self) -> None:
        for value in (None, [], "\n  \n", ["valid", 3]):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.quote({"labels": {"names": value}})

    def test_text_parameters_are_required_and_appear_in_details(self) -> None:
        with self.assertRaises(ValidationError):
            self.quote({"schedule": {"window": " "}})
        quote = self.quote({"schedule": {"window": "  Evenings  "}})
        self.assertEqual(quote.items[0].amount, Decimal(315))
        self.assertEqual(quote.items[0].detail, "Schedule: Evenings")

    def test_unknown_selections_and_wrong_container_types_are_rejected(self) -> None:
        addons: object
        for addons in ({"missing": {}}, {"kit": {"unexpected": 1}}, {"kit": []}, []):
            with self.subTest(addons=addons), self.assertRaises(ValidationError):
                self.quote(addons)
        with self.assertRaises(ValidationError):
            self.quote(tier="missing")
        with self.assertRaises(ValidationError):
            self.quote(discount="missing")

    def test_tier_restricted_services_follow_catalog_membership(self) -> None:
        self.assertEqual([s.key for s in self.agreement.services_at("basic")], ["materials"])
        self.assertEqual([s.key for s in self.agreement.services_at("max")], ["materials", "planning"])
        with self.assertRaises(ValidationError):
            self.agreement.services_at("missing")


class CatalogValidationTests(SimpleTestCase):
    def setUp(self) -> None:
        self.definition = deepcopy(CATALOG_DATA)
        self.agreement = self.definition["agreements"][1]
        self.addons = {addon["key"]: addon for addon in self.agreement["addons"]}

    def assert_invalid(self, field: str) -> None:
        with self.assertRaises(ValidationError) as raised:
            validate_catalog(self.definition)
        self.assertIn(field, str(raised.exception))

    def test_malformed_container_shapes_raise_validation_errors(self) -> None:
        value: object
        for value in (None, [], {}, {"agreements": {}, "discounts": []}):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_catalog(value)
        self.agreement["tiers"][0] = None
        self.assert_invalid("tiers")

    def test_missing_nested_required_fields_are_reported(self) -> None:
        del self.agreement["tiers"][0]["annual_fee"]
        self.assert_invalid("annual_fee")

    def test_unknown_catalog_and_rule_fields_are_rejected(self) -> None:
        self.definition["typo"] = True
        self.assert_invalid("typo")
        del self.definition["typo"]
        self.addons["kit"]["pricing"]["ammount"] = "1"
        self.assert_invalid("ammount")

    def test_identifiers_must_be_unique_in_their_scope(self) -> None:
        self.agreement["slug"] = self.definition["agreements"][0]["slug"]
        self.assert_invalid("duplicate slug")
        self.agreement["slug"] = "workshop"
        self.agreement["tiers"][1]["key"] = "basic"
        self.assert_invalid("duplicate key")

    def test_prices_are_finite_nonnegative_decimal_strings(self) -> None:
        for value in ("NaN", "Infinity", "-0.01", 3.5, "not money"):
            with self.subTest(value=value):
                self.agreement["tiers"][0]["annual_fee"] = value
                self.assert_invalid("annual_fee")

    def test_money_precision_must_fit_supported_currency_amounts(self) -> None:
        for value in ("0.001", "1e999", "0e999"):
            with self.subTest(value=value):
                self.addons["kit"]["pricing"]["amount"] = value
                self.assert_invalid("amount")

    def test_integer_fields_do_not_accept_booleans(self) -> None:
        self.agreement["tiers"][0]["fair_use"] = True
        self.assert_invalid("fair_use")

    def test_term_months_must_cover_whole_positive_years(self) -> None:
        for value in (0, 18, "24"):
            with self.subTest(value=value):
                self.definition["discounts"][0]["term_months"] = value
                self.assert_invalid("term_months")

    def test_discount_percentage_is_bounded(self) -> None:
        for value in (-1, 101):
            with self.subTest(value=value):
                self.definition["discounts"][0]["percent"] = value
                self.assert_invalid("percent")

    def test_tier_references_cannot_silently_remove_services_or_inclusions(self) -> None:
        self.agreement["services"][0]["tiers"] = ["absent"]
        self.assert_invalid("unknown tier")
        del self.agreement["services"][0]["tiers"]
        self.addons["advisor"]["included_in_tiers"] = ["absent"]
        self.assert_invalid("unknown tier")

    def test_default_tier_must_exist_and_configured_order_is_preserved(self) -> None:
        self.agreement["default_tier"] = "absent"
        self.assert_invalid("default_tier")
        self.agreement["default_tier"] = "plus"
        self.agreement["tiers"].reverse()
        catalog = Catalog(self.definition)
        self.assertEqual(catalog.agreements["workshop"].default_tier, "plus")
        self.assertEqual([tier.key for tier in catalog.agreements["workshop"].tiers], ["max", "plus", "basic"])
        self.assertEqual(list(catalog.agreements), ["studio", "workshop"])

    def test_response_targets_have_four_text_values(self) -> None:
        self.agreement["tiers"][0]["response_targets"] = ["one", "two"]
        self.assert_invalid("response_targets")

    def test_pricing_parameter_references_are_checked_before_quoting(self) -> None:
        self.addons["sessions"]["pricing"]["parameter"] = "absent"
        self.assert_invalid("unknown parameter")
        self.addons["sessions"]["pricing"]["parameter"] = "hours"
        self.addons["sessions"]["params"][0]["kind"] = "text"
        self.assert_invalid("cannot use")

    def test_choice_rule_must_cover_exactly_its_declared_values(self) -> None:
        del self.addons["reports"]["pricing"]["options"]["single"]
        self.assert_invalid("choice values")

    def test_bracket_limits_must_be_strictly_increasing(self) -> None:
        self.addons["batch"]["pricing"]["bands"][1]["up_to"] = 8
        self.assert_invalid("strictly increasing")

    def test_conditional_parameters_require_known_valid_values(self) -> None:
        condition = self.addons["reports"]["params"][1]["required_when"]
        condition["mode"] = "absent"
        self.assert_invalid("invalid choice")
        del condition["mode"]
        condition["absent"] = "value"
        self.assert_invalid("unknown parameter")

    def test_circular_parameter_dependencies_are_rejected(self) -> None:
        self.addons["reports"]["params"][0]["required_when"] = {"copies": 1}
        self.assert_invalid("cycle")

    def test_rule_cannot_use_a_parameter_in_its_inactive_branch(self) -> None:
        options = self.addons["reports"]["pricing"]["options"]
        options["periodic"] = deepcopy(options["single"])
        self.assert_invalid("not guaranteed to be active")

    def test_sum_cannot_collapse_different_recurrences_into_one_charge(self) -> None:
        self.addons["bundles"]["pricing"]["components"][0]["recurring"] = True
        self.assert_invalid("same recurrence")

    def test_recursive_malformed_rules_raise_validation_not_recursion_errors(self) -> None:
        rule: dict[str, Any] = {"type": "sum", "components": []}
        rule["components"].append(rule)
        self.addons["kit"]["pricing"] = rule
        self.assert_invalid("at most 32 levels")
