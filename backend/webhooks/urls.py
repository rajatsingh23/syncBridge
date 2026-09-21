from django.urls import path

from webhooks.views import MockWebhookView, ShopifyWebhookView, WooCommerceWebhookView

urlpatterns = [
    path("mock/", MockWebhookView.as_view(), name="mock-webhook"),
    path("shopify/", ShopifyWebhookView.as_view(), name="shopify-webhook"),
    path("woocommerce/", WooCommerceWebhookView.as_view(), name="woocommerce-webhook")
]