import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product
from orders.models import Order, OrderItem

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
def order(db, customer):
    category = Category.objects.create(name="Books", slug="books")
    product = Product.objects.create(
        category=category, name="Book", slug="book", price="10.00", stock=5,
    )
    order = Order.objects.create(user=customer)
    OrderItem.objects.create(order=order, product=product, price="10.00", quantity=1)
    return order


def _patch(api, order, status):
    return api.patch(f"/api/orders/{order.id}/", {"status": status}, format="json")


def test_valid_step_is_accepted(api, admin, order):
    api.force_authenticate(admin)
    r = _patch(api, order, "CONFIRMED")
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"


def test_skipping_steps_is_rejected(api, admin, order):
    api.force_authenticate(admin)
    r = _patch(api, order, "DELIVERED")
    assert r.status_code == 400


def test_full_happy_path(api, admin, order):
    api.force_authenticate(admin)
    for nxt in ("CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"):
        assert _patch(api, order, nxt).status_code == 200


def test_cancel_before_shipping_is_allowed(api, admin, order):
    api.force_authenticate(admin)
    assert _patch(api, order, "CANCELLED").status_code == 200


def test_delivered_is_terminal(api, admin, order):
    api.force_authenticate(admin)
    for nxt in ("CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"):
        _patch(api, order, nxt)
    assert _patch(api, order, "PENDING").status_code == 400
    assert _patch(api, order, "CANCELLED").status_code == 400


def test_customer_cannot_change_status(api, customer, order):
    api.force_authenticate(customer)
    assert _patch(api, order, "CONFIRMED").status_code == 403


def test_patch_to_cancelled_restores_stock(api, admin, customer):
    category = Category.objects.create(name="C", slug="c")
    product = Product.objects.create(category=category, name="P", slug="p", price="10.00", stock=3)
    order = Order.objects.create(user=customer)
    OrderItem.objects.create(order=order, product=product, price="10.00", quantity=2)
    api.force_authenticate(admin)
    r = api.patch(f"/api/orders/{order.id}/", {"status": "CANCELLED"}, format="json")
    assert r.status_code == 200
    product.refresh_from_db()
    assert product.stock == 5


def test_cancel_endpoint_restores_stock_for_owner(api, customer):
    category = Category.objects.create(name="C2", slug="c2")
    product = Product.objects.create(category=category, name="P2", slug="p2", price="10.00", stock=1)
    order = Order.objects.create(user=customer)
    OrderItem.objects.create(order=order, product=product, price="10.00", quantity=4)
    api.force_authenticate(customer)
    r = api.post(f"/api/orders/{order.id}/cancel/", {}, format="json")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"
    product.refresh_from_db()
    assert product.stock == 5


def test_deleting_active_order_restores_stock(api, admin, customer):
    category = Category.objects.create(name="D", slug="d")
    product = Product.objects.create(category=category, name="D1", slug="d1", price="10.00", stock=2)
    order = Order.objects.create(user=customer, status="DELIVERED")
    OrderItem.objects.create(order=order, product=product, price="10.00", quantity=3)
    api.force_authenticate(admin)
    r = api.delete(f"/api/orders/{order.id}/")
    assert r.status_code == 204
    product.refresh_from_db()
    assert product.stock == 5


def test_deleting_cancelled_order_does_not_restore_stock(api, admin, customer):
    category = Category.objects.create(name="E", slug="e")
    product = Product.objects.create(category=category, name="E1", slug="e1", price="10.00", stock=4)
    order = Order.objects.create(user=customer, status="CANCELLED")
    OrderItem.objects.create(order=order, product=product, price="10.00", quantity=2)
    api.force_authenticate(admin)
    r = api.delete(f"/api/orders/{order.id}/")
    assert r.status_code == 204
    product.refresh_from_db()
    assert product.stock == 4
