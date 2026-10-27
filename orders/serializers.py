from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    subtotal = serializers.FloatField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price", "quantity", "subtotal")
        # price is a snapshot captured at checkout, never sent by the client.
        read_only_fields = ("price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.FloatField(read_only=True)
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "username",
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
    class Meta:
        model = Order
        fields = ("status",)

    def validate_status(self, value):
        current = self.instance.status
        if value == current:
            return value
        if not self.instance.can_transition_to(value):
            raise serializers.ValidationError(
                f"Нельзя изменить статус с «{current}» на «{value}»."
            )
        return value
