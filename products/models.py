from django.core.validators import MinValueValidator
from django.db import models


class ProductCategory(models.Model):
    title = models.CharField(
        max_length=50,
        null=False,
        blank=False
    )
    url_title = models.SlugField(
        max_length=65,
        unique=True
    )
    parent = models.ForeignKey(
        'ProductCategory',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(
        max_length=50,
        null=False,
        blank=False
    )
    url_title = models.SlugField(
        max_length=65,
        null=False
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title
