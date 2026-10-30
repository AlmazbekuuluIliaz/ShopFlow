from rest_framework import serializers

from .models import DeliveryTier, Order, OrderItem


class DeliveryTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryTier
        fields = ("id", "min_subtotal", "price")


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
    items_total = serializers.FloatField(read_only=True)
    total_price = serializers.FloatField(read_only=True)
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "username",
            "status",
            "is_paid",
            "paid_at",
            "contact_name",
            "phone",
            "address",
            "comment",
            "delivery_price",
            "discount",
            "items",
            "items_total",
            "total_price",
            "created_at",
            "updated_at",
        )
        # The server owns all of these: user comes from the request, status
        # starts at PENDING and only an admin may change it afterwards.
        read_only_fields = (
            "user",
            "status",
            "is_paid",
            "paid_at",
            "contact_name",
            "phone",
            "address",
            "comment",
            "delivery_price",
            "discount",
            "created_at",
            "updated_at",
        )


class CheckoutSerializer(serializers.Serializer):
    contact_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(max_length=255)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)


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
        if value != Order.Status.CANCELLED and not self.instance.is_paid:
            raise serializers.ValidationError(
                "Неоплаченный заказ можно только отменить. Сначала отметьте оплату."
            )
        return value
