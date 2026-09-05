from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Product, Variant
from.serializers import ProductSerializer, VariantSerializer

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
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to add variants to this product.")
        serializer.save()
    