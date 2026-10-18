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
