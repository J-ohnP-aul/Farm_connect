"""Weekly pilot metrics — SDD §5.5 (pilot_report command).

The pilot's go/no-go gate (proposal §Rollout, phase 4) needs numbers, not
UI: weekly farmer listing activity (Q4) and buyer contact counts (Q5).
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from discovery.models import ContactEvent
from farms.models import Farm
from listings.models import Listing


class Command(BaseCommand):
    help = 'Print the weekly pilot metrics: farmer listing activity and buyer contacts.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Window length (default: 7 days).')

    def handle(self, *args, **options):
        days = options['days']
        since = timezone.now() - timedelta(days=days)

        self.stdout.write(self.style.MIGRATE_HEADING(f'Local Farm Map pilot report — last {days} days'))
        self.stdout.write('')

        onboarded = Farm.objects.count()
        active_farms = Farm.objects.filter(is_active=True).count()
        self.stdout.write(f'Farms onboarded: {onboarded} (visible: {active_farms})')
        self.stdout.write('')

        # Q4 — weekly farmer listing activity (database-design.md §7)
        self.stdout.write(self.style.MIGRATE_HEADING('Farmer listing activity'))
        rows = (
            Listing.objects.filter(created_at__gte=since)
            .values('farm__name')
            .annotate(active_days=Count('listing_date', distinct=True))
            .order_by('-active_days')
        )
        for row in rows:
            self.stdout.write(f'  {row["farm__name"]}: {row["active_days"]} listing day(s)')
        if not rows:
            self.stdout.write('  (no listings in window)')
        self.stdout.write('')

        # Q5 — buyer contact actions
        self.stdout.write(self.style.MIGRATE_HEADING('Buyer contacts'))
        contacts = (
            ContactEvent.objects.filter(created_at__gte=since)
            .values('channel')
            .annotate(taps=Count('id'))
            .order_by('channel')
        )
        total = 0
        for row in contacts:
            self.stdout.write(f'  {row["channel"]}: {row["taps"]} tap(s)')
            total += row['taps']
        self.stdout.write(f'  total: {total} tap(s)')
