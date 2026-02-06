from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDApplication
from idcards.services import generate_id_card


@receiver(post_save, sender=IDApplication)
def issue_id_card_on_approval(sender, instance, created, update_fields=None, **kwargs):
    """
    Generate ID card ONLY when:
    - Application already existed (not created)
    - Status changed to APPROVED
    - Passport exists
    - Avoid duplicate / recursive generation
    """

    # Do NOT run on creation
    if created:
        return

    # Only act when status was updated (optimization)
    if update_fields and "status" not in update_fields:
        return

    # Only when approved
    if instance.status != IDApplication.STATUS_APPROVED:
        return

    # Passport must exist
    if not instance.passport:
        return

    # Prevent multiple executions in same transaction
    def _generate():
        try:
            generate_id_card(instance)
        except Exception as e:
            print("SIGNAL ID GENERATION ERROR:", e)

    # Run after DB commit (prevents race conditions / partial state)
    transaction.on_commit(_generate)
