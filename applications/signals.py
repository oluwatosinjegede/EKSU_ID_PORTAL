from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IDApplication
from idcards.services import generate_id_card


@receiver(post_save, sender=IDApplication)
def issue_id_card_on_approval(sender, instance, created, **kwargs):
    # Never on application creation
    if created:
        return

    # Only when approved
    if instance.status != IDApplication.STATUS_APPROVED:
        return

    generate_id_card(instance)
