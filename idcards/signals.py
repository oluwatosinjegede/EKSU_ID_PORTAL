from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IDCard
from .generator import generate_id_card


@receiver(post_save, sender=IDCard)
def create_card_image(sender, instance, created, **kwargs):
    if instance.passport:
        generate_id_card(instance)
