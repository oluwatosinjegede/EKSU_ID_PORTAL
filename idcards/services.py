from django.db import transaction
from django.core.files.base import ContentFile

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


# =====================================================
# MAIN SERVICE — CREATE / GENERATE ID SAFELY
# =====================================================
def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create/reuse IDCard and generate image.
    Fully idempotent, Cloudinary-safe, race-condition safe.
    """
    print("ID SERVICE: START")

    if application.status != IDApplication.STATUS_APPROVED:
        print("ID SERVICE: NOT APPROVED")
        return None

    if not application.passport:
        print("ID SERVICE: NO PASSPORT")
        return None

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    if application.status != IDApplication.STATUS_APPROVED:
        raise ValueError("Application not approved")

    if not application.passport:
        raise ValueError("Passport missing")

    student = application.student

    with transaction.atomic():

        # -------------------------------------------------
        # Get or create IDCard
        # -------------------------------------------------
        id_card, _ = IDCard.objects.get_or_create(student=student)

        print("ID SERVICE: IDCARD OK", id_card.id)

        # -------------------------------------------------
        # Ensure passport exists on IDCard (sync if missing)
        # -------------------------------------------------
        if not id_card.passport and application.passport:
            try:
                src = application.passport.file
                src.seek(0)

                filename = f"{student.matric_number or id_card.uid}_passport.jpg"

                id_card.passport.save(
                    filename,
                    ContentFile(src.read()),
                    save=False,
                )
                id_card.save(update_fields=["passport"])

            except Exception:
                pass  # never crash service

        # -------------------------------------------------
        # If image already exists ? idempotent return
        # -------------------------------------------------
        if id_card.image and getattr(id_card.image, "name", None):
            return id_card

        # -------------------------------------------------
        # HARD CHECK — passport must exist before generation
        # -------------------------------------------------
        if not id_card.passport:
            raise RuntimeError("IDCard passport missing after sync")

        # -------------------------------------------------
        # Generate ID image
        # -------------------------------------------------
        print("ID SERVICE: GENERATING IMAGE...")

        build_id_card(id_card)

        if id_card.image:
            print("ID SERVICE: SUCCESS", id_card.image.url)
        else:
            print("ID SERVICE: FAILED — NO IMAGE")

        id_card.refresh_from_db()
        return id_card


# =====================================================
# SAFE ENSURE (REBUILD IF MISSING)
# =====================================================

def ensure_id_card_exists(id_card):
    """
    FULL SELF-HEAL ENGINE

    Repairs automatically:
    - Missing passport on IDCard
    - Missing image
    - Broken cards
    """

    if not id_card:
        return None

    # Already generated
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
        print("ID HEAL: Approved app has no passport")
        return None

    try:
        with transaction.atomic():

            # -------------------------------------------------
            # SELF-HEAL PASSPORT (Application ? IDCard)
            # -------------------------------------------------
            if not id_card.passport:
                try:
                    src = application.passport.file
                    src.seek(0)

                    filename = f"{id_card.student.matric_number or id_card.uid}_passport.jpg"

                    id_card.passport.save(
                        filename,
                        ContentFile(src.read()),
                        save=False,
                    )
                    id_card.save(update_fields=["passport"])
                    print("ID HEAL: Passport copied")

                except Exception as e:
                    print("ID HEAL: Passport copy failed:", str(e))

            # -------------------------------------------------
            # GENERATE IMAGE
            # -------------------------------------------------
            build_id_card(id_card)
            id_card.refresh_from_db()

            if id_card.image and getattr(id_card.image, "name", None):
                print("ID HEAL: ID generated OK")
                return id_card.image.url

            print("ID HEAL: Generation failed")
            return None

    except Exception as e:
        print("ID HEAL ERROR:", str(e))
        return None
