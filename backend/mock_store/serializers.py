from rest_framework import serializers
from .models import MockProduct, MockVariant, MockInventory

class MockVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockVariant
        fields = [
            "id",
            "external_id",
            "sku",
            "price",
            "currency",
        ]

class MockProductSerializer(serializers.ModelSerializer):
    variants = MockVariantSerializer(many=True, read_only=True)
    class Meta:
        model = MockProduct
        fields = [
            "id",
            "external_id",
            "title",
            "description",
            "variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class MockInventorySerializer(serializers.ModelSerializer):
    external_variant_id = serializers.CharField(
        source="variant.external_id",
        read_only=True,
    )

    sku = serializers.CharField(
        source="variant.sku",
        read_only=True,
    )

    class Meta:
        model = MockInventory
        fields = [
            "id",
            "external_variant_id",
            "sku",
            "quantity",
            "reserved_quantity",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "external_variant_id",
            "sku",
            "updated_at",
        ]