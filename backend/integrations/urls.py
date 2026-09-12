from django.urls import path
from integrations.views import ShopifyOAuthStartView, ShopifyOAuthCallbackView


urlpatterns = [
    path(
        "shopify/connect",
        ShopifyOAuthStartView.as_view(),
        name="shopify-oauth-start",
    ),
    path(
        "shopify/callback/",
        ShopifyOAuthCallbackView.as_view(),
        name="shopify-oauth-callback",
    )
]