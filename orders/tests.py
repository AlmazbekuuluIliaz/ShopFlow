from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem

User = get_user_model()


class CheckoutAtomicityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="pass12345")
        self.client.force_authenticate(self.user)
        self.cart = Cart.objects.create(user=self.user)
        self.category = Category.objects.create(name="Phones", slug="phones")
        self.url = reverse("order-list")

    def make_product(self, name, slug, price, stock):
        return Product.objects.create(
            category=self.category,
            name=name,
            slug=slug,
            price=Decimal(price),
            stock=stock,
        )

    def test_successful_checkout_reduces_stock_and_clears_cart(self):
        product = self.make_product("iPhone", "iphone", "999.00", 5)
        CartItem.objects.create(cart=self.cart, product=product, quantity=2)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product.refresh_from_db()
        self.assertEqual(product.stock, 3)
        self.assertEqual(self.cart.items.count(), 0)
        self.assertEqual(Order.objects.count(), 1)
        item = OrderItem.objects.get()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal("999.00"))

    def test_price_is_frozen_even_if_product_price_changes_later(self):
        product = self.make_product("iPhone", "iphone", "999.00", 5)
        CartItem.objects.create(cart=self.cart, product=product, quantity=1)

        self.client.post(self.url)
        product.price = Decimal("1499.00")
        product.save(update_fields=["price"])

        self.assertEqual(OrderItem.objects.get().price, Decimal("999.00"))

    def test_oversell_is_rejected_and_rolls_back(self):
        product = self.make_product("iPhone", "iphone", "999.00", 1)
        CartItem.objects.create(cart=self.cart, product=product, quantity=3)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(self.cart.items.count(), 1)

    def test_partial_failure_rolls_back_the_whole_order(self):
        good = self.make_product("Case", "case", "19.00", 10)
        bad = self.make_product("Charger", "charger", "29.00", 1)
        CartItem.objects.create(cart=self.cart, product=good, quantity=2)
        CartItem.objects.create(cart=self.cart, product=bad, quantity=5)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        good.refresh_from_db()
        bad.refresh_from_db()
        self.assertEqual(good.stock, 10)
        self.assertEqual(bad.stock, 1)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(self.cart.items.count(), 2)

    def test_empty_cart_is_rejected(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
