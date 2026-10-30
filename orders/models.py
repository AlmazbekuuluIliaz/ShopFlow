from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone


class DeliveryTier(models.Model):
    min_subtotal = models.DecimalField(max_digits=10, decimal_places=2, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["min_subtotal"]

    def __str__(self):
        return f"от {self.min_subtotal} → доставка {self.price}"

    @staticmethod
    def price_for(subtotal):
        tier = (
            DeliveryTier.objects.filter(min_subtotal__lte=subtotal)
            .order_by("-min_subtotal")
            .first()
        )
        return tier.price if tier else 0


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
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    contact_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.user})"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def pay(self):
        from rest_framework.exceptions import ValidationError

        if self.is_paid:
            raise ValidationError("Заказ уже оплачен.")
        if self.status == self.Status.CANCELLED:
            raise ValidationError("Нельзя оплатить отменённый заказ.")

        self.is_paid = True
        self.paid_at = timezone.now()
        self.save(update_fields=["is_paid", "paid_at", "updated_at"])

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
    def items_total(self):
        return sum((item.subtotal for item in self.items.all()), 0)

    @property
    def total_price(self):
        return self.items_total + self.delivery_price - self.discount


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
