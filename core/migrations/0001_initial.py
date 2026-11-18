# Generated for PushpaRecycle.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(blank=True, max_length=150)),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("full_name", models.CharField(max_length=160)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("role", models.CharField(choices=[("ADMIN", "Admin"), ("COLLECTOR", "Collector"), ("TEMPLE_MANAGER", "Temple Manager")], default="COLLECTOR", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"verbose_name": "user", "verbose_name_plural": "users", "abstract": False},
        ),
        migrations.CreateModel(
            name="Flower",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("nitrogen_content", models.CharField(max_length=80)),
                ("freshness_duration", models.CharField(max_length=80)),
                ("quality", models.CharField(choices=[("EXCELLENT", "Excellent Quality"), ("GOOD", "Good Quality"), ("MEDIUM", "Medium Quality")], max_length=20)),
                ("decomposition_rate", models.CharField(max_length=80)),
                ("fertilizer_potential", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("scientific_information", models.TextField(blank=True)),
                ("fertilizer_usage", models.TextField(blank=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="flowers/")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Temple",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180)),
                ("city", models.CharField(max_length=100)),
                ("state", models.CharField(max_length=100)),
                ("address", models.TextField()),
                ("contact_number", models.CharField(max_length=20)),
                ("pickup_time", models.CharField(max_length=80)),
                ("daily_flower_quantity", models.DecimalField(decimal_places=2, help_text="Quantity in kg", max_digits=8)),
                ("image", models.ImageField(blank=True, null=True, upload_to="temples/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_collectors", models.ManyToManyField(blank=True, limit_choices_to={"role": "COLLECTOR"}, related_name="assigned_temples", to=settings.AUTH_USER_MODEL)),
                ("manager", models.ForeignKey(blank=True, limit_choices_to={"role": "TEMPLE_MANAGER"}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="managed_temples", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=2, help_text="Quantity in kg", max_digits=9)),
                ("collection_date", models.DateField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("COLLECTED", "Collected"), ("DELIVERED", "Delivered"), ("PROCESSED", "Processed")], default="PENDING", max_length=20)),
                ("remarks", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("collector", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collections", to=settings.AUTH_USER_MODEL)),
                ("flower", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collections", to="core.flower")),
                ("temple", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collections", to="core.temple")),
            ],
            options={"ordering": ["-collection_date", "-created_at"]},
        ),
    ]
