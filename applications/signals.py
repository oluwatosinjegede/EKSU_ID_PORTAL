from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from applications.models import IDApplication
from idcards.models import IDCard
from idcards.generator import generate_id_card


@receiver(post_save, sender=IDApplication)
def generate_id_after_approval(sender, instance, created, **kwargs):
    """
    Trigger ID generation when application becomes APPROVED.
    Reliable and primary trigger.
    """

    if instance.status != IDApplication.STATUS_APPROVED:
        return

    # Must have passport
    if not instance.passport:
        return

    try:
        card, _ = IDCard.objects.get_or_create(student=instance.student)

        # Skip if already generated
        if card.image:
            return

        transaction.on_commit(lambda: generate_id_card(card))

    except Exception:
        pass
