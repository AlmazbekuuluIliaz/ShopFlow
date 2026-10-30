from django.contrib import admin

from .models import DeliveryTier, Order, OrderItem


@admin.register(DeliveryTier)
class DeliveryTierAdmin(admin.ModelAdmin):
    list_display = ("min_subtotal", "price")
    list_editable = ("price",)
    ordering = ("min_subtotal",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("subtotal",)

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("id", "user__username", "user__email")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    inlines = (OrderItemInline,)

    @admin.display(description="Total")
    def total_price(self, obj):
        return obj.total_price
