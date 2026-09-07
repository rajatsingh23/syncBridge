from django.urls import path

from .views import (
    MockProductListView,
    MockInventoryListView,
    MockInventoryUpdateView,
    MockOrderListView,
)

urlpatterns = [
    path("products/", MockProductListView.as_view(), name="mock-product-list"),
    path("inventory/", MockInventoryListView.as_view(), name="mock-inventory-list"),
    path("orders/", MockOrderListView.as_view(), name="mock-order-list"),
    path("inventory/<str:external_variant_id>/", MockInventoryUpdateView.as_view(), name="mock-inventory-update")
]