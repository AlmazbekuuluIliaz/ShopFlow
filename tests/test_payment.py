import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

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
def order(db, customer):
    return Order.objects.create(user=customer)


def _pay(api, order):
    return api.post(f"/api/orders/{order.id}/pay/", {}, format="json")


def test_owner_can_pay_order(api, customer, order):
    api.force_authenticate(customer)
    r = _pay(api, order)
    assert r.status_code == 200
    body = r.json()
    assert body["is_paid"] is True
    assert body["paid_at"] is not None


def test_paying_twice_is_rejected(api, customer, order):
    api.force_authenticate(customer)
    _pay(api, order)
    assert _pay(api, order).status_code == 400


def test_cannot_pay_cancelled_order(api, customer, order):
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    api.force_authenticate(customer)
    assert _pay(api, order).status_code == 400
    order.refresh_from_db()
    assert order.is_paid is False


def test_customer_cannot_pay_foreign_order(api, customer, order):
    other = User.objects.create_user(username="cust2", password="pass12345")
    api.force_authenticate(other)
    assert _pay(api, order).status_code == 404
