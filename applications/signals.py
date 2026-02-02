from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IDApplication
from idcards.services import generate_id_card


@receiver(post_save, sender=IDApplication)
def auto_issue_id_card(sender, instance, **kwargs):
    """
    Automatically generate ID card when application is approved
    """

    # Only act on APPROVED applications
    if instance.status != "APPROVED":
        return

    # SINGLE source of truth
    generate_id_card(instance)
