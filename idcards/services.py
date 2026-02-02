from idcards.models import IDCard


def generate_id_card(application):
    id_card, created = IDCard.objects.get_or_create(
        student=application.student,
        defaults={
            "application": application,
            "status": "active",
        }
    )
    return id_card
