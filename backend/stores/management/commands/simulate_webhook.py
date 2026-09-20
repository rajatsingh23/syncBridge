import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from webhooks.services.signature import generate_signature

from django.core.management.base import BaseCommand
from stores.models import Store


class Command(BaseCommand):
    help = "Simulate a mock webhook event."

    def add_arguments(self, parser):
        parser.add_argument(
            "--store-id",
            type=int,
            required=True,
            help="ID of the store receiving the webhook.",
        )

        parser.add_argument(
            "--event-id",
            type=str,
            required=True,
            help="Unique ID of the webhook event.",
        )

        parser.add_argument(
            "--event-type",
            type=str,
            required=True,
            help="Type of webhook event.",
        )

    def handle(self, *args, **options):
        store_id = options["store_id"]
        event_id = options["event_id"]
        event_type = options["event_type"]

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Store with ID {store_id} does not exist."
                )
            )
            return

        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "data": {
                "message": "Simulated webhook event",
            },
        }

        payload_bytes = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        secret = store.credentials.get("webhook_secret")

        if not secret:
            self.stdout.write(
                self.style.ERROR(
                    "Webhook secret is not configured for this store."
                )
            )
            return

        signature = generate_signature(
            payload=payload_bytes,
            secret=secret,
        )
        
        url = "http://127.0.0.1:8000/api/webhooks/mock/"

        request = Request(
            url=url,
            data=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Store-ID": str(store.id),
                "X-Webhook-Signature": signature,
            },
            method="POST",
        )

        try:
            with urlopen(request) as response:
                response_body = response.read().decode("utf-8")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"HTTP Status: {response.status}\n"
                        f"Response: {response_body}"
                    )
                )

        except HTTPError as error:
            error_body = error.read().decode("utf-8")

            self.stdout.write(
                self.style.ERROR(
                    f"HTTP Status: {error.code}\n"
                    f"Response: {error_body}"
                )
            )

        except URLError as error:
            self.stdout.write(
                self.style.ERROR(
                    f"Request failed: {error.reason}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Payload: {payload_bytes.decode('utf-8')}\n"
                f"Signature: {signature}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Store: {store_id}\n"
                f"Event ID: {event_id}\n"
                f"Event Type: {event_type}"
            )
        )