from django.core.management.base import BaseCommand
from idcards.models import IDCard
from idcards.services import ensure_id_card_exists


class Command(BaseCommand):
    help = "Self-heal and rebuild all missing ID cards"

    def handle(self, *args, **kwargs):
        rebuilt = 0
        skipped = 0

        for card in IDCard.objects.all():
            url = ensure_id_card_exists(card)
            if url:
                rebuilt += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Rebuilt={rebuilt}, Skipped={skipped}"
        ))
