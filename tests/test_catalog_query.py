import pytest
from rest_framework.test import APIClient

from catalog.models import Category, Product


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def books(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def toys(db):
    return Category.objects.create(name="Toys", slug="toys")


@pytest.fixture
def products(db, books, toys):
    return [
        Product.objects.create(category=books, name="Django Book", slug="django-book", price="30.00", stock=5),
        Product.objects.create(category=books, name="Python Book", slug="python-book", price="50.00", stock=5),
        Product.objects.create(category=toys, name="Toy Car", slug="toy-car", price="10.00", stock=5),
    ]


def test_search_by_name(api, products):
    r = api.get("/api/products/?search=python")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["results"]]
    assert names == ["Python Book"]


def test_filter_by_category(api, products, books):
    r = api.get(f"/api/products/?category={books.id}")
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_filter_by_price_range(api, products):
    r = api.get("/api/products/?min_price=20&max_price=40")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["results"]]
    assert names == ["Django Book"]


def test_ordering_by_price(api, products):
    r = api.get("/api/products/?ordering=price")
    prices = [p["price"] for p in r.json()["results"]]
    assert prices == sorted(prices)


def test_invalid_ordering_is_rejected(api, products):
    r = api.get("/api/products/?ordering=stock")
    assert r.status_code == 400


def test_invalid_price_is_rejected(api, products):
    r = api.get("/api/products/?min_price=abc")
    assert r.status_code == 400


def test_pagination_shape(api, products):
    r = api.get("/api/products/")
    body = r.json()
    assert set(body) >= {"count", "next", "previous", "results"}
    assert body["count"] == 3
