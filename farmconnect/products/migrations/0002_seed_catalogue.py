"""Seed the fixed V1 catalogue — FR-11, BR-02 (eggs, milk, honey, vegetables).

Database-design.md §5.3: seeded by a data migration so every environment
(prototype, CI, production) starts with the same catalogue.
"""

from django.db import migrations


SEED = [
    {'name': 'Eggs', 'slug': 'eggs', 'unit': 'tray'},
    {'name': 'Milk', 'slug': 'milk', 'unit': 'litre'},
    {'name': 'Honey', 'slug': 'honey', 'unit': 'kg'},
    {'name': 'Vegetables', 'slug': 'vegetables', 'unit': 'kg'},
]


def seed(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for entry in SEED:
        Product.objects.get_or_create(
            slug=entry['slug'],
            defaults={'name': entry['name'], 'category': entry['name'], 'unit': entry['unit']},
        )


def unseed(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(slug__in=[e['slug'] for e in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
