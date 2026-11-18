"""Product catalogue — database-design.md §5.3.

Fixed V1 catalogue (eggs, milk, honey, vegetables), seeded by a data
migration. Products are deactivated, never deleted, because listings
reference them (SDD §4).
"""

from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=60, unique=True)
    category = models.CharField(max_length=60)  # equals name in V1
    unit = models.CharField(max_length=20)  # tray / litre / kg / bunch …
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
