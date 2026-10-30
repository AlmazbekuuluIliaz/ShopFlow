"""Roles & per-user data isolation (spec section 4)."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product

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
def customer2(db):
    return User.objects.create_user(username="cust2", password="pass12345")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        category=category, name="Book", slug="book",
        price="10.00", stock=5, available=True,
    )


# --- Catalog: read open, write admin-only ---------------------------------

def test_guest_can_read_catalog(api, product):
    r = api.get("/api/products/")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert len(body["results"]) == 1


def test_customer_cannot_create_product(api, customer, category):
    api.force_authenticate(customer)
    r = api.post(
        "/api/products/",
        {"category": category.id, "name": "X", "slug": "x", "price": "1.00", "stock": 1},
        format="json",
    )
    assert r.status_code == 403


def test_admin_can_create_product(api, admin, category):
    api.force_authenticate(admin)
    r = api.post(
        "/api/products/",
        {"category": category.id, "product_type": "BOOK", "name": "X", "slug": "x", "price": "1.00", "stock": 1},
        format="json",
    )
    assert r.status_code == 201


def test_product_type_is_required(api, admin, category):
    api.force_authenticate(admin)
    r = api.post(
        "/api/products/",
        {"category": category.id, "name": "Y", "slug": "y", "price": "1.00", "stock": 1},
        format="json",
    )
    assert r.status_code == 400


# --- Cart: isolation + stock ----------------------------------------------

def test_cart_is_isolated_between_users(api, customer, customer2, product):
    api.force_authenticate(customer)
    api.post("/api/cart/", {"product": product.id, "quantity": 2}, format="json")

    api.force_authenticate(customer2)
    assert api.get("/api/cart/").json()["total_quantity"] == 0


def test_cart_rejects_over_stock(api, customer, product):
    api.force_authenticate(customer)
    r = api.post("/api/cart/", {"product": product.id, "quantity": 99}, format="json")
    assert r.status_code == 400


# --- Orders: checkout, isolation, status ----------------------------------

def test_checkout_freezes_price_and_decrements_stock(api, customer, product):
    api.force_authenticate(customer)
    api.post("/api/cart/", {"product": product.id, "quantity": 2}, format="json")

    r = api.post("/api/orders/", {}, format="json")
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "PENDING"
    assert str(data["items"][0]["price"]) == "10.00"

    product.refresh_from_db()
    assert product.stock == 3  # 5 - 2
    assert api.get("/api/cart/").json()["total_quantity"] == 0  # cart emptied


def test_checkout_empty_cart_is_rejected(api, customer):
    api.force_authenticate(customer)
    r = api.post("/api/orders/", {}, format="json")
    assert r.status_code == 400


def test_customer_sees_only_own_orders(api, customer, customer2, product):
    api.force_authenticate(customer)
    api.post("/api/cart/", {"product": product.id, "quantity": 1}, format="json")
    oid = api.post("/api/orders/", {}, format="json").json()["id"]

    api.force_authenticate(customer2)
    assert api.get("/api/orders/").json() == []
    assert api.get(f"/api/orders/{oid}/").status_code == 404  # foreign order hidden


def test_only_admin_changes_status(api, admin, customer, product):
    api.force_authenticate(customer)
    api.post("/api/cart/", {"product": product.id, "quantity": 1}, format="json")
    oid = api.post("/api/orders/", {}, format="json").json()["id"]

    # Customer may not change status.
    assert api.patch(f"/api/orders/{oid}/", {"status": "CONFIRMED"}, format="json").status_code == 403

    # Admin sees the order and can change its status.
    api.force_authenticate(admin)
    assert any(o["id"] == oid for o in api.get("/api/orders/").json())
    assert api.post(f"/api/orders/{oid}/pay/", {}, format="json").status_code == 200
    r = api.patch(f"/api/orders/{oid}/", {"status": "CONFIRMED"}, format="json")
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"
