from django.db import transaction
from django.utils import timezone

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


# =====================================================
# MAIN SERVICE — CREATE / GENERATE ID (CLOUDINARY + FAILOVER SAFE)
# =====================================================
def generate_id_card(application: IDApplication):

    print("ID SERVICE: START")

    # ---------------------------
    # HARD VALIDATION
    # ---------------------------
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

    try:
        with transaction.atomic():

            # Lock row to prevent race
            id_card, _ = (
                IDCard.objects.select_for_update()
                .get_or_create(student=student)
            )

            print("ID SERVICE: IDCARD OK", id_card.id)

            # -------------------------------------------------
            # IDEMPOTENT — Already generated?
            # -------------------------------------------------
            if id_card.image and getattr(id_card.image, "public_id", None):
                print("ID SERVICE: IMAGE EXISTS (CLOUDINARY)")
                return id_card

            # -------------------------------------------------
            # GENERATE IMAGE
            # -------------------------------------------------
            print("ID SERVICE: GENERATING IMAGE")
            result = build_id_card(id_card)

            id_card.refresh_from_db()

            # ---------------------------
            # CLOUDINARY SUCCESS
            # ---------------------------
            if id_card.image and getattr(id_card.image, "public_id", None):
                print("ID SERVICE: GENERATED (CLOUDINARY)", id_card.image.url)
                return id_card

            # ---------------------------
            # FAILOVER SUCCESS (MEMORY IMAGE)
            # ---------------------------
            if isinstance(result, (bytes, bytearray)):
                print("ID SERVICE: GENERATED (FAILOVER MODE)")
                return id_card

            print("ID SERVICE: FAILED - GENERATOR RETURNED NONE")
            return None

    except Exception as e:
        print("ID SERVICE ERROR:", str(e))
        return None


# =====================================================
# SELF-HEAL ENGINE — REBUILD IF BROKEN
# =====================================================
def ensure_id_card_exists(id_card):

    if not id_card:
        return None

    # -------------------------------------------------
    # Already valid Cloudinary image?
    # -------------------------------------------------
    if id_card.image and getattr(id_card.image, "public_id", None):
        return id_card.image.url

    # -------------------------------------------------
    # Find approved application
    # -------------------------------------------------
    application = (
        IDApplication.objects
        .filter(student=id_card.student, status=IDApplication.STATUS_APPROVED)
        .first()
    )

    if not application:
        print("ID HEAL: NO APPROVED APPLICATION")
        return None

    if not application.passport:
        print("ID HEAL: APPROVED APPLICATION HAS NO PASSPORT")
        return None

    try:
        with transaction.atomic():

            print("ID HEAL: REBUILD START")

            id_card = (
                IDCard.objects.select_for_update()
                .get(pk=id_card.pk)
            )

            result = build_id_card(id_card)

            id_card.refresh_from_db()

            # ---------------------------
            # CLOUDINARY SUCCESS
            # ---------------------------
            if id_card.image and getattr(id_card.image, "public_id", None):
                print("ID HEAL: SUCCESS (CLOUDINARY)")
                return id_card.image.url

            # ---------------------------
            # FAILOVER SUCCESS
            # ---------------------------
            if isinstance(result, (bytes, bytearray)):
                print("ID HEAL: SUCCESS (FAILOVER MODE)")
                return None  # memory image shown via view, not URL

            print("ID HEAL: FAILED - GENERATOR RETURNED NONE")
            return None

    except Exception as e:
        print("ID HEAL ERROR:", str(e))
        return None
