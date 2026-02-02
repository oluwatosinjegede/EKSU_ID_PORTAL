from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IDApplication
from idcards.services import generate_id_card


@receiver(post_save, sender=IDApplication)
def auto_issue_id_card(sender, instance, created, **kwargs):
    # Only run on creation
    if not created:
        return

    # Only issue AFTER approval
    if instance.status != IDApplication.STATUS_APPROVED:
        return

    generate_id_card(instance)
