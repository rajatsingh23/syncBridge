from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path("api/", include("stores.urls")),
    path("api/", include("products.urls")),
    path("api/mock-store/", include("mock_store.urls")),
    path("api/integrations", include("integrations.urls")),
]
