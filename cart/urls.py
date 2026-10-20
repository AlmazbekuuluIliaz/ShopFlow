from django.urls import path

from .views import CartAPIView, CartItemAPIView

urlpatterns = [
    path("cart/", CartAPIView.as_view(), name="cart-api"),
    path("cart/items/<int:pk>/", CartItemAPIView.as_view(), name="cart-item"),
]
