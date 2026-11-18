from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    CollectionRecord,
    CustomUser,
    Flower,
    FlowerSubmission,
    Temple,
)


class Command(BaseCommand):
    help = "Seed PushpaRecycle role-based demo data (Temple Owners, Collectors, Admins, Temples, Submissions, Collections)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding PushpaRecycle demo users and data...")

        # 1. Admin Department User
        admin, _ = CustomUser.objects.get_or_create(
            email="admin@pushparecycle.local",
            defaults={
                "full_name": "Devi Sharma (Admin Head)",
                "phone": "+91 9000000001",
                "role": CustomUser.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.role = CustomUser.Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Admin@12345")
        admin.save()

        # 2. Temple Owner Users
        temple_owner_1, _ = CustomUser.objects.get_or_create(
            email="temple@pushparecycle.local",
            defaults={
                "full_name": "Pandit Ramesh Shastri",
                "phone": "+91 9876500001",
                "role": CustomUser.Role.TEMPLE_OWNER,
            },
        )
        temple_owner_1.role = CustomUser.Role.TEMPLE_OWNER
        temple_owner_1.set_password("Temple@12345")
        temple_owner_1.save()

        temple_owner_2, _ = CustomUser.objects.get_or_create(
            email="owner2@pushparecycle.local",
            defaults={
                "full_name": "Swami Anantanand",
                "phone": "+91 9876500002",
                "role": CustomUser.Role.TEMPLE_OWNER,
            },
        )
        temple_owner_2.role = CustomUser.Role.TEMPLE_OWNER
        temple_owner_2.set_password("Temple@12345")
        temple_owner_2.save()

        # 3. SONPK Collector Users
        collector_1, _ = CustomUser.objects.get_or_create(
            email="collector@pushparecycle.local",
            defaults={
                "full_name": "Aarav Kumar (SONPK Field Collector)",
                "phone": "+91 9111100001",
                "role": CustomUser.Role.COLLECTOR,
            },
        )
        collector_1.role = CustomUser.Role.COLLECTOR
        collector_1.set_password("Collector@12345")
        collector_1.save()

        collector_2, _ = CustomUser.objects.get_or_create(
            email="collector2@pushparecycle.local",
            defaults={
                "full_name": "Pooja Verma (SONPK Logistics)",
                "phone": "+91 9111100002",
                "role": CustomUser.Role.COLLECTOR,
            },
        )
        collector_2.role = CustomUser.Role.COLLECTOR
        collector_2.set_password("Collector@12345")
        collector_2.save()

        # 4. Registered Temples
        temple_data = [
            (
                "Shree Siddhivinayak Mandir",
                "Mumbai",
                "Maharashtra",
                "SK Bole Marg, Prabhadevi, Mumbai - 400028",
                "+91 22 2422 4438",
                "Pandit Ramesh Shastri",
                temple_owner_1,
            ),
            (
                "Kashi Vishwanath Mandir",
                "Varanasi",
                "Uttar Pradesh",
                "Lahori Tola, Varanasi - 221001",
                "+91 542 239 2629",
                "Swami Anantanand",
                temple_owner_2,
            ),
            (
                "Meenakshi Amman Temple",
                "Madurai",
                "Tamil Nadu",
                "Madurai Main, Madurai - 625001",
                "+91 452 234 4360",
                "Sundaram Gurukkal",
                temple_owner_1,
            ),
        ]

        temples = []
        for name, city, state, address, contact, person, owner in temple_data:
            temple, _ = Temple.objects.get_or_create(
                name=name,
                defaults={
                    "city": city,
                    "state": state,
                    "address": address,
                    "contact_number": contact,
                    "contact_person": person,
                    "owner": owner,
                },
            )
            temple.owner = owner
            temple.save()
            temples.append(temple)

        # 5. Flower Reference Types
        flower_types = ["Marigold (Genda)", "Rose (Gulab)", "Jasmine (Mogra)", "Lotus (Kamal)", "Hibiscus (Gudhal)", "Mixed Sacred Flowers"]
        for ft in flower_types:
            Flower.objects.get_or_create(name=ft)

        # 6. Flower Submissions & Collections
        sample_submissions = [
            # (Temple, Flower Type, Weight, Days Ago, Status, Remarks, Collected By, Collected Weight)
            (temples[0], "Marigold (Genda)", Decimal("85.50"), 10, FlowerSubmission.Status.COLLECTED, "Morning aarti offerings, pure fresh lot.", collector_1, Decimal("85.50")),
            (temples[0], "Rose (Gulab)", Decimal("42.00"), 7, FlowerSubmission.Status.COLLECTED, "Red and pink temple roses.", collector_1, Decimal("41.50")),
            (temples[0], "Mixed Sacred Flowers", Decimal("110.00"), 4, FlowerSubmission.Status.COLLECTED, "Special Tuesday puja collection.", collector_2, Decimal("110.00")),
            (temples[0], "Marigold (Genda)", Decimal("65.00"), 1, FlowerSubmission.Status.PENDING, "Packed in 3 jute bags ready at North Gate.", None, None),
            (temples[0], "Jasmine (Mogra)", Decimal("28.00"), 0, FlowerSubmission.Status.SUBMITTED, "Fresh garland offerings from morning darshan.", None, None),

            (temples[1], "Lotus (Kamal)", Decimal("35.00"), 8, FlowerSubmission.Status.COLLECTED, "Blue and pink sacred lotuses.", collector_1, Decimal("35.00")),
            (temples[1], "Marigold (Genda)", Decimal("140.00"), 5, FlowerSubmission.Status.COLLECTED, "Ghat puja offerings, sorted dry.", collector_2, Decimal("138.00")),
            (temples[1], "Mixed Sacred Flowers", Decimal("95.00"), 2, FlowerSubmission.Status.PENDING, "Ready for afternoon transport.", None, None),
            (temples[1], "Rose (Gulab)", Decimal("50.00"), 0, FlowerSubmission.Status.SUBMITTED, "Stored in cool shade at courtyard.", None, None),

            (temples[2], "Jasmine (Mogra)", Decimal("75.00"), 6, FlowerSubmission.Status.COLLECTED, "Fragrant temple garlands, optimal for bio-compost.", collector_2, Decimal("75.00")),
            (temples[2], "Hibiscus (Gudhal)", Decimal("30.00"), 3, FlowerSubmission.Status.PENDING, "Sorted petals, moisture controlled.", None, None),
            (temples[2], "Marigold (Genda)", Decimal("90.00"), 0, FlowerSubmission.Status.SUBMITTED, "Ready for collection near prasad hall.", None, None),
        ]

        for temple, f_type, weight, days_ago, status, remarks, col_user, col_weight in sample_submissions:
            sub_date = date.today() - timedelta(days=days_ago)
            sub, created = FlowerSubmission.objects.get_or_create(
                temple=temple,
                flower_type=f_type,
                submission_date=sub_date,
                defaults={
                    "weight": weight,
                    "status": status,
                    "remarks": remarks,
                    "submitted_by": temple.owner,
                },
            )
            sub.weight = weight
            sub.status = status
            sub.remarks = remarks
            sub.submitted_by = temple.owner
            sub.save()

            if status == FlowerSubmission.Status.COLLECTED and col_user and not hasattr(sub, "collection_record"):
                col_time = timezone.now() - timedelta(days=days_ago, hours=2)
                CollectionRecord.objects.create(
                    submission=sub,
                    collector=col_user,
                    collected_at=col_time,
                    collected_weight=col_weight or weight,
                    remarks=f"Verified weight {col_weight or weight} kg collected in clean condition.",
                    status=CollectionRecord.Status.COLLECTED,
                )

        self.stdout.write(self.style.SUCCESS("✓ Successfully seeded demo users for all 3 roles:"))
        self.stdout.write("  - Temple Owner:   temple@pushparecycle.local   / Temple@12345")
        self.stdout.write("  - SONPK Collector: collector@pushparecycle.local / Collector@12345")
        self.stdout.write("  - Admin Dept:     admin@pushparecycle.local     / Admin@12345")
