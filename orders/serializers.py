from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price", "quantity", "subtotal")
        # price is a snapshot captured at checkout, never sent by the client.
        read_only_fields = ("price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "status",
            "items",
            "total_price",
            "created_at",
            "updated_at",
        )
        # The server owns all of these: user comes from the request, status
        # starts at PENDING and only an admin may change it afterwards.
        read_only_fields = ("user", "status", "created_at", "updated_at")


class OrderStatusSerializer(serializers.ModelSerializer):
    """Admin-only: change an order's status (validated against Status choices)."""

    class Meta:
        model = Order
        fields = ("status",)
