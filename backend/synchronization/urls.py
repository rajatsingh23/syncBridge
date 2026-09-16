from rest_framework.routers import DefaultRouter

from synchronization.views import SyncJobViewSet


router = DefaultRouter()

router.register(
    "jobs",
    SyncJobViewSet,
    basename="sync-job",
)

urlpatterns = router.urls