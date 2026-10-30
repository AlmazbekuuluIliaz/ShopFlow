"""Order cancellation, status transitions, JWT logout, /me, register validation."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product
from orders.models import Order

User = get_user_model()
PASSWORD = "pass12345xyz"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="xadmin", password=PASSWORD, is_staff=True, is_superuser=True
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(username="xcust", password=PASSWORD)


@pytest.fixture
def customer2(db):
    return User.objects.create_user(username="xcust2", password=PASSWORD)


@pytest.fixture
def product(db):
    category = Category.objects.create(name="C", slug="c-extra")
    return Product.objects.create(
        category=category, name="P", slug="p-extra",
        price="10.00", stock=5, available=True,
    )


def _place_order(api, user, product, qty=2):
    api.force_authenticate(user)
    api.post("/api/cart/", {"product": product.id, "quantity": qty}, format="json")
    return api.post("/api/orders/", {}, format="json").json()["id"]


# --- order cancellation ---

def test_owner_cancels_pending_order_and_stock_restored(api, customer, product):
    oid = _place_order(api, customer, product, qty=2)
    product.refresh_from_db()
    assert product.stock == 3

    r = api.post(f"/api/orders/{oid}/cancel/", format="json")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"

    product.refresh_from_db()
    assert product.stock == 5


def test_cannot_cancel_shipped_order(api, customer, product):
    oid = _place_order(api, customer, product, qty=1)
    Order.objects.filter(pk=oid).update(status="DELIVERED")
    r = api.post(f"/api/orders/{oid}/cancel/", format="json")
    assert r.status_code == 400


def test_cannot_cancel_foreign_order(api, customer, customer2, product):
    oid = _place_order(api, customer, product, qty=1)
    api.force_authenticate(customer2)
    assert api.post(f"/api/orders/{oid}/cancel/", format="json").status_code == 404


# --- status transition validation ---

def test_invalid_status_transition_rejected(api, admin, customer, product):
    oid = _place_order(api, customer, product, qty=1)
    api.force_authenticate(admin)
    r = api.patch(f"/api/orders/{oid}/", {"status": "DELIVERED"}, format="json")
    assert r.status_code == 400


def test_valid_status_transition(api, admin, customer, product):
    oid = _place_order(api, customer, product, qty=1)
    api.force_authenticate(admin)
    api.post(f"/api/orders/{oid}/pay/", {}, format="json")
    r = api.patch(f"/api/orders/{oid}/", {"status": "CONFIRMED"}, format="json")
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"


# --- JWT logout / blacklist ---

def test_logout_blacklists_refresh_token(api, customer):
    tokens = api.post(
        "/api/auth/token/", {"username": "xcust", "password": PASSWORD}, format="json"
    ).json()
    refresh = tokens["refresh"]

    assert api.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code == 200
    r = api.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
    assert r.status_code == 401


# --- profile ---

def test_me_returns_current_user(api, customer):
    api.force_authenticate(customer)
    r = api.get("/api/users/me/")
    assert r.status_code == 200
    assert r.json()["username"] == "xcust"


# --- register validation ---

def test_register_rejects_weak_password(api, db):
    r = api.post("/api/auth/register/", {"username": "newbie", "password": "123"}, format="json")
    assert r.status_code == 400


def test_register_rejects_duplicate_username(api, customer):
    r = api.post("/api/auth/register/", {"username": "xcust", "password": PASSWORD}, format="json")
    assert r.status_code == 400
