from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, VariantViewSet, InventoryViewSet, ExternalProductViewSet, ExternalVariantViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("variants", VariantViewSet, basename="variant")
router.register("inventory", InventoryViewSet, basename="inventory")
router.register("external-products", ExternalProductViewSet, basename="external-products")
router.register("external-variants", ExternalVariantViewSet, basename="external-variant")
urlpatterns = router.urls