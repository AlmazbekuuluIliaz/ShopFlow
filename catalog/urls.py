from django.urls import path

from .views import (
    CategoryDetailAPIView,
    CategoryListCreateAPIView,
    ProductDetailAPIView,
    ProductImageDetailAPIView,
    ProductImageListCreateAPIView,
    ProductListCreateAPIView,
)

urlpatterns = [
    path("categories/", CategoryListCreateAPIView.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryDetailAPIView.as_view(), name="category-detail"),
    path("products/", ProductListCreateAPIView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
    path("products/<int:pk>/images/", ProductImageListCreateAPIView.as_view(), name="product-image-list"),
    path("product-images/<int:pk>/", ProductImageDetailAPIView.as_view(), name="product-image-detail"),
]
