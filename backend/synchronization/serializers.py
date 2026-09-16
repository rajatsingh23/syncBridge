from rest_framework import serializers

from synchronization.models import SyncError, SyncJob


class SyncErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncError
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "error_type",
            "status_code",
            "message",
            "retry_count",
            "resolved",
            "created_at",
        ]


class SyncJobSerializer(serializers.ModelSerializer):
    errors = SyncErrorSerializer(many=True, read_only=True)

    class Meta:
        model = SyncJob
        fields = [
            "id",
            "store",
            "sync_type",
            "status",
            "total_items",
            "processed_items",
            "successful_items",
            "failed_items",
            "started_at",
            "completed_at",
            "created_at",
            "errors",
        ]
        read_only_fields = fields