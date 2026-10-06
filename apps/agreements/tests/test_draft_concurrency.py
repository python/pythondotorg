from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from time import monotonic, sleep
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.db import connection, connections, transaction
from django.http import Http404
from django.test import RequestFactory, TransactionTestCase
from django.urls import resolve, reverse

from apps.agreements import workflow
from apps.agreements.documents import sha256
from apps.agreements.models import Agreement, CustomContract
from apps.agreements.orders.documents import compose_order_form_markdown
from apps.agreements.registry import get_kind
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_agreements import make_officer
from apps.agreements.tests.test_orders import make_order, payload


@skipUnless(connection.vendor == "postgresql", "Exercises PostgreSQL row-lock contention")
class DraftConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.officer = make_officer()
        self.officer.get_all_permissions()

    def post_during_change(self, subject, route, data, change, *, user=None):
        """Make a request contend with a transaction already holding the draft lock."""
        backend = Queue()
        url = reverse(route, args=[subject.pk])

        def submit():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    backend.put(cursor.fetchone()[0])
                request = RequestFactory().post(url, data)
                request.user = user or self.officer
                request.session = {}
                MessageMiddleware(lambda _request: None).process_request(request)
                match = resolve(url)
                try:
                    return match.func(request, **match.kwargs).status_code
                except Http404:
                    return 404
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                type(subject).objects.select_for_update().get(pk=subject.pk)
                pending = pool.submit(submit)
                pid = backend.get(timeout=10)
                deadline = monotonic() + 10
                while monotonic() < deadline:
                    if pending.done():
                        self.fail(f"Draft mutation did not wait for the offer: {pending.result()}")
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [pid])
                        row = cursor.fetchone()
                    if row and row[0] == "Lock":
                        break
                    sleep(0.01)
                else:
                    self.fail("Draft mutation never reached the held row lock")
                result = change()
            status = pending.result(timeout=10)
        return status, result

    def mutate_while_offering(self, subject, kind, route, data):
        def offer_and_sign():
            agreement = workflow.offer(get_kind(kind), subject, user=self.officer)
            return workflow.sign(
                agreement,
                workflow.Signature("Customer", "Director", "customer@example.com"),
                seen_sha256=agreement.document_sha256,
            )

        status, agreement = self.post_during_change(subject, route, data, offer_and_sign)
        subject.refresh_from_db()
        self.assertEqual(subject.agreement_id, agreement.pk)
        self.assertEqual(subject.agreement.status, Agreement.Status.SIGNED)
        return status, agreement

    def contract(self):
        return CustomContract.objects.create(
            title="Original contract",
            counterparty_name="Example Company",
            body_markdown="Original terms.",
            created_by=self.officer,
        )

    def test_contract_edit_cannot_detach_a_concurrent_signed_offer(self):
        contract = self.contract()
        status, _ = self.mutate_while_offering(
            contract,
            "custom",
            "agreements:custom_edit",
            {"title": "Stale edit", "counterparty_name": "Changed", "body_markdown": "Changed terms."},
        )
        self.assertEqual(status, 302)
        self.assertEqual(contract.title, "Original contract")
        self.assertEqual(contract.body_markdown, "Original terms.")

    def test_contract_delete_cannot_remove_a_concurrent_signed_offer(self):
        status, _ = self.mutate_while_offering(self.contract(), "custom", "agreements:custom_delete", {})
        self.assertEqual(status, 404)

    def test_order_edit_preserves_a_concurrent_signed_offer_and_frozen_selections(self):
        program = make_program()
        order = make_order(self.officer, program=program)
        status, _ = self.mutate_while_offering(
            order, "order", "agreements:order_edit", payload(legal_name="Stale edit")
        )
        self.assertEqual(status, 302)
        self.assertEqual(order.legal_name, "Example Workshops, Inc.")
        self.assertEqual(order.catalog_snapshot, program.definition)
        self.assertEqual(list(order.agreements.values_list("agreement", "tier")), [("studio", "plus")])

    def test_order_delete_preserves_a_concurrent_signed_offer_and_its_lines(self):
        order = make_order(self.officer, program=make_program())
        status, _ = self.mutate_while_offering(order, "order", "agreements:order_delete", {})
        self.assertEqual(status, 404)
        self.assertEqual(list(order.agreements.values_list("agreement", "tier")), [("studio", "plus")])

    def test_reassigned_customer_cannot_sign_the_order(self):
        customer = get_user_model().objects.create_user("customer", "customer@example.com")
        replacement = get_user_model().objects.create_user("replacement", "replacement@example.com")
        order = make_order(self.officer, program=make_program(), customer_account=customer)
        digest = sha256(compose_order_form_markdown(order))

        def reassign():
            order.customer_account = replacement
            order.save(update_fields=["customer_account"])

        status, _ = self.post_during_change(
            order,
            "agreements:order_sign",
            {"signer_name": "Customer", "signer_title": "Director", "accept": "on", "document_sha256": digest},
            reassign,
            user=customer,
        )
        self.assertEqual(status, 404)
        order.refresh_from_db()
        self.assertEqual(order.customer_account_id, replacement.pk)
        self.assertIsNone(order.agreement_id)
        self.assertFalse(Agreement.objects.exists())

    def test_removed_customer_cannot_offer_the_order(self):
        customer = get_user_model().objects.create_user("customer", "customer@example.com")
        order = make_order(self.officer, program=make_program(), customer_account=customer)

        def unlink():
            order.customer_account = None
            order.save(update_fields=["customer_account"])

        status, _ = self.post_during_change(order, "agreements:order_offer", {}, unlink, user=customer)
        self.assertEqual(status, 404)
        order.refresh_from_db()
        self.assertIsNone(order.customer_account_id)
        self.assertIsNone(order.agreement_id)
        self.assertFalse(Agreement.objects.exists())
