from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer


class CategoryListCreateAPIView(APIView):
    """GET: list categories (anyone). POST: create (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailAPIView(APIView):
    """GET one (anyone). PUT/DELETE (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        return Response(CategorySerializer(category).data)

    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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

    def get(self, request):
        products = Product.objects.select_related("category").all()

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

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(APIView):
    """GET one (anyone). PUT/DELETE (admin only)."""

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
