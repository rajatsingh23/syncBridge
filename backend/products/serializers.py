from rest_framework import serializers

from .models import Product, Variant, Inventory, ExternalProduct, ExternalVariant

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]

class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = [
            "id",
            "product",
            "sku",
            "title",
            "price",
            "currency",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = [
            "id",
            "variant",
            "store",
            "quantity",
            "reserved_quantity",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "updated_at",
        ]

class ExternalProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProduct
        fields = [
            "id",
            "product",
            "store",
            "external_id",
            "external_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class ExternalVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalVariant
        fields = [
            "id",
            "variant",
            "store",
            "external_id",
            "external_data",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]