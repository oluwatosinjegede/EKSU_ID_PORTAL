from django.db.models.signals import post_save
from django.dispatch import receiver
from idcards.models import IDCard
from .models import IDApplication
from idcards.services import generate_id_card


@receiver(post_save, sender=IDApplication)
def auto_issue_id_card(sender, instance, created, **kwargs):
    # Only issue on first creation
    if not created:
        return

    # Safety check: do not issue twice
    if IDCard.objects.filter(student=instance.student).exists():
        return

    generate_id_card(instance)
