import json
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from stores.models import Store, Integration
from webhooks.models import WebhookEvent
from webhooks.services.signature import verify_signature


class MockWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        store_id = request.headers.get("X-Store-ID")
        signature = request.headers.get("X-Webhook-Signature")

        if not store_id:
            return Response(
                {"detail": "X-Store-ID header is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not signature:
            return Response(
                {"detail": "X-Webhook-Signature header is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        store = get_object_or_404(
            Store.objects.select_related("integration"),
            id=store_id,
        )

        if store.integration.provider != Integration.Provider.MOCK:
            return Response(
                {"detail": "Invalid provider for this webhook endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        secret = store.credentials.get("webhook_secret")

        if not secret:
            return Response(
                {"detail": "Webhook secret is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not verify_signature(
            payload=request.body,
            signature=signature,
            secret=secret,
        ):
            return Response(
                {"detail": "Invalid webhook signature."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(
                {"detail": "Invalid JSON payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_id = payload.get("event_id")
        event_type = payload.get("event_type")

        if not event_id:
            return Response(
                {"detail": "event_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not event_type:
            return Response(
                {"detail": "event_type is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_event = WebhookEvent.objects.filter(
            store=store,
            event_id=event_id,
        ).first()

        if existing_event:
            return Response(
                {
                    "detail": "Webhook event already received.",
                    "event_id": event_id,
                },
                status=status.HTTP_200_OK,
            )

        WebhookEvent.objects.create(
            store=store,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=WebhookEvent.Status.RECEIVED,
        )

        try:
            with transaction.atomic():
                WebhookEvent.objects.create(
                    store=store,
                    event_id=event_id,
                    event_type=event_type,
                    payload=payload,
                    status=WebhookEvent.Status.RECEIVED,
                )
        except IntegrityError:
            return Response(
                {
                    "detail": "Webhook received.",
                    "event_id": event_id,
                },
                status=status.HTTP_200_OK,
            )