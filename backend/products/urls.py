from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, VariantViewSet, InventoryViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("variants", VariantViewSet, basename="variant")
router.register("inventory", InventoryViewSet, basename="inventory")
urlpatterns = router.urls