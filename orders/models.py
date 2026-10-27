from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.PROCESSING, Status.CANCELLED},
        Status.PROCESSING: {Status.SHIPPED, Status.CANCELLED},
        Status.SHIPPED: {Status.DELIVERED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.user})"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def cancel(self):
        from rest_framework.exceptions import ValidationError

        from catalog.models import Product

        if not self.can_transition_to(self.Status.CANCELLED):
            raise ValidationError(f"Нельзя отменить заказ в статусе «{self.status}».")

        with transaction.atomic():
            for item in self.items.select_related("product"):
                product = Product.objects.select_for_update().get(pk=item.product_id)
                product.stock += item.quantity
                product.save(update_fields=["stock"])
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status", "updated_at"])

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), 0)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.product} @ {self.price}"

    @property
    def subtotal(self):
        return self.price * self.quantity


@receiver(pre_delete, sender=Order)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    if instance.status == Order.Status.CANCELLED:
        return
    from catalog.models import Product
    for item in instance.items.all():
        Product.objects.filter(pk=item.product_id).update(
            stock=models.F("stock") + item.quantity
        )
