from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Product, Variant, Inventory, ExternalVariant, ExternalProduct
from.serializers import ProductSerializer, VariantSerializer, InventorySerializer, ExternalProductSerializer, ExternalVariantSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user)
    
    def perform_create(self,serializer):
        serializer.save(owner=self.request.user)

class VariantViewSet(viewsets.ModelViewSet):
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Variant.objects.filter(product__owner=self.request.user)
    def perform_create(self, serializer):
        product = serializer.validated_data["product"]

        if product.owner != self.request.user:
            raise PermissionDenied("You do not have permission to add variants to this product.")
        serializer.save()

class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Inventory.objects.filter(
            variant__product__owner=self.request.user,
            store__user=self.request.user,
        )

    def perform_create(self, serializer):
        variant = serializer.validated_data["variant"]
        store = serializer.validated_data["store"]

        if variant.product.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to manage this variant"
            )

        if store.user != self.request.user:
            raise PermissionDenied(
                "You do not have permission to manage this store."
            )

        serializer.save()

class ExternalProductViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExternalProduct.objects.filter(
            product__owner=self.request.user,
            store__user=self.request.user,
        )

    def perform_create(self, serializer):
        product = serializer.validated_data["product"]
        store = serializer.validated_data["store"]

        if product.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to manage this product."
            )

        if store.user != self.request.user:
            raise PermissionDenied(
                "You do not have permissions to manage this store."
            )

        serializer.save()

class ExternalVariantViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalVariantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExternalVariant.objects.filter(
            variant__product__owner=self.request.user,
            store__user=self.request.user,
        )

    def perform_create(self, serializer):
        variant = serializer.validated_data["variant"]
        store = serializer.validated_data["store"]

        if variant.product.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to tmanage this variant."
            )

        if store.user != self.request.user:
            raise PermissionDenied(
                "You do not have permission to manage this store."
            )

        serializer.save()