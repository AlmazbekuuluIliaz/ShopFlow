from django.urls import path

from .views import (
    OrderCancelAPIView,
    OrderDetailAPIView,
    OrderListCreateAPIView,
)

urlpatterns = [
    path("orders/", OrderListCreateAPIView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("orders/<int:pk>/cancel/", OrderCancelAPIView.as_view(), name="order-cancel"),
]
