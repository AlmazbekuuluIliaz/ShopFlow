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


def test_product_detail_has_category_object_and_specs(api, books):
    p = Product.objects.create(
        category=books, name="Django Book", slug="dj", price="30.00", stock=5,
        product_type="BOOK", author="A. Author", publisher="O'Reilly",
        language="Русский", publication_year=2024, pages=350, isbn="978-5",
    )
    r = api.get(f"/api/products/{p.id}/")
    assert r.status_code == 200
    body = r.json()
    assert body["category_detail"]["name"] == "Books"
    labels = [s["label"] for s in body["specs"]]
    assert "Тип" in labels and "Автор" in labels and "ISBN" in labels
    assert "related" in body


def test_product_detail_related_same_category_only(api, books, toys):
    p1 = Product.objects.create(category=books, name="B1", slug="b1", price="10.00", stock=1)
    p2 = Product.objects.create(category=books, name="B2", slug="b2", price="10.00", stock=1)
    p3 = Product.objects.create(category=toys, name="T1", slug="t1", price="10.00", stock=1)
    r = api.get(f"/api/products/{p1.id}/")
    related_ids = [x["id"] for x in r.json()["related"]]
    assert p2.id in related_ids
    assert p3.id not in related_ids
    assert p1.id not in related_ids


def test_product_detail_has_format_age_and_gallery(api, books):
    from catalog.models import ProductImage
    p = Product.objects.create(
        category=books, name="Book", slug="bk", price="10.00", stock=1,
        media_format="AUDIO", age_rating="12+",
    )
    ProductImage.objects.create(product=p, image="products/x.jpg", alt="back", position=1)
    r = api.get(f"/api/products/{p.id}/")
    body = r.json()
    assert len(body["images"]) == 1
    labels = {s["label"]: s["value"] for s in body["specs"]}
    assert labels.get("Формат") == "Аудиокнига"
    assert labels.get("Возраст") == "12+"
