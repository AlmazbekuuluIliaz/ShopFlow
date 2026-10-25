from rest_framework import serializers

from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt", "position")


class ProductShortSerializer(serializers.ModelSerializer):
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "image", "in_stock")


class ProductSerializer(serializers.ModelSerializer):
    in_stock = serializers.BooleanField(read_only=True)
    category_detail = CategorySerializer(source="category", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specs = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_detail",
            "product_type",
            "name",
            "slug",
            "description",
            "image",
            "images",
            "author",
            "publisher",
            "language",
            "publication_year",
            "pages",
            "cover_type",
            "isbn",
            "issn",
            "issue_number",
            "issue_date",
            "media_format",
            "age_rating",
            "price",
            "stock",
            "available",
            "in_stock",
            "specs",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
