from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, VariantViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("variants", VariantViewSet, basename="variant")

urlpatterns = router.urls