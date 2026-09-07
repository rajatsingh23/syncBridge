from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import MockProduct, MockInventory
from .serializers import MockProductSerializer, MockInventorySerializer

class MockProductListView(generics.ListAPIView):
    queryset = MockProduct.objects.all()
    serializer_class = MockProductSerializer
    permission_classes = [AllowAny]

class MockInventoryListView(generics.ListAPIView):
    queryset = MockInventory.objects.select_related("variant")
    serializer_class = MockInventorySerializer
    permission_classes = [AllowAny]