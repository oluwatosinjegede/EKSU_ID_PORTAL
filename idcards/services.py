from django.db import transaction

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


# =====================================================
# MAIN SERVICE — CREATE / GENERATE ID (CLOUDINARY SAFE)
# =====================================================
def generate_id_card(application: IDApplication):
    """
    Create/reuse IDCard and generate image.
    Cloudinary-safe, idempotent, race-safe.
    """

    print("ID SERVICE: START")

    if not application or not application.student:
        print("ID SERVICE: INVALID APPLICATION")
        return None

    if application.status != IDApplication.STATUS_APPROVED:
        print("ID SERVICE: NOT APPROVED")
        return None

    if not application.passport:
        print("ID SERVICE: NO PASSPORT")
        return None

    student = application.student

    with transaction.atomic():

        # -------------------------------------------------
        # Get or create IDCard
        # -------------------------------------------------
        id_card, _ = IDCard.objects.get_or_create(student=student)
        print("ID SERVICE: IDCARD OK", id_card.id)

        # -------------------------------------------------
        # If image already exists ? return (IDEMPOTENT)
        # -------------------------------------------------
        if id_card.image and getattr(id_card.image, "name", None):
            print("ID SERVICE: IMAGE ALREADY EXISTS")
            return id_card

        # -------------------------------------------------
        # Generate image (passport read from Application via URL)
        # -------------------------------------------------
        print("ID SERVICE: GENERATING IMAGE...")
        build_id_card(id_card)

        id_card.refresh_from_db()

        if id_card.image and getattr(id_card.image, "name", None):
            print("ID SERVICE: SUCCESS", id_card.image.url)
            return id_card

        print("ID SERVICE: FAILED — NO IMAGE")
        return None


# =====================================================
# SELF-HEAL ENGINE — REBUILD IF BROKEN
# =====================================================
def ensure_id_card_exists(id_card):
    """
    Fully self-healing ID repair.

    Repairs:
    - Missing image
    - Broken cards
    - Late approval
    """

    if not id_card:
        return None

    # Already exists
    if id_card.image and getattr(id_card.image, "name", None):
        return id_card.image.url

    # Find approved application
    application = (
        IDApplication.objects
        .filter(student=id_card.student, status=IDApplication.STATUS_APPROVED)
        .first()
    )

    if not application:
        print("ID HEAL: No approved application")
        return None

    if not application.passport:
        print("ID HEAL: Approved application has no passport")
        return None

    try:
        with transaction.atomic():

            print("ID HEAL: REBUILDING IMAGE...")
            build_id_card(id_card)
            id_card.refresh_from_db()

            if id_card.image and getattr(id_card.image, "name", None):
                print("ID HEAL: SUCCESS")
                return id_card.image.url

            print("ID HEAL: FAILED — NO IMAGE")
            return None

    except Exception as e:
        print("ID HEAL ERROR:", str(e))
        return None
