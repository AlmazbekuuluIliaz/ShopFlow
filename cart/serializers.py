from rest_framework import serializers

from catalog.models import Product

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """One line in the cart (read view)."""

    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField(source="product.price")
    image = serializers.ImageField(source="product.image", read_only=True)
    stock = serializers.ReadOnlyField(source="product.stock")
    subtotal = serializers.FloatField(read_only=True)

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "product_name",
            "image",
            "stock",
            "price",
            "quantity",
            "subtotal",
            "added_at",
        )
        read_only_fields = ("added_at",)


class CartSerializer(serializers.ModelSerializer):
    """The whole cart: its lines plus computed totals."""

    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.FloatField(read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "total_price", "total_quantity", "updated_at")


class AddCartItemSerializer(serializers.Serializer):
    """Input for adding/updating a cart line. Stock is checked in the view,
    where the resulting quantity (existing + new) is known."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1, default=1)
