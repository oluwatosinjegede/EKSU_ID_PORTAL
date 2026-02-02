from django.db import transaction
from idcards.models import IDCard
from idcards.image import generate_id_card_image


def generate_id_card(application):
    student = application.student

    with transaction.atomic():
        id_card, _ = IDCard.objects.get_or_create(
            student=student,
            defaults={"is_active": True},
        )

        if id_card.image:
            return id_card

        result = generate_id_card_image(id_card)

        id_card.image = result["public_id"]
        id_card.save(update_fields=["image"])

    return id_card
