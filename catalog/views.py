from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer, ProductShortSerializer


def _is_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_admin))


class CategoryListCreateAPIView(APIView):
    """GET: list categories (anyone). POST: create (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(operation_id="categories_list", responses=CategorySerializer(many=True))
    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)

    @extend_schema(operation_id="categories_create", request=CategorySerializer, responses=CategorySerializer)
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailAPIView(APIView):
    """GET one (anyone). PUT/DELETE (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(operation_id="categories_retrieve", responses=CategorySerializer)
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        return Response(CategorySerializer(category).data)

    @extend_schema(operation_id="categories_update", request=CategorySerializer, responses=CategorySerializer)
    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(operation_id="categories_destroy", responses={204: None})
    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListCreateAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer

    ALLOWED_ORDERING = {
        "price", "-price", "name", "-name", "created_at", "-created_at",
    }

    @extend_schema(
        operation_id="products_list",
        responses=ProductSerializer(many=True),
        parameters=[
            OpenApiParameter("search", str, description="Поиск по названию товара."),
            OpenApiParameter("category", int, description="ID категории."),
            OpenApiParameter("min_price", str, description="Минимальная цена."),
            OpenApiParameter("max_price", str, description="Максимальная цена."),
            OpenApiParameter(
                "ordering", str,
                description="price, -price, name, -name, created_at, -created_at",
            ),
        ],
    )
    def get(self, request):
        products = Product.objects.select_related("category").all()
        if not _is_admin(request.user):
            products = products.filter(available=True)

        search = request.query_params.get("search")
        if search:
            products = products.filter(name__icontains=search)

        category = request.query_params.get("category")
        if category:
            if not category.isdigit():
                return Response(
                    {"detail": "category must be an integer id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            products = products.filter(category_id=int(category))

        for param, lookup in (("min_price", "price__gte"), ("max_price", "price__lte")):
            raw = request.query_params.get(param)
            if raw is None:
                continue
            try:
                value = Decimal(raw)
            except (InvalidOperation, TypeError):
                return Response(
                    {"detail": f"{param} must be a number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            products = products.filter(**{lookup: value})

        ordering = request.query_params.get("ordering")
        if ordering:
            if ordering not in self.ALLOWED_ORDERING:
                allowed = ", ".join(sorted(self.ALLOWED_ORDERING))
                return Response(
                    {"detail": f"ordering must be one of: {allowed}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            products = products.order_by(ordering)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        page = paginator.paginate_queryset(products, request, view=self)
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(operation_id="products_create", request=ProductSerializer, responses=ProductSerializer)
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(APIView):
    """GET one (anyone). PUT/DELETE (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(operation_id="products_retrieve", responses=ProductSerializer)
    def get(self, request, pk):
        queryset = Product.objects.select_related("category")
        if not _is_admin(request.user):
            queryset = queryset.filter(available=True)
        product = get_object_or_404(queryset, pk=pk)

        related = (
            Product.objects.filter(category=product.category, available=True)
            .exclude(pk=product.pk)[:6]
        )

        data = ProductSerializer(product).data
        data["related"] = ProductShortSerializer(related, many=True).data
        return Response(data)

    @extend_schema(operation_id="products_update", request=ProductSerializer, responses=ProductSerializer)
    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(operation_id="products_destroy", responses={204: None})
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
