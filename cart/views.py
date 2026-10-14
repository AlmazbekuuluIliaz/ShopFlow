from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import AddCartItemSerializer, CartSerializer


def get_user_cart(user):
    """The caller's own cart, created on first access."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartAPIView(APIView):
    """The current user's cart.

    No cart id is ever accepted from the client: we always resolve the cart
    from request.user, so one user can never read or change another's cart.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_user_cart(request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        """Add a product to the cart, or increase its quantity if present."""
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        cart = get_user_cart(request.user)
        item = cart.items.filter(product=product).first()
        new_qty = (item.quantity if item else 0) + quantity

        # Stock validation (spec requirement) against the resulting quantity.
        if not product.available:
            return Response(
                {"detail": "Product is not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_qty > product.stock:
            return Response(
                {"detail": f"Only {product.stock} left in stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item:
            item.quantity = new_qty
            item.save()
        else:
            cart.items.create(product=product, quantity=quantity)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemAPIView(APIView):
    """Update the quantity of, or remove, a single line in the user's cart."""

    permission_classes = [IsAuthenticated]

    def get_item(self, request, pk):
        # Scoped to the caller's own cart: an id from someone else's cart
        # simply yields 404 — the core of per-user data isolation.
        cart = get_user_cart(request.user)
        return get_object_or_404(CartItem, pk=pk, cart=cart)

    def patch(self, request, pk):
        item = self.get_item(request, pk)
        try:
            quantity = int(request.data.get("quantity"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "quantity must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quantity < 1:
            return Response(
                {"detail": "quantity must be >= 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quantity > item.product.stock:
            return Response(
                {"detail": f"Only {item.product.stock} left in stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.quantity = quantity
        item.save()
        return Response(CartSerializer(item.cart).data)

    def delete(self, request, pk):
        item = self.get_item(request, pk)
        cart = item.cart
        item.delete()
        return Response(CartSerializer(cart).data)
