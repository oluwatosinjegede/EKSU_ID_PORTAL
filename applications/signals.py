from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IDApplication
from idcards.models import IDCard
from idcards.services import generate_id_card_pdf


@receiver(post_save, sender=IDApplication)
def auto_issue_id_card(sender, instance, created, **kwargs):
    """
    Automatically generate ID card when application is approved
    """

    # Only act on APPROVED applications
    if instance.status != "APPROVED":
        return

    # Prevent duplicate ID cards
    id_card, created_card = IDCard.objects.get_or_create(
        student=instance.student
    )

    # Generate PDF only if not already generated
    if not id_card.pdf:
        generate_id_card_pdf(id_card)
