from django.urls import path

from .views import MockProductListView, MockInventoryListView


urlpatterns = [
    path("products/", MockProductListView.as_view(), name="mock-product-list"),
    path("inventory/", MockInventoryListView.as_view(), name="mock-inventory-list"),
]