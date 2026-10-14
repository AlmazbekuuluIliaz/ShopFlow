from django.urls import path

from .views import OrderDetailAPIView, OrderListCreateAPIView

urlpatterns = [
    path("orders/", OrderListCreateAPIView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
]
