from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("added_at", "subtotal")

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_quantity", "total_price", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartItemInline,)

    @admin.display(description="Items")
    def total_quantity(self, obj):
        return obj.total_quantity

    @admin.display(description="Total")
    def total_price(self, obj):
        return obj.total_price
