from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from synchronization.models import SyncJob
from synchronization.serializers import SyncJobSerializer


class SyncJobViewSet(ReadOnlyModelViewSet):
    serializer_class = SyncJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            SyncJob.objects
            .filter(store__user=self.request.user)
            .select_related("store")
            .prefetch_related("errors")
            .order_by("-created_at")
        )