from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum

from .models import (
    Collection,
    CollectionRecord,
    CustomUser,
    Flower,
    FlowerSubmission,
    Temple,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "full_name", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "phone", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone", "role", "password1", "password2"),
        }),
    )


@admin.register(Temple)
class TempleAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "contact_number", "contact_person", "owner", "created_at")
    list_filter = ("city", "state")
    search_fields = ("name", "city", "state", "address", "contact_person", "contact_number")
    autocomplete_fields = ("owner",)


@admin.register(FlowerSubmission)
class FlowerSubmissionAdmin(admin.ModelAdmin):
    list_display = ("temple", "flower_type", "weight", "submission_date", "status", "submitted_by", "created_at")
    list_filter = ("status", "submission_date", "flower_type")
    search_fields = ("temple__name", "flower_type", "remarks", "submitted_by__full_name", "submitted_by__email")
    autocomplete_fields = ("temple", "submitted_by")


@admin.register(CollectionRecord)
class CollectionRecordAdmin(admin.ModelAdmin):
    list_display = ("submission", "collector", "collected_at", "collected_weight", "status", "created_at")
    list_filter = ("status", "collected_at")
    search_fields = ("submission__temple__name", "collector__full_name", "collector__email", "remarks")
    autocomplete_fields = ("submission", "collector")


@admin.register(Flower)
class FlowerAdmin(admin.ModelAdmin):
    list_display = ("name", "quality", "nitrogen_content", "decomposition_rate", "fertilizer_potential")
    list_filter = ("quality",)
    search_fields = ("name", "fertilizer_potential")


@admin.register(Collection)
class LegacyCollectionAdmin(admin.ModelAdmin):
    list_display = ("temple", "flower", "collector", "quantity", "collection_date", "status")
    list_filter = ("status", "collection_date")
    search_fields = ("temple__name", "collector__full_name")


admin.site.site_header = "PushpaRecycle — Admin Department"
admin.site.site_title = "PushpaRecycle Admin"
admin.site.index_title = "System Overview & Controls"
