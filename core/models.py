from datetime import date
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.urls import reverse
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        extra_fields.setdefault("full_name", "Administrator")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        TEMPLE_OWNER = "TEMPLE_OWNER", "Temple Owner"
        COLLECTOR = "COLLECTOR", "SONPK Collector"
        ADMIN = "ADMIN", "Admin Department"

    # Alias for backward compatibility
    Role.TEMPLE_MANAGER = Role.TEMPLE_OWNER

    username = models.CharField(max_length=150, unique=False, blank=True)
    full_name = models.CharField(max_length=160)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25, blank=True)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.TEMPLE_OWNER)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    def __str__(self):
        role_label = self.get_role_display()
        name = self.full_name or self.email
        return f"{name} ({role_label})"

    @property
    def is_temple_owner(self):
        return self.role == self.Role.TEMPLE_OWNER

    @property
    def is_collector(self):
        return self.role == self.Role.COLLECTOR

    @property
    def is_admin_dept(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class Temple(models.Model):
    name = models.CharField(max_length=180)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=30)
    contact_person = models.CharField(max_length=120, blank=True)
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="owned_temples",
        blank=True,
        null=True,
        limit_choices_to={"role": CustomUser.Role.TEMPLE_OWNER},
    )
    # Legacy field preserved for smooth migration
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="managed_temples",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        owner_name = f" - {self.owner.full_name}" if self.owner else ""
        return f"{self.name}{owner_name}"

    def get_absolute_url(self):
        return reverse("temple_detail", kwargs={"pk": self.pk})

    @property
    def primary_owner(self):
        return self.owner or self.manager


class FlowerSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        PENDING = "PENDING", "Pending Collection"
        COLLECTED = "COLLECTED", "Collected"

    temple = models.ForeignKey(
        Temple,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    submitted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flower_submissions"
    )
    flower_type = models.CharField(
        max_length=120,
        help_text="Type of flowers (e.g. Marigold, Rose, Jasmine, Mixed)"
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Weight in kilograms (must be > 0)"
    )
    submission_date = models.DateField(default=date.today)
    remarks = models.TextField(blank=True, help_text="Optional remarks from temple owner")
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submission_date", "-created_at"]
        verbose_name = "Flower Submission"
        verbose_name_plural = "Flower Submissions"

    def __str__(self):
        return f"{self.temple.name} - {self.flower_type} ({self.weight} kg) [{self.get_status_display()}]"

    @property
    def is_collected(self):
        return self.status == self.Status.COLLECTED


class CollectionRecord(models.Model):
    class Status(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"

    submission = models.OneToOneField(
        FlowerSubmission,
        on_delete=models.CASCADE,
        related_name="collection_record"
    )
    collector = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="collections_recorded",
        limit_choices_to={"role": CustomUser.Role.COLLECTOR}
    )
    collected_at = models.DateTimeField(default=timezone.now)
    collected_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Collected weight in kilograms"
    )
    remarks = models.TextField(blank=True, help_text="Collection notes/observations")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.COLLECTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-collected_at", "-created_at"]
        verbose_name = "Collection Record"
        verbose_name_plural = "Collection Records"

    def __str__(self):
        return f"Collection #{self.pk} - {self.submission.temple.name} by {self.collector.full_name or self.collector.email}"


# Optional catalog model for predefined flower types and educational properties
class Flower(models.Model):
    class Quality(models.TextChoices):
        EXCELLENT = "EXCELLENT", "Excellent Quality"
        GOOD = "GOOD", "Good Quality"
        MEDIUM = "MEDIUM", "Medium Quality"

    name = models.CharField(max_length=120)
    nitrogen_content = models.CharField(max_length=80, blank=True)
    freshness_duration = models.CharField(max_length=80, blank=True)
    quality = models.CharField(max_length=20, choices=Quality.choices, default=Quality.GOOD)
    decomposition_rate = models.CharField(max_length=80, blank=True)
    fertilizer_potential = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    scientific_information = models.TextField(blank=True)
    fertilizer_usage = models.TextField(blank=True)
    image = models.ImageField(upload_to="flowers/", blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# Legacy Collection model preserved to avoid migration table drops
class Collection(models.Model):
    temple = models.ForeignKey(Temple, on_delete=models.CASCADE, related_name="legacy_collections")
    flower = models.ForeignKey(Flower, on_delete=models.PROTECT, related_name="legacy_collections", null=True, blank=True)
    collector = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="legacy_collections")
    quantity = models.DecimalField(max_digits=9, decimal_places=2, help_text="Quantity in kg")
    collection_date = models.DateField()
    status = models.CharField(max_length=20, default="PENDING")
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-collection_date", "-created_at"]

    def __str__(self):
        return f"{self.temple} - {self.quantity} kg"
