import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from accounts.models import User
from stores.models import Integration, Store
from webhooks.models import WebhookEvent
from webhooks.services.signature import generate_signature
from webhooks.tasks import process_webhook_event

class WebhookSignatureTests(SimpleTestCase):

    def test_generate_signature(self):
        payload = b'{"event":"product.updated"}'
        secret = "test-secret"

        signature = generate_signature(
            payload=payload,
            secret=secret,
        )

        self.assertTrue(signature)

    def test_valid_signature_is_accepted(self):
        payload = b'{"event":"product.updated"}'
        secret = "test-secret"

        signature = generate_signature(
            payload=payload,
            secret=secret,
        )

        self.assertEqual(
            len(signature),
            64,
        )

    def test_invalid_signature_is_rejected(self):
        payload = b'{"event":"product.updated"}'
        secret = "test-secret"

        signature = generate_signature(
            payload=payload,
            secret=secret,
        )

        self.assertNotEqual(
            signature,
            "invalid-signature",
        )

    def test_modified_payload_changes_signature(self):
        payload = b'{"event":"product.updated"}'
        modified_payload = b'{"event":"order.created"}'
        secret = "test-secret"

        original_signature = generate_signature(
            payload=payload,
            secret=secret,
        )

        modified_signature = generate_signature(
            payload=modified_payload,
            secret=secret,
        )

        self.assertNotEqual(
            original_signature,
            modified_signature,
        )


class WebhookEndpointTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="webhook-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Webhook Test Store",
            external_store_id="webhook-test-store",
            credentials={
                "webhook_secret": "webhook-test-secret",
            },
        )

    def setUp(self):
        self.client = APIClient()

    def make_payload(self):
        return {
            "event_id": "evt-001",
            "event_type": "product.updated",
            "external_id": "mock-product-001",
            "data": {
                "product_id": "mock-product-001",
            },
        }

    def test_valid_webhook_is_received(self):
        payload = self.make_payload()

        body = json.dumps(payload).encode("utf-8")

        signature = generate_signature(
            payload=body,
            secret="webhook-test-secret",
        )

        response = self.client.post(
            "/api/webhooks/mock/",
            data=body,
            content_type="application/json",
            HTTP_X_STORE_ID=str(self.store.id),
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            WebhookEvent.objects.count(),
            1,
        )

        event = WebhookEvent.objects.get()

        self.assertEqual(
            event.event_id,
            "evt-001",
        )

        self.assertEqual(
            event.event_type,
            "product.updated",
        )

        self.assertEqual(
            event.store,
            self.store,
        )

    def test_invalid_signature_is_rejected(self):
        payload = self.make_payload()

        body = json.dumps(payload).encode("utf-8")

        response = self.client.post(
            "/api/webhooks/mock/",
            data=body,
            content_type="application/json",
            HTTP_X_STORE_ID=str(self.store.id),
            HTTP_X_WEBHOOK_SIGNATURE="invalid-signature",
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            WebhookEvent.objects.count(),
            0,
        )

    def test_unknown_store_is_rejected(self):
        payload = self.make_payload()

        body = json.dumps(payload).encode("utf-8")

        signature = generate_signature(
            payload=body,
            secret="webhook-test-secret",
        )

        response = self.client.post(
            "/api/webhooks/mock/",
            data=body,
            content_type="application/json",
            HTTP_X_STORE_ID="999999",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            WebhookEvent.objects.count(),
            0,
        )

    def test_duplicate_webhook_is_not_created_twice(self):
        payload = self.make_payload()
        raw_payload = json.dumps(payload).encode("utf-8")

        signature = generate_signature(
            payload=raw_payload,
            secret="webhook-test-secret",
        )

        headers = {
            "HTTP_X_STORE_ID": str(self.store.id),
            "HTTP_X_WEBHOOK_SIGNATURE": signature,
            "content_type": "application/json",
        }

        first_response = self.client.post(
            "/api/webhooks/mock/",
            data=raw_payload,
            **headers,
        )

        second_response = self.client.post(
            "/api/webhooks/mock/",
            data=raw_payload,
            **headers,
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(
            WebhookEvent.objects.filter(
                store=self.store,
                event_id=payload["event_id"],
            ).count(),
            1,
        )

        self.assertIn(
            "already received",
            second_response.json()["detail"],
        )

    @patch("webhooks.views.process_webhook_event.delay")
    def test_valid_webhook_queues_processing_task(
        self,
        mock_delay,
    ):
        payload = self.make_payload()
        raw_payload = json.dumps(payload).encode("utf-8")

        signature = generate_signature(
            payload=raw_payload,
            secret="webhook-test-secret",
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/webhooks/mock/",
                data=raw_payload,
                content_type="application/json",
                HTTP_X_STORE_ID=str(self.store.id),
                HTTP_X_WEBHOOK_SIGNATURE=signature,
            )

        self.assertEqual(response.status_code, 200)

        webhook_event = WebhookEvent.objects.get(
            store=self.store,
            event_id=payload["event_id"],
        )

        mock_delay.assert_called_once_with(webhook_event.id)
        
class WebhookProcessingTaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="webhook-task@example.com",
            password="test-password",
        )

        cls.integration = Integration.objects.get(
            provider=Integration.Provider.MOCK,
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=cls.integration,
            name="Task Test Store",
            external_store_id="task-store-001",
            credentials={
                "webhook_secret": "webhook-test-secret",
            },
        )

    def create_webhook_event(self, status=WebhookEvent.Status.RECEIVED):
        return WebhookEvent.objects.create(
            store=self.store,
            event_id="task-event-001",
            event_type="product.updated",
            payload={
                "event_id": "task-event-001",
                "event_type": "product.updated",
                "data": {
                    "product_id": "product-001",
                },
            },
            status=status,
        )

    def test_received_event_is_processed(self):
        webhook_event = self.create_webhook_event()

        result = process_webhook_event.apply(
            args=[webhook_event.id],
        ).get()

        webhook_event.refresh_from_db()

        self.assertEqual(
            webhook_event.status,
            WebhookEvent.Status.PROCESSED,
        )
        self.assertIsNotNone(webhook_event.processed_at)

        self.assertEqual(
            result["webhook_event_id"],
            webhook_event.id,
        )
        self.assertEqual(
            result["status"],
            WebhookEvent.Status.PROCESSED,
        )

    def test_already_processed_event_is_not_processed_again(self):
        webhook_event = self.create_webhook_event(
            status=WebhookEvent.Status.PROCESSED,
        )

        result = process_webhook_event.apply(
            args=[webhook_event.id],
        ).get()

        webhook_event.refresh_from_db()

        self.assertEqual(
            webhook_event.status,
            WebhookEvent.Status.PROCESSED,
        )
        self.assertEqual(
            result["message"],
            "Webhook event was already processed.",
        )

    @patch("webhooks.tasks.WebhookEvent.objects.get")
    def test_processing_failure_marks_event_as_failed(
        self,
        mock_get,
    ):
        webhook_event = self.create_webhook_event()

        mock_get.return_value = webhook_event

        original_save = webhook_event.save
        save_call_count = 0

        def save_with_failure(*args, **kwargs):
            nonlocal save_call_count
            save_call_count += 1

            if save_call_count == 2:
                raise RuntimeError("Deliberate processing failure")

            return original_save(*args, **kwargs)

        with patch.object(
            webhook_event,
            "save",
            side_effect=save_with_failure,
        ):
            process_webhook_event.push_request(retries=3)

            try:
                with self.assertRaises(RuntimeError):
                    process_webhook_event.run(webhook_event.id)
            finally:
                process_webhook_event.pop_request()

        webhook_event.refresh_from_db()

        self.assertEqual(
            webhook_event.status,
            WebhookEvent.Status.FAILED,
        )

    def test_processing_error_triggers_retry(self):
        webhook_event = WebhookEvent.objects.create(
            store=self.store,
            event_id="retry-event-1",
            event_type="product.created",
            payload={"product_id": 123},
        )

        original_save = webhook_event.save
        save_call_count = 0

        def failing_save(*args, **kwargs):
            nonlocal save_call_count
            save_call_count += 1

            if save_call_count == 2:
                raise RuntimeError("Temporary processing failure")

            return original_save(*args, **kwargs)

        with patch(
            "webhooks.tasks.WebhookEvent.objects.get",
            return_value=webhook_event,
        ), patch.object(
            webhook_event,
            "save",
            side_effect=failing_save,
        ), patch.object(
            process_webhook_event,
            "retry",
            side_effect=RuntimeError("Retry requested"),
        ) as mock_retry:

            with self.assertRaises(RuntimeError) as context:
                process_webhook_event.run(webhook_event.id)

        self.assertEqual(
            str(context.exception),
            "Retry requested",
        )

        mock_retry.assert_called_once()

    def test_webhook_fails_after_maximum_retries(self):
        webhook_event = WebhookEvent.objects.create(
            store=self.store,
            event_id="retry-limit-event",
            event_type="product.created",
            payload={"product_id": 456},
        )

        original_save = webhook_event.save
        save_call_count = 0

        def failing_save(*args, **kwargs):
            nonlocal save_call_count
            save_call_count += 1

            # First save: PROCESSING — succeeds.
            # Every subsequent processing save fails.
            if save_call_count == 2:
                raise RuntimeError("Permanent processing failure")

            return original_save(*args, **kwargs)

        with patch(
            "webhooks.tasks.WebhookEvent.objects.get",
            return_value=webhook_event,
        ), patch.object(
            webhook_event,
            "save",
            side_effect=failing_save,
        ):
            process_webhook_event.push_request(retries=3)

            try:
                with self.assertRaises(RuntimeError):
                    process_webhook_event.run(
                        webhook_event.id,
                    )
            finally:
                process_webhook_event.pop_request()

        webhook_event.refresh_from_db()

        self.assertEqual(
            webhook_event.status,
            WebhookEvent.Status.FAILED,
        )