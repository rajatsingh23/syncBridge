from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .pagination import MockStorePagination
import time

from django.shortcuts import get_object_or_404

from .models import MockProduct, MockInventory, MockOrder
from .serializers import MockProductSerializer, MockInventorySerializer, MockOrderSerializer

class MockProductListView(generics.ListAPIView):
    queryset = MockProduct.objects.all()
    serializer_class = MockProductSerializer
    permission_classes = [AllowAny]
    pagination_class = MockStorePagination

    def list(self, request, *args, **kwargs):
        simulate = request.query_params.get("simulate")
        if simulate == "slow":
            time.sleep(12)
            
        if simulate == "401":
            return Response(
                {"detail": "Authentication failed ."},
                status = status.HTTP_401_UNAUTHORIZED
            )
        if simulate == "404":
            return Response(
                {"detail": "Resource not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if simulate == "429":
            return Response(
                {"detail": "Rate limit exceeded."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        if simulate == "500":
            return Response(
                {"detail": "Internal server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
        return super().list(request, *args, *kwargs)

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