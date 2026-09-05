from rest_framework import serializers

from .models import Store

class StoreSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(
        source="integration.name",
        read_only=True,
    )

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "integration",
            "integration_name",
            "external_store_id",
            "status",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "id",
            "integration_name",
            "created_at",
            "updated_at"
        ]