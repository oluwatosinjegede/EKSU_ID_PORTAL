from django.db import transaction
from idcards.models import IDCard
from idcards.generator import generate_id_card
from applications.models import IDApplication


def generate_id_card(application: IDApplication) -> IDCard:
    student = application.student

    with transaction.atomic():
        id_card, _ = IDCard.objects.get_or_create(
            student=student,
            defaults={"is_active": True},
        )

        # If an image already exists on Cloudinary, reuse it
        if id_card.image:
            return id_card

        # generate_id_card_image should return a dict like {"public_id": "...", ...}
        result = generate_id_card_image(id_card)

        public_id = result.get("public_id")
        if not public_id:
            # Optionally raise or handle error if Cloudinary didn't return a public_id
            raise ValueError("generate_id_card_image did not return a public_id")

        # For CloudinaryField, assigning the public_id is enough
        id_card.image = public_id
        id_card.save(update_fields=["image"])

        return id_card
