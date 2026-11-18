
from django.core.management.base import BaseCommand
from core.models import CustomUser


class Command(BaseCommand):
    help = "Create demo accounts without modifying existing users."

    DEMO_USERS = [
        {
            "email": "admin@pushparecycle.local",
            "password": "Admin@12345",
            "full_name": "Devi Sharma (Admin Head)",
            "phone": "+91 9000000001",
            "role": CustomUser.Role.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "email": "temple@pushparecycle.local",
            "password": "Temple@12345",
            "full_name": "Pandit Ramesh Shastri",
            "phone": "+91 9876500001",
            "role": CustomUser.Role.TEMPLE_OWNER,
        },
        {
            "email": "owner2@pushparecycle.local",
            "password": "Temple@12345",
            "full_name": "Swami Anantanand",
            "phone": "+91 9876500002",
            "role": CustomUser.Role.TEMPLE_OWNER,
        },
        {
            "email": "collector@pushparecycle.local",
            "password": "Collector@12345",
            "full_name": "Aarav Kumar (SONPK Field Collector)",
            "phone": "+91 9111100001",
            "role": CustomUser.Role.COLLECTOR,
        },
        {
            "email": "collector2@pushparecycle.local",
            "password": "Collector@12345",
            "full_name": "Pooja Verma (SONPK Logistics)",
            "phone": "+91 9111100002",
            "role": CustomUser.Role.COLLECTOR,
        },
    ]

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for data in self.DEMO_USERS:
            email = data["email"]

            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"Already exists; left unchanged: {email}")
                )
                existing_count += 1
                continue

            user_data = data.copy()
            password = user_data.pop("password")

            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                **user_data,
            )

            self.stdout.write(self.style.SUCCESS(f"Created: {user.email}"))
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Created: {created_count}, Already existed: {existing_count}"
            )
        )
