"""Seed demo/test data around Kisii University (dev tool, idempotent).

Creates curated Places (Kisii University, Kisii Town) and a handful of
farms within a few kilometres of campus, each with today's listings.
Re-running wipes the previous demo set first (phone numbers 07xx…0000xx).
"""

from decimal import Decimal

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accounts.models import User
from discovery.models import ContactEvent, Place
from farms.models import Farm
from listings.services import publish_for_today
from products.models import Product

DEMO_PHONE_PREFIX = '+254700001'

PLACES = [
    {'name': 'Kisii University', 'slug': 'kisii-university',
     'location': Point(34.1563, -0.6771, srid=4326), 'display_order': 0},
    {'name': 'Kisii Town', 'slug': 'kisii-town',
     'location': Point(34.1594, -0.6810, srid=4326), 'display_order': 1},
    {'name': 'Nyanchwa', 'slug': 'nyanchwa',
     'location': Point(34.1520, -0.6700, srid=4326), 'display_order': 2},
]

# (name, lng, lat, phone-suffix, pickup hours, products {slug: (price, note)})
FARMS = [
    ('Nyanchwa Fresh Farm', 34.1545, -0.6781, '01', 'Mon-Sat, 7am-6pm', {
        'eggs': (Decimal('400'), '10 trays'),
        'vegetables': (Decimal('50'), 'kale, tomatoes, onions'),
        'milk': (None, ''),
    }),
    ('Getembe Honey Farm', 34.1490, -0.6695, '02', 'Daily, 8am-5pm', {
        'honey': (Decimal('700'), 'raw combs and squeezed jars'),
        'eggs': (Decimal('450'), ''),
    }),
    ('Mosocho Dairy', 34.1780, -0.6550, '03', 'Mon-Sat, 6am-8am & 4pm-7pm', {
        'milk': (Decimal('60'), 'fresh cow milk, morning and evening'),
    }),
    ('Sunripe Shamba', 34.1480, -0.6950, '04', 'Daily, 7am-7pm', {
        'vegetables': (Decimal('40'), 'bananas, avocado, sukuma wiki'),
        'eggs': (Decimal('380'), '5 trays left'),
    }),
    ('Highland Apiary', 34.1900, -0.6420, '05', 'Tue-Sun, 9am-5pm', {
        'honey': (Decimal('650'), '1kg jars'),
        'vegetables': (Decimal('55'), 'seasonal greens'),
    }),
    ('Campside Eggs & Milk', 34.1630, -0.6840, '06', 'Mon-Sat, 6am-6pm', {
        'eggs': (Decimal('420'), ''),
        'milk': (None, 'by the litre, bring a container'),
        'honey': (Decimal('750'), 'few jars this week'),
    }),
]


class Command(BaseCommand):
    help = 'Seed demo farms and places around Kisii University for testing.'

    def handle(self, *args, **options):
        # Wipe previous demo data (PROTECT chains: events -> farms -> users)
        old_farm_ids = Farm.objects.filter(owner__phone_number__startswith=DEMO_PHONE_PREFIX).values_list('id', flat=True)
        deleted_events = ContactEvent.objects.filter(farm_id__in=list(old_farm_ids)).delete()
        Place.objects.filter(slug__in=['demo-town']).delete()
        deleted_farms = Farm.objects.filter(owner__phone_number__startswith=DEMO_PHONE_PREFIX).delete()
        deleted_users = User.objects.filter(phone_number__startswith=DEMO_PHONE_PREFIX).delete()

        for entry in PLACES:
            place, _ = Place.objects.update_or_create(
                slug=entry['slug'],
                defaults={
                    'name': entry['name'], 'location': entry['location'],
                    'display_order': entry['display_order'],
                },
            )
        self.stdout.write(f'places: {Place.objects.count()} active')

        products = {p.slug: p for p in Product.objects.filter(is_active=True)}
        for name, lng, lat, suffix, hours, product_list in FARMS:
            user, _ = User.objects.get_or_create(
                phone_number=f'{DEMO_PHONE_PREFIX}{suffix}',
                defaults={'name': name, 'role': User.Role.FARMER},
            )
            user.set_password('demo-farm-1')
            user.save()
            farm = Farm(
                owner=user, name=name,
                location=Point(lng, lat, srid=4326),
                pickup_hours=hours, contact_phone=user.phone_number,
                is_active=True,  # demo farms are past onboarding
            )
            farm.save()
            details = {}
            for slug, (price, note) in product_list.items():
                if slug in products:
                    farm.products.add(products[slug])
                    details[slug] = {'price_kes': price, 'quantity_note': note}
            publish_for_today(farm, details)
            self.stdout.write(f'farm: {name} — {", ".join(details)} ')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(FARMS)} demo farms around Kisii University '
            f'(wiped {deleted_farms[1]} old farms, {deleted_users[1]} old users, '
            f'{deleted_events[1]} contact events).'
        ))
