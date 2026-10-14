from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from cart.models import Cart

from .models import Order, OrderItem
from .permissions import IsOwnerOrAdmin, is_admin
from .serializers import OrderSerializer, OrderStatusSerializer


class OrderListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Isolation: a customer sees only their own orders; an admin sees all.
        if is_admin(request.user):
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(user=request.user)
        orders = orders.prefetch_related("items")
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        """Place an order from the current user's cart."""
        return self._checkout(request)

    @transaction.atomic
    def _checkout(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        items = list(cart.items.select_related("product")) if cart else []
        if not items:
            raise ValidationError("Your cart is empty.")

        order = Order.objects.create(user=request.user)
        for item in items:
            # Lock the product row so two checkouts can't oversell the same stock.
            product = Product.objects.select_for_update().get(pk=item.product_id)
            if item.quantity > product.stock:
                # Raising here rolls back the whole transaction — no partial order.
                raise ValidationError(
                    f"Not enough stock for '{product.name}': {product.stock} left."
                )
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,  # freeze the price at purchase time
                quantity=item.quantity,
            )
            product.stock -= item.quantity
            product.save(update_fields=["stock"])

        cart.items.all().delete()  # cart is emptied once the order is placed
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_order(self, request, pk):
        # Scope the queryset first: a customer can only ever look inside their
        # own orders, so someone else's id yields 404 — it doesn't even reveal
        # that the order exists. Admins see everything.
        queryset = Order.objects.prefetch_related("items")
        if not is_admin(request.user):
            queryset = queryset.filter(user=request.user)
        order = get_object_or_404(queryset, pk=pk)
        # Second line of defence: object-level permission check.
        self.check_object_permissions(request, order)
        return order

    def get(self, request, pk):
        order = self.get_order(request, pk)
        return Response(OrderSerializer(order).data)

    def patch(self, request, pk):
        order = self.get_order(request, pk)
        # Owners can view their order, but only an admin may change its status.
        if not is_admin(request.user):
            return Response(
                {"detail": "Only an admin can change the order status."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)
