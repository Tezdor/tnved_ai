from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import RateLimitBucket


class Command(BaseCommand):
    help = "Удаляет счётчики rate limit старше суток."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать количество записей без удаления."
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=1)

        if options["dry_run"]:
            count = RateLimitBucket.objects.filter(
                window_started_at__lt=cutoff
            ).count()

            self.stdout.write(
                f"Устаревших счётчиков: {count}. Ничего не удалено."
            )
            return

        total = 0

        while True:
            with transaction.atomic():
                ids = list(
                    RateLimitBucket.objects
                    .select_for_update(skip_locked=True)
                    .filter(window_started_at__lt=cutoff)
                    .order_by("pk")
                    .values_list("pk", flat=True)[:500]
                )

                if not ids:
                    break

                deleted, _ = RateLimitBucket.objects.filter(
                    pk__in=ids
                ).delete()

                total += deleted

        self.stdout.write(
            self.style.SUCCESS(f"Удалено счётчиков: {total}")
        )