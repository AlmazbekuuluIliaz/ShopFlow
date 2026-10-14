from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "available", "created_at")
    list_filter = ("available", "category", "created_at")
    list_editable = ("price", "stock", "available")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("category",)
