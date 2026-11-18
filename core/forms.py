from decimal import Decimal
from datetime import date
from django import forms
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import (
    CollectionRecord,
    CustomUser,
    FlowerSubmission,
    Temple,
)


class RoleLoginForm(forms.Form):
    ROLE_CHOICES = [
        ("", "Select Your Role (or auto-detect)"),
        (CustomUser.Role.TEMPLE_OWNER, "Temple Owner"),
        (CustomUser.Role.COLLECTOR, "SONPK Collector"),
        (CustomUser.Role.ADMIN, "Admin Department"),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Choose your role or let the system detect it from your credentials."
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "name@example.com", "autocomplete": "email"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••", "autocomplete": "current-password"})
    )

    def __init__(self, *args, expected_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_role = expected_role
        if expected_role:
            self.fields["role"].initial = expected_role
            self.fields["role"].widget = forms.HiddenInput()
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        selected_role = cleaned_data.get("role") or self.expected_role

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email address or password. Please verify your credentials.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated. Please contact the administrator.")

            # If user explicitly logged in through a role portal (or selected role)
            if selected_role and user.role != selected_role and not (selected_role == CustomUser.Role.ADMIN and user.is_superuser):
                role_labels = dict(CustomUser.Role.choices)
                expected_label = role_labels.get(selected_role, selected_role)
                actual_label = role_labels.get(user.role, user.role)
                raise forms.ValidationError(
                    f"Access Denied: Your account is registered as '{actual_label}', not '{expected_label}'. Please log in through your appropriate role portal."
                )

            self.user = user

        return cleaned_data


class FlowerSubmissionForm(forms.ModelForm):
    COMMON_FLOWER_CHOICES = [
        ("Marigold", "Marigold (Genda)"),
        ("Rose", "Rose (Gulab)"),
        ("Jasmine", "Jasmine (Mogra)"),
        ("Hibiscus", "Hibiscus (Gudhal)"),
        ("Lotus", "Lotus (Kamal)"),
        ("Chrysanthemum", "Chrysanthemum (Sevanti)"),
        ("Mixed Flowers", "Mixed Temple Flowers"),
        ("Other", "Other (specify in remarks)"),
    ]

    flower_type = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. Marigold, Rose, Jasmine, or Mixed",
            "list": "flower-type-suggestions"
        }),
        help_text="Select a common flower or type a custom variety."
    )

    class Meta:
        model = FlowerSubmission
        fields = ["temple", "flower_type", "weight", "submission_date", "remarks"]
        widgets = {
            "temple": forms.Select(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 50.00", "step": "0.1", "min": "0.1"}),
            "submission_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes regarding purity, moisture, or collection time..."}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("submission_date"):
            self.initial["submission_date"] = date.today()
        if user and user.role == CustomUser.Role.TEMPLE_OWNER:
            user_temples = Temple.objects.filter(owner=user)
            self.fields["temple"].queryset = user_temples
            if user_temples.count() == 1:
                self.initial["temple"] = user_temples.first()
                self.fields["temple"].widget = forms.HiddenInput()

    def clean_weight(self):
        weight = self.cleaned_data.get("weight")
        if weight is None or weight <= Decimal("0"):
            raise forms.ValidationError("Flower weight must be a positive numeric value strictly greater than 0 kg.")
        return weight


class TempleProfileForm(forms.ModelForm):
    class Meta:
        model = Temple
        fields = ["name", "address", "city", "state", "contact_person", "contact_number"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Temple Name"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Full street address"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "State"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primary Contact Person / Priest"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone / Mobile Number"}),
        }


class CollectionRecordForm(forms.ModelForm):
    collected_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        initial=timezone.now
    )

    class Meta:
        model = CollectionRecord
        fields = ["collected_at", "collected_weight", "remarks"]
        widgets = {
            "collected_weight": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "min": "0.1"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Quality notes, bag count, vehicle used, etc."}),
        }

    def clean_collected_weight(self):
        weight = self.cleaned_data.get("collected_weight")
        if weight is None or weight <= Decimal("0"):
            raise forms.ValidationError("Collected weight must be strictly greater than 0 kg.")
        return weight


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Leave blank to keep existing password"}),
        required=False,
        help_text="Required when creating a new account. Minimum 8 characters."
    )
    # Optional fields for auto-creating a temple if user is a Temple Owner
    create_temple_name = forms.CharField(
        max_length=180,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Shri Krishna Mandir"}),
        help_text="Optional: If creating a Temple Owner, provide a temple name to automatically create and link their temple."
    )
    create_temple_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Temple street address, city, state"}),
    )

    class Meta:
        model = CustomUser
        fields = ["role", "full_name", "email", "phone", "is_active"]
        widgets = {
            "role": forms.Select(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "user@example.com"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 9876543210"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.is_create = kwargs.pop("is_create", False)
        super().__init__(*args, **kwargs)
        if self.is_create:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Minimum 8 characters."

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        if self.is_create and (not pwd or len(pwd) < 8):
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return pwd

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = CustomUser.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email


class AdminTempleForm(forms.ModelForm):
    class Meta:
        model = Temple
        fields = ["name", "city", "state", "address", "contact_person", "contact_number", "owner"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control"}),
            "owner": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = CustomUser.objects.filter(role=CustomUser.Role.TEMPLE_OWNER)
        self.fields["owner"].required = False
