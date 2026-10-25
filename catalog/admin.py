from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt", "position")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "product_type", "category", "price", "stock", "available", "created_at")
    list_display_links = ("thumbnail", "name")
    list_filter = ("product_type", "media_format", "age_rating", "available", "category", "created_at")
    list_editable = ("price", "stock", "available")
    search_fields = ("name", "description", "author", "publisher", "isbn", "issn")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    readonly_fields = ("created_at", "updated_at", "image_preview")
    autocomplete_fields = ("category",)
    inlines = [ProductImageInline]

    fieldsets = (
        ("Основное", {
            "fields": ("product_type", "category", "name", "slug", "description"),
        }),
        ("Изображение", {
            "fields": ("image", "image_preview"),
        }),
        ("Для публики", {
            "classes": ("book-fields",),
            "fields": ("author", "publication_year", "pages", "cover_type", "isbn"),
        }),
        ("Для периодики", {
            "classes": ("periodical-fields",),
            "fields": ("issn", "issue_number", "issue_date"),
        }),
        ("Характеристики", {
            "fields": ("publisher", "language", "media_format", "age_rating"),
        }),
        ("Продажи", {
            "fields": ("price", "stock", "available"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    class Media:
        js = ("catalog/product_admin.js",)

    @admin.display(description="Image")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px;">',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:200px;border-radius:6px;">',
                obj.image.url,
            )
        return "No image uploaded"
