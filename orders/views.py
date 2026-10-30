from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from cart.models import Cart

from .models import DeliveryTier, Order, OrderItem
from .permissions import IsOwnerOrAdmin, is_admin
from .serializers import (
    CheckoutSerializer,
    DeliveryTierSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)


class DeliveryTierListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="delivery_tiers_list",
        responses=DeliveryTierSerializer(many=True),
    )
    def get(self, request):
        tiers = DeliveryTier.objects.all()
        return Response(DeliveryTierSerializer(tiers, many=True).data)


class OrderListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="orders_list", responses=OrderSerializer(many=True))
    def get(self, request):
        # Isolation: a customer sees only their own orders; an admin sees all.
        if is_admin(request.user):
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(user=request.user)
        orders = orders.prefetch_related("items")
        return Response(OrderSerializer(orders, many=True).data)

    @extend_schema(operation_id="orders_create", request=CheckoutSerializer, responses=OrderSerializer)
    def post(self, request):
        """Place an order from the current user's cart."""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._checkout(request, serializer.validated_data)

    @transaction.atomic
    def _checkout(self, request, data):
        cart = Cart.objects.filter(user=request.user).first()
        items = list(cart.items.select_related("product")) if cart else []
        if not items:
            raise ValidationError("Ваша корзина пуста.")

        order = Order.objects.create(
            user=request.user,
            contact_name=data["contact_name"],
            phone=data["phone"],
            address=data["address"],
            comment=data.get("comment", ""),
        )
        for item in items:
            # Lock the product row so two checkouts can't oversell the same stock.
            product = Product.objects.select_for_update().get(pk=item.product_id)
            if item.quantity > product.stock:
                # Raising here rolls back the whole transaction — no partial order.
                raise ValidationError(
                    f"Недостаточно товара «{product.name}»: в наличии {product.stock} шт."
                )
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,  # freeze the price at purchase time
                quantity=item.quantity,
            )
            product.stock -= item.quantity
            product.save(update_fields=["stock"])

        order.delivery_price = DeliveryTier.price_for(order.items_total)
        order.save(update_fields=["delivery_price"])

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

    @extend_schema(operation_id="orders_retrieve", responses=OrderSerializer)
    def get(self, request, pk):
        order = self.get_order(request, pk)
        return Response(OrderSerializer(order).data)

    @extend_schema(operation_id="orders_update_status", request=OrderStatusSerializer, responses=OrderSerializer)
    def patch(self, request, pk):
        order = self.get_order(request, pk)
        # Owners can view their order, but only an admin may change its status.
        if not is_admin(request.user):
            return Response(
                {"detail": "Менять статус заказа может только администратор."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get("status")
        if new_status == Order.Status.CANCELLED and order.status != Order.Status.CANCELLED:
            order.cancel()
        else:
            serializer.save()
        return Response(OrderSerializer(order).data)

    @extend_schema(operation_id="orders_delete", responses={204: None})
    def delete(self, request, pk):
        order = self.get_order(request, pk)
        if not is_admin(request.user):
            return Response(
                {"detail": "Удалять заказы может только администратор."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderCancelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(operation_id="orders_cancel", request=None, responses=OrderSerializer)
    def post(self, request, pk):
        queryset = Order.objects.prefetch_related("items")
        if not is_admin(request.user):
            queryset = queryset.filter(user=request.user)
        order = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, order)
        order.cancel()
        return Response(OrderSerializer(order).data)


class OrderPayAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(operation_id="orders_pay", request=None, responses=OrderSerializer)
    def post(self, request, pk):
        queryset = Order.objects.prefetch_related("items")
        if not is_admin(request.user):
            queryset = queryset.filter(user=request.user)
        order = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, order)
        order.pay()
        return Response(OrderSerializer(order).data)
