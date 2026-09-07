from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .pagination import MockStorePagination

from django.shortcuts import get_object_or_404

from .models import MockProduct, MockInventory, MockOrder
from .serializers import MockProductSerializer, MockInventorySerializer, MockOrderSerializer

class MockProductListView(generics.ListAPIView):
    queryset = MockProduct.objects.all()
    serializer_class = MockProductSerializer
    permission_classes = [AllowAny]
    pagination_class = MockStorePagination

class MockInventoryListView(generics.ListAPIView):
    queryset = MockInventory.objects.select_related("variant")
    serializer_class = MockInventorySerializer
    permission_classes = [AllowAny]

class MockOrderListView(generics.ListAPIView):
    queryset = MockOrder.objects.all()
    serializer_class = MockOrderSerializer
    permission_classes = [AllowAny]

class MockInventoryUpdateView(generics.UpdateAPIView):
    queryset = MockInventory.objects.select_related("variant")
    serializer_class = MockInventorySerializer
    permission_classes = [AllowAny]

    def get_object(self):
        
        external_variant_id = self.kwargs["external_variant_id"]

        return get_object_or_404(
            self.get_queryset(),
            variant__external_id=external_variant_id,
        )

    def update(self, request, *args, **kwargs):
        inventory = self.get_object()
        quantity = request.data.get("quantity")

        if quantity is None:
            return Response(
                {"error": "quantity is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventory.quantity = quantity
        inventory.save()

        return Response(
            MockInventorySerializer(inventory).data,
            status=status.HTTP_200_OK,
        )