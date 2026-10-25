from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Type(models.TextChoices):
        BOOK = "BOOK", "Книга"
        MAGAZINE = "MAGAZINE", "Журнал"
        NEWSPAPER = "NEWSPAPER", "Газета"

    class CoverType(models.TextChoices):
        HARD = "HARD", "Твёрдый"
        SOFT = "SOFT", "Мягкий"

    class Format(models.TextChoices):
        PRINT = "PRINT", "Бумажная"
        EBOOK = "EBOOK", "Электронная"
        AUDIO = "AUDIO", "Аудиокнига"

    class AgeRating(models.TextChoices):
        A0 = "0+", "0+"
        A6 = "6+", "6+"
        A12 = "12+", "12+"
        A16 = "16+", "16+"
        A18 = "18+", "18+"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    product_type = models.CharField(
        max_length=20,
        choices=Type.choices,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True)

    author = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=50, blank=True)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    cover_type = models.CharField(max_length=10, choices=CoverType.choices, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    issn = models.CharField(max_length=20, blank=True)
    issue_number = models.CharField(max_length=50, blank=True)
    issue_date = models.DateField(null=True, blank=True)

    media_format = models.CharField(max_length=10, choices=Format.choices, default=Format.PRINT)
    age_rating = models.CharField(max_length=3, choices=AgeRating.choices, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["available"]),
            models.Index(fields=["product_type"]),
        ]

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.available and self.stock > 0

    @property
    def specs(self):
        rows = [("Тип", self.get_product_type_display())]
        candidates = [
            ("Автор", self.author),
            ("Издательство", self.publisher),
            ("Язык", self.language),
            ("Формат", self.get_media_format_display()),
            ("Возраст", self.age_rating),
            ("Год издания", self.publication_year),
            ("Страниц", self.pages),
            ("Переплёт", self.get_cover_type_display() if self.cover_type else ""),
            ("ISBN", self.isbn),
            ("ISSN", self.issn),
            ("Номер выпуска", self.issue_number),
            ("Дата выпуска", self.issue_date),
        ]
        for label, value in candidates:
            if value:
                rows.append((label, value))
        return [{"label": label, "value": str(value)} for label, value in rows]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Image #{self.pk} for {self.product}"
