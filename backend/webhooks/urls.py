from django.urls import path

from webhooks.views import MockWebhookView

urlpatterns = [
    path("mock/", MockWebhookView.as_view(), name="mock-webhook"),
]