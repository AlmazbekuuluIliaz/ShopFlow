"""Admin-only actions added in the in-service admin: order delete, product images."""
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from catalog.models import Category, Product
from orders.models import Order

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="admin1", password="pass12345", is_staff=True, is_superuser=True
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(username="cust1", password="pass12345")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        category=category, product_type="BOOK", name="Book", slug="book",
        price="10.00", stock=5, available=True,
    )


def make_image():
    buf = BytesIO()
    Image.new("RGB", (2, 2), "red").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile("t.png", buf.read(), content_type="image/png")


def test_admin_can_delete_order(api, admin, customer):
    order = Order.objects.create(user=customer)
    api.force_authenticate(admin)
    r = api.delete(f"/api/orders/{order.id}/")
    assert r.status_code == 204
    assert not Order.objects.filter(id=order.id).exists()


def test_customer_cannot_delete_own_order(api, customer):
    order = Order.objects.create(user=customer)
    api.force_authenticate(customer)
    r = api.delete(f"/api/orders/{order.id}/")
    assert r.status_code == 403
    assert Order.objects.filter(id=order.id).exists()


def test_admin_can_add_and_delete_product_image(api, admin, product, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    api.force_authenticate(admin)
    r = api.post(f"/api/products/{product.id}/images/", {"image": make_image()}, format="multipart")
    assert r.status_code == 201
    image_id = r.json()["id"]
    assert product.images.count() == 1

    r2 = api.delete(f"/api/product-images/{image_id}/")
    assert r2.status_code == 204
    assert product.images.count() == 0


def test_customer_cannot_add_product_image(api, customer, product):
    api.force_authenticate(customer)
    r = api.post(f"/api/products/{product.id}/images/", {"image": make_image()}, format="multipart")
    assert r.status_code == 403
    assert product.images.count() == 0


def test_guest_can_list_product_images(api, product):
    r = api.get(f"/api/products/{product.id}/images/")
    assert r.status_code == 200
    assert r.json() == []
