from django.urls import path

from .views import (
    DeliveryTierListAPIView,
    OrderCancelAPIView,
    OrderDetailAPIView,
    OrderListCreateAPIView,
    OrderPayAPIView,
)

urlpatterns = [
    path("delivery-tiers/", DeliveryTierListAPIView.as_view(), name="delivery-tier-list"),
    path("orders/", OrderListCreateAPIView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("orders/<int:pk>/cancel/", OrderCancelAPIView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/pay/", OrderPayAPIView.as_view(), name="order-pay"),
]
